"""Exercise the delivered native Linux cancellation and upstream artifact ABI."""

import ctypes
from pathlib import Path
import sys
import tempfile
import threading
import time


class Result(ctypes.Structure):
    _fields_ = [("exit_code", ctypes.c_int), ("output", ctypes.c_void_p),
                ("error", ctypes.c_void_p), ("truncated", ctypes.c_int)]


engine = ctypes.CDLL(sys.argv[1])
engine.qfli_py_cancel_create.restype = ctypes.c_void_p
engine.qfli_py_cancel_request.argtypes = [ctypes.c_void_p]
engine.qfli_py_cancel_free.argtypes = [ctypes.c_void_p]
engine.qfli_py_result_free.argtypes = [ctypes.POINTER(Result)]
engine.qfli_py_execute_into.argtypes = [ctypes.POINTER(Result), ctypes.c_char_p,
    ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
    ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
engine.qfli_py_version.restype = ctypes.c_char_p
print("Engine:", engine.qfli_py_version().decode(), flush=True)
passed = 0


def execute(root, source="", token=None, compile_only=False, artifact=None,
            bytecode=None, stdin=""):
    result = Result()
    engine.qfli_py_execute_into(ctypes.byref(result), source.encode(),
        stdin.encode(), 0, str(root).encode(), str(root / "main.py").encode(),
        int(compile_only), token, str(artifact).encode() if artifact else None,
        str(bytecode).encode() if bytecode else None)
    try:
        return (result.exit_code,
                ctypes.string_at(result.output).decode() if result.output else "",
                ctypes.string_at(result.error).decode() if result.error else "",
                result.truncated)
    finally:
        engine.qfli_py_result_free(ctypes.byref(result))


def check(condition, label, detail):
    global passed
    assert condition, (label, detail)
    passed += 1
    print("PASS", label, flush=True)


with tempfile.TemporaryDirectory(prefix="qfli-python-linux-") as temporary:
    root = Path(temporary)
    for label, source in [
        ("loop cancellation", "print('before')\nwhile True: pass\n"),
        ("sleep cancellation", "import time\nprint('before')\ntime.sleep(60)\n")
    ]:
        token = engine.qfli_py_cancel_create()
        result = []
        worker = threading.Thread(target=lambda: result.append(execute(root, source, token)))
        try:
            worker.start()
            time.sleep(0.25)
            started = time.monotonic()
            engine.qfli_py_cancel_request(token)
            worker.join(3)
            check(not worker.is_alive() and result[0][0] == 130
                  and result[0][1] == "before\n" and time.monotonic() - started < 3,
                  label, result)
        finally:
            engine.qfli_py_cancel_request(token)
            worker.join()
            engine.qfli_py_cancel_free(token)
    result = execute(root, "print('fresh')\n")
    check(result[:2] == (0, "fresh\n"), "fresh run after cancellation", result)

    token = engine.qfli_py_cancel_create()
    try:
        engine.qfli_py_cancel_request(token)
        result = execute(root, "open('side-effect.txt', 'w').write('bad')", token)
        check(result[0] == 130 and not (root / "side-effect.txt").exists(),
              "pre-start cancellation has no effects", result)
    finally:
        engine.qfli_py_cancel_free(token)

    active = engine.qfli_py_cancel_create()
    queued = engine.qfli_py_cancel_create()
    first, second = [], []
    running = threading.Thread(target=lambda: first.append(execute(root, "while True: pass", active)))
    waiting = threading.Thread(target=lambda: second.append(execute(root, "print('queued')", queued)))
    try:
        running.start()
        time.sleep(0.1)
        waiting.start()
        time.sleep(0.1)
        engine.qfli_py_cancel_request(queued)
        check(running.is_alive(), "queued token does not cancel active run", first)
        engine.qfli_py_cancel_request(active)
        running.join(3)
        waiting.join(3)
        check(not running.is_alive() and not waiting.is_alive()
              and first[0][0] == 130 and second[0][0] == 130 and not second[0][1],
              "queued cancellation survives serialization", (first, second))
    finally:
        engine.qfli_py_cancel_request(active)
        engine.qfli_py_cancel_request(queued)
        running.join()
        waiting.join()
        engine.qfli_py_cancel_free(active)
        engine.qfli_py_cancel_free(queued)

    artifact = root / "main.mpy"
    result = execute(root, "print('artifact')\nprint(input())\n", compile_only=True,
                     artifact=artifact)
    check(result[0] == 0 and not result[1] and artifact.is_file(),
          "upstream compile saves bytecode without execution", result)
    result = execute(root, bytecode=artifact, stdin="loaded\n")
    check(result[:2] == (0, "artifact\nloaded\n"),
          "source-free bytecode execution and stdin", result)
    invalid = root / "invalid.mpy"
    invalid.write_bytes(b"not an upstream artifact")
    result = execute(root, bytecode=invalid)
    check(result[0] != 0 and not result[1] and result[2],
          "invalid bytecode returns real error", result)
    result = execute(root, "print('recovered')\n")
    check(result[:2] == (0, "recovered\n"), "fresh run after bytecode error", result)

print(f"PASS {passed}/{passed} real Linux lifecycle/artifact checks", flush=True)
