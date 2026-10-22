#!/usr/bin/env python3
"""Exercise the real compile-only native parser with no JavaScript execution."""
import ctypes
from pathlib import Path
import sys


def main():
    library = ctypes.CDLL(str(Path(sys.argv[1]).resolve()))
    check = library.qfli_web_syntax_check
    check.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_int32, ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_int32), ctypes.c_char_p, ctypes.c_size_t]
    check.restype = ctypes.c_int32
    library.qfli_web_syntax_version.restype = ctypes.c_char_p
    print(library.qfli_web_syntax_version().decode())

    def parse(source, module=False):
        encoded = source.encode("utf8")
        start, end = ctypes.c_int32(), ctypes.c_int32()
        message = ctypes.create_string_buffer(2048)
        status = check(encoded, len(encoded), module, ctypes.byref(start), ctypes.byref(end), message, len(message))
        return status, start.value, end.value, message.value.decode()

    clean = ["const n = 1;", "throw new Error('MUST NOT EXECUTE');", "while(true) {}", "Promise.resolve().then(() => { throw 1; });", "fetch('https://example.invalid');", "require('fs').writeFileSync('MUST_NOT_EXIST', 'bad');", "class A { #x = 1; method() { return this.#x; } }", "const x = {v: 1}; x?.v ?? 0;", "const re = /[a-z]+/u;"]
    for source in clean:
        assert parse(source)[0] == 0, (source, parse(source))
    for source in ["import value from './does-not-exist.js'; export default value;", "import 'https://example.invalid/never-load.js';", "export const value = await Promise.resolve(1);"]:
        assert parse(source, True)[0] == 0, (source, parse(source, True))
    for source in ["const = 1;", "function f( {", "const re = /[a-/;", "let same; let same;", "import { from './x';"]:
        assert parse(source, "import" in source)[0] == 1, (source, parse(source))
    for source in ["const emoji='😀'; const bad = ;", "// 😀\r\nconst emoji='😀'; const bad = ;", "//\rconst emoji='😀'; const bad = ;"]:
        result = parse(source)
        expected = len(source[:source.rindex(';')].encode('utf-16-le')) // 2
        assert result[:3] == (1, expected, expected + 1), (source, result, expected)
    eof = "const x = ("
    assert parse(eof)[:3] == (1, len(eof), len(eof)), parse(eof)
    assert parse(" " * (512 * 1024 + 1))[0] == -1
    assert parse("(" * 10000)[0] == -1, parse("(" * 10000)
    for _ in range(30):
        assert parse("globalThis.changed = true;")[0] == 0
        assert parse("const bad = ;")[0] == 1
    print("PASS: genuine syntax, modules/imports, no execution, UTF-16/CRLF/emoji, EOF, resource limits, repeated contexts")


if __name__ == "__main__":
    main()
