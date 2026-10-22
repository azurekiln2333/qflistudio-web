# Offline Web syntax parser

This bridge compiles source using retained QuickJS 2026-06-04 with
`JS_EVAL_FLAG_COMPILE_ONLY`. It never runs the result, jobs, or imported source.
The retained patch bypasses upstream compile-only module resolution; no module
loader or `quickjs-libc` is linked. Only the two `qfli_web_syntax_*` C ABI symbols
are public. Each request owns a fresh runtime, with 512 KiB UTF-8 input, 32 MiB
runtime memory and 512 KiB stack bounds. Resource failures return unavailable.

The pure Dart product adapter uses actual HTML5/csslib parsers and this native
JavaScript parser, analyzes unsaved buffers in a separate isolate, preserves
UTF-16/CRLF/emoji ranges, and performs no project filesystem reads or writes.
HTML5's parser normalizes CRLF internally; the adapter maps spans back to the
original buffer. CSS coverage is the grammar supported by csslib, not browser
semantic/style validation. Missing native delivery remains explicitly unavailable.

Build sources stay pinned by `vendor/quickjs/SOURCE.json` and `HASHES.sha256`.
Python builds and CMake configurations verify retained inputs. No build step
downloads dependencies. The original official archive is retained, together
with the exact patch and MIT license.

```powershell
# Installed Windows host toolchains in this workspace. GCC 4.9 is a linker
# driver only: actual probes found it miscompiles QuickJS module atoms.
python scripts/build_web_syntax.py --platform windows --cc D:/ProgramFiles/Huawei/OpenHarmony/Sdk/23/native/llvm/bin/clang.exe --sdk D:/ProgramFiles/Dev-Cpp/MinGW64 --link-cc D:/ProgramFiles/Dev-Cpp/MinGW64/bin/gcc.exe
python native/web_syntax/test_native.py build/native/web_syntax/windows/qfli_web_syntax.dll
python scripts/build_web_syntax.py --platform ohos --abi arm64-v8a --sdk D:/ProgramFiles/Huawei/OpenHarmony/Sdk/23/native
python scripts/build_web_syntax.py --platform ohos --abi x86_64 --sdk D:/ProgramFiles/Huawei/OpenHarmony/Sdk/23/native
```

GCC 9+ or Clang is required for compilation. The bridge rejects older GCC.
Windows Clang can use an installed MinGW sysroot and separate linker driver;
the output DLL requires only Windows system DLLs. Desktop tests may specify
`QFLI_WEB_SYNTAX_LIBRARY`; production resolves a packaged library beside the
executable (Windows), in the app Frameworks directory (macOS), or executable
`lib/` (Linux), then the platform dynamic loader. Apple static builds use
process symbols, with the product retaining/force-loading the archive.

Root platform integration owns Android/OHOS/Linux CMake registration and native
packaging, the Windows DLL install, and Apple per-architecture build/linking.
`QFLI_WEB_SYNTAX_STATIC=ON` switches the CMake target to a static archive.
Apple Python builders accept `--arch arm64|x86_64` and
`--apple-sdk iphoneos|iphonesimulator|macosx`. iPhone device requires arm64;
iOS minimum is 13.0, macOS minimum is 11.0. Build each platform/architecture
separately, and validate Mach-O platform and arch before lipo/linking.

Host behavior tests and cross-compiled ELF evidence do not prove device
execution, signed installation, Apple tooling availability, or browser semantic
validation. Those are separate product acceptance gates.
