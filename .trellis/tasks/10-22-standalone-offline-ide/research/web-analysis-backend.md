# Web source analysis backend — 2026-10-22

## Boundary and design

The editor currently has no product analyzer. Implement the core `CodeAnalyzer`
contract over the exact active unsaved snapshot, without reading or writing user
files. The adapter owns only new `lib/services/web_code_analyzer*.dart`, native
bridge/build/test files under `native/web_syntax`, source-only `vendor/quickjs`,
and its test. Root owns dependency/profile/platform packaging integration.

Use the actual HTML5 parser (`html`, resolved 0.15.7) and CSS parser (`csslib`,
1.0.2), with parser-produced spans. Parse HTML embedded script/style source by
the DOM node's original source offsets, not by a regular expression. Do not
claim modern CSS semantic validation: csslib is a syntax parser with limited
support for newer CSS grammar. Preserve its backend name and reported messages.

Use QuickJS 2026-06-04 (official Bellard release, MIT, ES2025) for JavaScript
compile-only parsing. Upstream source inspection found module resolution before
the compile-only return. Retain a minimal patch that skips module resolution in
compile-only mode, and install no module loader. There is no call to evaluation
without `JS_EVAL_FLAG_COMPILE_ONLY`, no execution of the resulting function or
jobs, no quickjs-libc, CLI, filesystem or network bindings. Each parse gets a
fresh runtime with memory/stack limits and a 512 KiB UTF-8 source limit.

The C ABI returns status, one native parser error, and exact UTF-16 start/end
offsets. QuickJS reports 1-based Unicode scalar columns over LF-delimited lines;
convert those against the original UTF-8 source while preserving CRLF and emoji.
HTML/CSS spans already index the Dart UTF-16 string. Embedded offsets are added
to original source positions. EOF remains an insertion point. Missing native
backend and resource failures produce explicit unavailable status.

Validate absolute normalized owned paths and active snapshot revision before
dispatch. Bound work and perform parser/FFI work in a separate isolate. Return
diagnostics only for the active snapshot; never synthesize project-file errors.
External script/style references are not loaded. HTML script data blocks (e.g.
JSON) are not compiled as JavaScript. Scripts with `type=module` use module mode;
standalone `.mjs` uses module mode and `.js` accepts either valid classic or
valid module grammar, while preserving real parser error ranges.

## Native packaging contract

`native/web_syntax/CMakeLists.txt` provides target `qfli_web_syntax`, shared by
default and static with `QFLI_WEB_SYNTAX_STATIC=ON`. Dart opens
`qfli_web_syntax.dll`, `libqfli_web_syntax.so`, or the dylib, with process-symbol
fallback for Apple static linkage. Root integrates add_subdirectory/package
delivery and the MIT license asset. Build scripts do not run pub or download
anything; source is pinned and retained locally.

Installed toolchains inspected: SDK23 OpenHarmony clang 15.0.4/CMake and MinGW64
gcc host. Build genuine SDK23 arm64/x86_64 ELF shared libraries and a Windows
DLL for native behavior tests. Android/Apple/platform runtime claims require
their actual installed tools and devices. Host tests and cross-compilation do
not prove OHOS runtime execution.

## Primary research

- Official release and license: https://bellard.org/quickjs/
- Official API documentation: https://bellard.org/quickjs/quickjs.html
- Official release source: https://bellard.org/quickjs/quickjs-2026-06-04.tar.xz
  (SHA-256 `b376e839b322978313d929fd20663b11ba58b75df5a46c126dd19ea2fa70ad2a`).
- Installed parser source/API: `html-0.15.7/lib/parser.dart`,
  `html-0.15.7/lib/dom.dart`, `csslib-1.0.2/lib/parser.dart`.

## Validation plan

Real native cases: valid classic/module/import source, actual syntax errors,
CRLF/emoji columns, EOF, no program execution (throw/infinite loop), no module
loads, source/resource limits, repeated fresh contexts. Dart adapter cases:
HTML/CSS real parser errors; embedded exact spans; JSON scripts; unsaved text
instead of differing disk contents; path/revision/limit rejection; native
unavailable; unsupported language honesty. Inspect native imports/exports and
SDK23 ELF architecture before handing packaging to root.

