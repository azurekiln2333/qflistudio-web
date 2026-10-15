"""Reproduce the access-log regression against the real Linux embedded library.

The embedded engine runs more than one cycle in a single process: the editor
calls validate() (nginx -t) and then start() (server). A stale time cache made
the access-log handler skip every line after a -t run, so this probe asserts the
log is written in each sequence.

Scenarios, selected by PROBE_MODE:
  server-only         server once
  test-then-server    -t once, then server
  server-then-server  server, stop, server
  test-then-restart   -t, server, stop, server again

Run:
    python3 access_log_probe.py <libqfli_nginx.so>
"""

import ctypes
import http.client
import os
import socket
import sys
import tempfile
import time
from pathlib import Path


def bind_library(path):
    library = ctypes.CDLL(path)
    library.qfli_nginx_version.restype = ctypes.c_char_p
    library.qfli_nginx_start.argtypes = [ctypes.c_char_p, ctypes.c_int]
    library.qfli_nginx_start.restype = ctypes.c_int64
    library.qfli_nginx_poll.argtypes = [ctypes.c_int64, ctypes.POINTER(ctypes.c_int)]
    library.qfli_nginx_stop.argtypes = [ctypes.c_int64]
    library.qfli_nginx_release.argtypes = [ctypes.c_int64]
    return library


def run_to_completion(library, token):
    code = ctypes.c_int()
    for _ in range(800):
        if library.qfli_nginx_poll(token, ctypes.byref(code)) == 1:
            library.qfli_nginx_release(token)
            return code.value
        time.sleep(0.01)
    raise RuntimeError("worker did not complete")


def request(port, path):
    deadline = time.monotonic() + 4
    while True:
        try:
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
            connection.request("GET", path)
            response = connection.getresponse()
            status = response.status
            response.read()
            connection.close()
            return status
        except ConnectionRefusedError:
            if time.monotonic() > deadline:
                raise
            time.sleep(0.02)


def make_prefix(root):
    prefix = Path(root)
    (prefix / "index.html").write_text("probe", encoding="utf-8")
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    (prefix / "nginx.conf").write_text(
        "daemon off;\nmaster_process off;\npid nginx.pid;\n"
        "error_log stderr warn;\nevents { worker_connections 64; }\n"
        "http {\n"
        "  log_format webforge escape=json "
        "'{\"method\":\"$request_method\",\"uri\":\"$request_uri\","
        "\"status\":$status,\"time\":$request_time}';\n"
        "  access_log access.log webforge;\n"
        "  client_body_temp_path temp/client;\n"
        "  proxy_temp_path temp/proxy;\n"
        f"  server {{\n    listen 127.0.0.1:{port};\n"
        f"    root \"{prefix}\";\n  }}\n}}\n",
        encoding="utf-8",
    )
    (prefix / "temp" / "client").mkdir(parents=True)
    (prefix / "temp" / "proxy").mkdir(parents=True)
    return port


def serve(library, prefix, port):
    token = library.qfli_nginx_start(os.fsencode(prefix), 0)
    if token <= 0:
        raise RuntimeError("server start failed: %d" % token)
    status = request(port, "/index.html")
    time.sleep(0.3)
    library.qfli_nginx_stop(token)
    run_to_completion(library, token)
    return status


def check_config(library, prefix):
    token = library.qfli_nginx_start(os.fsencode(prefix), 1)
    if token <= 0:
        raise RuntimeError("config check start failed: %d" % token)
    return run_to_completion(library, token)


def run(mode):
    library = bind_library(SO_PATH)
    with tempfile.TemporaryDirectory(prefix="qfli-access-probe-") as name:
        prefix = Path(name)
        port = make_prefix(name)

        if mode == "test-then-server":
            print("config-check exit", check_config(library, prefix))
        elif mode == "server-then-server":
            print("warmup status", serve(library, prefix, port))
        elif mode == "test-then-restart":
            print("config-check exit", check_config(library, prefix))
            print("first server status", serve(library, prefix, port))
            # The first server run already wrote a line; drop it so the second
            # run's contribution is measured on its own.
            first = (prefix / "access.log").stat().st_size if (prefix / "access.log").exists() else 0
            (prefix / "access.log").write_text("")
            print("first run log bytes", first)
        elif mode != "server-only":
            raise SystemExit("unknown mode: %s" % mode)

        status = serve(library, prefix, port)
        access = prefix / "access.log"
        size = access.stat().st_size if access.exists() else -1
        print("mode", mode, "http status", status, "access.log size", size)
        return status == 200 and size > 0


MODES = ("server-only", "test-then-server", "server-then-server", "test-then-restart")

if __name__ == "__main__":
    SO_PATH = sys.argv[1]
    selected = os.environ.get("PROBE_MODE")
    modes = (selected,) if selected else MODES
    failures = [m for m in modes if not run(m)]
    if failures:
        print("ACCESS_LOG_PROBE FAIL:", ", ".join(failures))
        sys.exit(1)
    print("ACCESS_LOG_PROBE PASS:", ", ".join(modes))