## Verified implementation evidence

- `flutter test --no-pub --concurrency=1 test/web_code_analyzer_test.dart`:
  **15/15 passed**. The real Windows DLL participates in all five native adapter
  cases (no parser mocks). Final integration runs should repeat this suite with
  the root's full affected tests after profile/platform changes.
- Scoped `flutter analyze --no-pub` over the four new service files and service
  test: **No issues found**.
- `python native/web_syntax/test_native.py
  build/native/web_syntax/windows/qfli_web_syntax.dll`: **PASS** for actual
  classic/module/import grammar; valid and invalid syntax; throwing and infinite
  loop programs only compiled; remote imports never loaded; exact
  UTF-16/CRLF/emoji/EOF positions; source/stack bounds; 30 repeated fresh contexts.
- Installed MinGW GCC 4.9.2 miscompiled QuickJS module atom reference counting:
  the real import probe crashed in `JS_DupAtom`/`add_req_module_entry` (gdb).
  Using installed SDK23 Clang 15.0.4 for Windows compilation and MinGW solely as
  linker driver passes all probes. The bridge rejects GCC below 9 rather than
  shipping the failing backend. The resulting DLL imports only Windows system
  DLLs (KERNEL32/msvcrt/USER32), with no additional runtime DLL dependency.
- Installed SDK23 Clang 15.0.4 built genuine arm64-v8a and x86_64 OHOS shared
  libraries. `llvm-readelf` proves DYN/AArch64 or DYN/x86-64, entry point zero and
  16 KiB LOAD alignment. Dynamic exports are the two intended `qfli_*` ABI
  functions. No `JS_Eval` export or socket/connect/open/exec import exists.
  QuickJS retains its normal assertion `abort` import.
- The standalone native CMake target also configured and built successfully
  using SDK23's `ohos.toolchain.cmake` (arm64, Release). It verifies
  `HASHES.sha256` at configure time. An isolated copied fixture with intentionally
  modified `cutils.h` is rejected with `Retained QuickJS source hash mismatch`.
- Installed Android NDK 28.2.13676358 built genuine arm64-v8a and x86_64 shared
  libraries; both are DYN, correct machine and entry point zero, with 16 KiB LOAD
  alignment. Android pthread symbols come from libc; do not link `-lpthread`.
- Verified the retained archive hash, every source/header/license/patch hash,
  and byte-for-byte equality of patched `quickjs.c` to the official archive plus
  the exact recorded one-hunk module-resolution patch.
- Real HTML5 source investigation found two offset hazards, now regression
  covered: CRLF normalization, and null `endSourceSpan` on raw-text script/style
  elements. Content is bounded by actual text-node source spans instead, so
  subsequent HTML is never fed to CSS/JavaScript parsers.

Build artifacts (workspace-local evidence; these are not device passes):

| Target | Library under `build/native/web_syntax/` | SHA-256 |
| --- | --- | --- |
| Windows host | `windows/qfli_web_syntax.dll` | `11967d444d1cb681b813bc3836da7e4be969a6e11320c077d64757ef2a93dce2` |
| OHOS arm64 | `ohos/arm64-v8a/libqfli_web_syntax.so` | `f671b38cf34061eb7cfe4625c5e508181a3c76fb070447492780b35832e6330f` |
| OHOS x86_64 | `ohos/x86_64/libqfli_web_syntax.so` | `b0f7e2efc222642ca8bea3b01bf2f1b860e8f607fa9343c0d7b7365ae40e8cda` |
| Android arm64 | `android/arm64-v8a/libqfli_web_syntax.so` | `2ebff46f25895389f0650fb0d41484e5c75a65bc86a64a8b62b794b86734427b` |
| Android x86_64 | `android/x86_64/libqfli_web_syntax.so` | `85421d77371cba8fa77c30bb532860c507065dcc0d62ce6202eff7eec5da87ce` |

Apple builders support explicit architecture and SDK/platform arguments; no
Apple compile/link/runtime pass is claimed on this Windows host. The default
Ubuntu WSL distribution cannot mount its missing VHDX; no Linux execution pass
is claimed from that failed host probe. No device, signed packaging, OHOS/Android
runtime execution, or full product acceptance is inferred from cross-compilation.
