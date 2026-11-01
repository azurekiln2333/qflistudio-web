# Native QuickJS web-syntax packaging — read-only review

> **Superseded in part.** See `native-packaging-recheck.md` for the second pass and
> `native-packaging-resolution.md` for the third. **B1, B2, B3, M1 and the OHOS packaging
> gap are all resolved as of the third pass** — the Windows preflight exists, the analyzer is
> constructed and consumed, the loader paths are corrected, and both ABIs ship in an inspected
> HAP. The stale "artifacts predate the change" note in §2 below is withdrawn. Remaining open
> items are Apple/macOS runtime + signing, on-device `dlopen`, signed installation, and the
> minor M2–M8 robustness notes.

Reviewer scope: read-only inspection of the uncommitted native/packaging work added by
another owner (QuickJS `2026-06-04` syntax-only bridge). **No source was modified, no
Flutter/Gradle/CMake build was run, no other task was touched.** Evidence is file
inspection plus two read-only build-artifact probes of the existing `ohos/` output tree.

Paths under review:

| Area | File |
| --- | --- |
| Bridge source | `native/web_syntax/CMakeLists.txt`, `qfli_web_syntax.{c,h}`, `test_native.py` |
| Vendored parser | `vendor/quickjs/` (+ `SOURCE.json` hash manifest) |
| Build driver | `scripts/build_web_syntax.py` |
| Apple bundling | `scripts/bundle_web_syntax_apple.sh`, `ios/Flutter/WebSyntax.xcconfig`, `ios/Runner.xcodeproj/project.pbxproj`, `macos/Runner.xcodeproj/project.pbxproj` |
| Per-platform wiring | `android/app/build.gradle.kts`, `linux/CMakeLists.txt`, `windows/CMakeLists.txt`, `ohos/entry/src/main/cpp/CMakeLists.txt` |
| Dart FFI | `lib/services/web_javascript_syntax{,_native,_stub}.dart`, `lib/services/web_code_analyzer.dart` |

---

## 1. Blocking findings

### B1. The native backend is not reachable from any UI — the packaging has no user-visible effect yet

`lib/services/web_code_analyzer.dart` is the only consumer of the QuickJS bridge, and it
is imported **only by its own test**:

```
D:\MyNewProjects\qfli_web\test\web_code_analyzer_test.dart   line 6
```

No page/widget/service imports `web_code_analyzer.dart`. So shipping the DLL/`.so`/`.a`
across six platforms currently changes nothing a user can see; all diagnostics the app
shows still come from the pure-Dart scanners.

Reproduce:

```powershell
Select-String -Path lib/*.dart,lib/**/*.dart -Pattern "web_code_analyzer"
# -> no matches outside test/
```

Action: either land the UI wiring in the same release, or state explicitly that this
packaging ships dormant infrastructure. Do **not** list "JavaScript syntax diagnostics
on device" as delivered until a tools surface calls `WebCodeAnalyzer`.

### B2. Windows default build path is likely broken, and its failure mode is `FATAL_ERROR`

`windows/CMakeLists.txt` (added block) does:

```cmake
find_program(QFLI_SYNTAX_CC NAMES clang gcc)          # clang preferred
if(NOT QFLI_SYNTAX_PYTHON OR NOT QFLI_SYNTAX_CC)
  message(FATAL_ERROR "Offline JavaScript diagnostics require Python and GCC/Clang ...")
endif()
set(QFLI_SYNTAX_WINDOWS_SYSROOT "" CACHE PATH "Optional MinGW sysroot ...")
```

and `scripts/build_web_syntax.py` only adds a non-MSVC target when a sysroot is supplied:

```python
if args.platform == "windows" and args.sdk:
    flags += ["--target=x86_64-w64-windows-gnu", f"--sysroot={args.sdk}"]
...
if args.platform == "windows":
    link_flags += ["-static-libgcc", "-static", "-lwinpthread"]
```

Three problems compound on a stock Flutter Windows dev box:

1. Neither `clang` nor `gcc` is normally on `PATH` → **`FATAL_ERROR` aborts the whole
   `flutter build windows`**, not just the JS feature. Every existing contributor and CI
   job without MinGW/LLVM loses the ability to build the app.
2. If LLVM's `clang` *is* on `PATH`, it defaults to the **MSVC** target
   (`x86_64-pc-windows-msvc`). With `QFLI_SYNTAX_WINDOWS_SYSROOT` unset (the default), it
   compiles against MSVC headers and then fails to link, because `-static`, `-static-libgcc`
   and `-lwinpthread` are MinGW-isms.
3. The "optional" sysroot is in practice **mandatory whenever `clang` is selected**, which
   is exactly what `find_program` prefers.

Suggested direction (owner's call):

- Prefer `gcc` before `clang` in `find_program(... NAMES gcc clang)`, since a bare MinGW
  `gcc` needs neither `--target` nor `--sysroot` nor `--link-cc`.
- When `clang` is chosen and `QFLI_SYNTAX_WINDOWS_SYSROOT` is empty, either auto-locate a
  MinGW sysroot or `FATAL_ERROR` with that specific message — not the generic one.
- Prefer graceful degradation over `FATAL_ERROR` for a diagnostics nicety: skip the custom
  target and let Dart's `unavailable` path report "offline parser unavailable". That keeps
  `flutter build windows` green on machines without GCC/Clang, matching how the feature
  already behaves at runtime when the library is missing.

### B3. The explicit FFI path never resolves on Android/OHOS; success rests on the bare-name fallback

`lib/services/web_javascript_syntax_native.dart` `_open()` tries, for the non-Windows,
non-macOS case, a joined path and then the bare soname:

```
<executableDirectory>/lib/libqfli_web_syntax.so
libqfli_web_syntax.so
```

With `android { packaging { jniLibs { useLegacyPackaging = true } } }` (in the diff), the
native libraries are extracted to the app's `nativeLibraryDir`, i.e.
`/data/user/<id>/<pkg>/lib/`, **not** into a `lib/` subdirectory of it. `Platform
.resolvedExecutable` already points into that directory, so the joined candidate is
`.../lib/lib/libqfli_web_syntax.so` — a path that never exists. The same shape applies to
OHOS (`<bundle>/libs/<abi>/`).

The `ArgumentError` from `DynamicLibrary.open` on the bogus path is caught, so the bare
name is reached and *should* resolve through the process linker namespace. Behaviour is
therefore probably fine, but it is unverified on both platforms and the first candidate is
misleading dead code. Recommend deriving the directory from `resolvedExecutable`'s parent
without the extra `lib` segment (or dropping the candidate and documenting the namespace
reliance), and confirming once on a real device each for Android and OHOS.

---

## 2. Verification gaps — current artifacts cannot prove OHOS packaging

`ohos/entry/src/main/cpp/CMakeLists.txt` adds `native/web_syntax` and the target is
`SHARED` (`QFLI_WEB_SYNTAX_STATIC` defaults `OFF`), which is right: the N-API module cannot
carry the parser statically for `dart:ffi`.

What the existing output tree shows:

```
ohos/entry/.cxx/.../CMakeCache.txt                2026-10-15 18:54:55
ohos/entry/build/.../obj/arm64-v8a/libqfli_nginx_napi.so   2026-10-15 18:54:56
ohos/entry/src/main/cpp/CMakeLists.txt            2026-10-22 12:48:05
```

The artifacts **predate** the change, there is no `web_syntax` sub-build directory under
`.cxx/`, and no `libqfli_web_syntax.so` anywhere in `ohos/entry/build`. That absence proves
nothing by itself, but it means **OHOS packaging of the parser is unproven**.

Supporting evidence in favour (so this is a "must verify", not a suspected defect):

- DevEco does pass the ABI variable the CMakeLists branches on. From
  `ohos/entry/.cxx/default/default/release/arm64-v8a/metadata_generation_command.txt`:
  `-DOHOS_ARCH=arm64-v8a`, `-DCMAKE_OHOS_ARCH_ABI=arm64-v8a`. `build-profile.json5`
  filters to `["arm64-v8a", "x86_64"]`, matching the two prebuilt nginx archive branches.
- hvigor evidently copies *everything* from
  `.../intermediates/cmake/default/obj/<abi>/` into the package: `libc++_shared.so` reaches
  `intermediates/libs/default/<abi>/` and `stripped_native_libs/` even though it is not a
  target of this project. A second project `.so` should follow the same path.

Verification to run once a device or emulator target exists (`hdc list targets` was empty
in this session):

```powershell
flutter build hap --release
# then confirm the arch actually contains the parser
tar -tf .\build\ohos\hap\entry-default-unsigned.hap   # or unzip -l on dist output
# expect: libs/arm64-v8a/libqfli_web_syntax.so and libs/arm64-v8a/libqfli_nginx_napi.so
```

Also assert the 16 KB alignment option survived (`-Wl,-z,max-page-size=16384` is set in both
`native/web_syntax/CMakeLists.txt` and the Python driver) and that
`qfli_web_syntax_check` is exported by the packaged `.so`.

---

## 3. Medium / robustness findings

### M1. Apple static retention is plausible but unasserted

`ios/Flutter/WebSyntax.xcconfig`:

```
OTHER_LDFLAGS = $(inherited) -force_load "$(BUILT_PRODUCTS_DIR)/qfli-web-syntax/libqfli_web_syntax.a"
```

Mechanism is correct: `-force_load` pulls every archive member, and the header marks both
exports `visibility("default"), used`, so the object cannot be dropped for being unreferenced.
But nothing *proves* `_qfli_web_syntax_check` survives into the shipped binary under
Release settings (`DEAD_CODE_STRIPPING = YES`, `-dead_strip`). Cheapest guarantee is a
`-u` reference or a release-pipeline assertion:

```bash
# after linking Release
nm -gU "$BUILT_PRODUCTS_DIR/$PRODUCT_NAME.app/$PRODUCT_NAME" | grep _qfli_web_syntax_check
```

If it is absent, add `-Wl,-u,_qfli_web_syntax_check` to the same `OTHER_LDFLAGS`.
Also note `$(inherited)` is present, so this composes safely with the Flutter-generated
flags — and macOS deliberately does not include this xcconfig (it links a dylib instead),
which is consistent.

### M2. `vtool` assertion is brittle

`scripts/bundle_web_syntax_apple.sh` extracts every archive member and runs
`xcrun vtool -show-build` on each `.o`, then requires every `platform` line to equal
`IOS` / `IOSSIMULATOR` / `MACOS`. Under `set -euo pipefail`, a single member without
`LC_BUILD_VERSION`, or a `vtool` that refuses an object file, aborts the build. Reasonable
intent (it is the only way to catch device-vs-simulator `arm64` confusion), but consider
`vtool ... || true` plus an explicit "no platform lines found" failure so diagnostics point
at the real cause instead of an opaque phase error.

Related: for iOS the extracted `.o` files live in a `mktemp -d` inside `$arch_output` and are
never removed; only `$output/$library` is lipo'd, so this is disk hygiene, not correctness.
On macOS the leftover `.o`s in `$arch_output` are in fact *required* by that inspection.

### M3. Do not co-locate iphoneos and iphonesimulator outputs

`lipo -create` runs across `$ARCHS` inside one `$BUILT_PRODUCTS_DIR`. That is safe only
because Xcode gives device and simulator builds different `BUILT_PRODUCTS_DIR`s. Both would
otherwise contribute an `arm64` slice and `lipo` would refuse ("same architectures … can't
be in the same fat file"). Worth a comment so nobody "simplifies" the output layout later.

### M4. Windows shares one DLL across configurations

`set(QFLI_SYNTAX_OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/web_syntax")` is configuration-
independent, while the custom command always builds with `-O2`. Functionally fine (the DLL
does not vary by Flutter config) but Debug and Release share a single artifact and can race
if both are built concurrently. If that matters, append `${CMAKE_CFG_INTDIR}` (Visual Studio
generator) or move the output under the config directory.

### M5. Embedded NUL — lower risk than it first looks, but untested

The Dart side passes `utf8.encode(source).length` and a `toNativeUtf8()` buffer, and the C
side validates `source[length] == '\0'` before calling
`JS_Eval(context, source, length, ...)`. Because `JS_Eval` is given an **explicit** `length`,
a `\u0000` inside the source does not truncate the parse — QuickJS consumes the full byte
range and reports a normal `SyntaxError` whose position `error_offsets()` maps consistently.
So this is not the truncation bug it resembles. It is simply untested: add one case
(`'var a = 1;\u0000'`) and pin whatever QuickJS actually reports. (An earlier draft of this
review overstated this as silent truncation; corrected after reading `qfli_web_syntax.c`.)

### M6. `error_offsets()` assumes well-formed UTF-8

`error_offsets()` classifies a lead byte by range (`<0x80`→1, `<0xe0`→2, `<0xf0`→3, else 4)
and credits 2 UTF-16 units for 4-byte sequences. Dart's `utf8.encode` always emits valid
UTF-8 (unpaired surrogates become U+FFFD), so the normal path is correct. Two residual
edges: a stray continuation byte (0x80–0xBF) is classified as a 2-byte lead, and the
`index + count > length` guard runs *after* the position match, so a position landing on a
truncated sequence can return `units = 2` for a single remaining byte. Neither is reachable
from Dart today; a bounds check before the match would make the function total.

### M7. No call-level caching

`_open()` is invoked on every `checkJavaScriptSyntax` call, and the C side creates and tears
down a `JSRuntime` + `JSContext` per call (`JS_NewRuntime` → `JS_Eval` → `JS_FreeRuntime`),
with a 32 MiB memory limit and 512 KiB stack. `DynamicLibrary.open` on an already-loaded
library is cheap and refcounted, so the FFI part is fine, but a fresh runtime per call is not
free on large sources. Since `WebCodeAnalyzer.analyze` already runs inside `Isolate.run`, the
cost lands off the UI thread — acceptable today. Worth revisiting only if the eventual UI
wiring (B1) calls this per keystroke on large files.

### M8. Hash manifest scope

`vendor/quickjs/SOURCE.json` pins all five compiled upstream `.c` files **and** their
transitive headers (`quickjs*.h`, `cutils.h`, `dtoa.h`, `libregexp*.h`, `libunicode*.h`,
`list.h`), plus `LICENSE` and the local patch, and `build_web_syntax.py` hard-fails on any
mismatch. That is solid. `native/web_syntax/qfli_web_syntax.{c,h}` are project-owned and
intentionally unhashed; worth one sentence in the docs so it does not read as an oversight.

---

## 4. Confirmed correct (checked, no action)

- **`WebCodeAnalyzer` ES-module fallback is correct.** For `.js`, the first attempt runs
  `module: false` and the retry at line 186 passes `module: true` before comparing
  `moduleResult.message == null`, so a valid ES module is accepted and a genuine script
  error is retained. No change needed. (An earlier draft of this review flagged this as a
  bug; the line was re-read and the finding retracted.)
- **Byte-length vs UTF-16 contract is consistent.** Dart sends `utf8` *byte* length; the C
  terminator check compares against that same byte length; `error_offsets()` walks UTF-8 lead
  bytes to build byte ranges and converts to **UTF-16 code units**, which is what Dart's
  `String.length` and the `endOffset > source.length` bound use. No unit mismatch at the
  boundary. (M5/M6 are the only edges.)
- **Visibility.** `C_VISIBILITY_PRESET hidden` plus explicit
  `visibility("default"), used` / `__declspec(dllexport)` is correct for both the shared
  builds and the Apple static archive.
- **iOS phase order.** `CF1100010000000000000003 /* Build Embedded Nginx */` sits at position
  5, before `97C146EA /* Sources */` and `97C146EB /* Frameworks */` (the link phase), so the
  archive named in `outputPaths` and consumed by `-force_load` exists before linking.
- **macOS Phase exists and is correctly ordered.** `macos/Runner.xcodeproj` runs
  `bundle_web_syntax_apple.sh` in `3399D490228B24CF009A79C7 /* ShellScript */` (position 9),
  after Flutter's `Bundle Framework` embed (position 8) and before target code signing. It
  installs into `$TARGET_BUILD_DIR/$CONTENTS_FOLDER_PATH/Frameworks`, sets
  `install_name_tool -id @rpath/...`, signs ad-hoc when `EXPANDED_CODE_SIGN_IDENTITY` is
  empty (`:-` default plus an explicit empty check), and uses
  `--timestamp --options runtime` only for a real identity. `outputPaths = ()` means it
  always runs, which is what a bundle-mutating phase needs.
- **macOS does not need `WebSyntax.xcconfig`.** `macos/Flutter/*.xcconfig` correctly omit it;
  the dylib is loaded via `DynamicLibrary.open` from `../Frameworks`, matching the Dart
  lookup for macOS.
- **Linux install target matches the Dart path.** `install(TARGETS qfli_web_syntax LIBRARY
  DESTINATION "${INSTALL_BUNDLE_LIB_DIR}")` with `INSTALL_BUNDLE_LIB_DIR =
  ${CMAKE_INSTALL_PREFIX}/lib` yields `<bundle>/lib/libqfli_web_syntax.so`, exactly the
  joined candidate in `_open()`.
- **Windows install target matches the Dart path.** `install(FILES ... DESTINATION
  ${INSTALL_BUNDLE_LIB_DIR})` with `INSTALL_BUNDLE_LIB_DIR = ${CMAKE_INSTALL_PREFIX}` puts
  `qfli_web_syntax.dll` beside the runner executable, matching
  `p.join(executableDirectory, 'qfli_web_syntax.dll')`. `add_dependencies(${BINARY_NAME}
  web_syntax_runtime)` is declared after `add_subdirectory("runner")`, so `BINARY_NAME`
  exists. (Correct layout, broken default toolchain — see B2.)
- **Android wiring.** `externalNativeBuild.cmake.path = file("../../native/web_syntax/
  CMakeLists.txt")` resolves to `<root>/native/web_syntax`; AGP packages every shared library
  the native build produces, so no `jniLibs` entry is needed; `-Wl,-z,max-page-size=16384` is
  applied for 16 KB pages. No `abiFilters` in Gradle, and the bridge is portable C, so the
  Flutter ABI set is fine.
- **Relative paths all resolve to `<root>/native/web_syntax`** from `linux/` (`../native/…`),
  `windows/` (`${CMAKE_CURRENT_SOURCE_DIR}/..`), `android/app/` (`../../native/…`) and
  `ohos/entry/src/main/cpp/` (`../../../../../native/…`, five levels up to the repo root).
- **`QFLI_WEB_SYNTAX_STATIC` defaults `OFF`**, so Android/Linux/Windows/OHOS build `SHARED`;
  only the Apple path produces an archive, and it does so through the Python driver rather
  than CMake — no platform accidentally gets a static parser.
- **Graceful runtime degradation.** `checkJavaScriptSyntax` returns an `available:false`
  result with a reason when the library is missing, and `WebCodeAnalyzer` folds that into
  `CodeAnalysisResult.unavailableReason` instead of pretending the code is clean.

---

## 5. Interaction with the backend owner's planned follow-ups

- **Windows clang + MinGW sysroot.** As planned, but see B2: the current default
  (`clang` preferred, sysroot optional) is the configuration most likely to fail on an
  ordinary dev machine, and it fails as `FATAL_ERROR`, taking the whole app build with it.
  Landing the sysroot work does not by itself fix the "no compiler on PATH" case.
- **Apple `--arch` / `--apple-sdk`.** Already threaded end to end
  (`bundle_web_syntax_apple.sh` → `build_web_syntax.py`, with the device/`arm64` guard and
  iOS-vs-macOS SDK cross-checks in place). Keep the per-`PLATFORM_NAME` output separation
  (M3) when touching it.
- **Apple hash verification.** `build_web_syntax.py` already verifies the pinned sources on
  every invocation, and the Xcode phase depends on `vendor/quickjs/SOURCE.json`, so a
  vendored change re-triggers the build. If post-link symbol assertion (M1) is added, put it
  in the same script so there is one place to audit.

---

## 6. Suggested order of work for the owner

1. B2 — stop the Windows `FATAL_ERROR` path from breaking `flutter build windows`; then
   prefer `gcc`, then require a sysroot for `clang`.
2. B1 — decide whether UI wiring lands in this release; if not, downgrade the delivery
   claim in the task notes to "native parser packaged, not yet surfaced".
3. Section 2 — one real `flutter build hap` with a HAP content listing settles OHOS.
4. M1 — add the `nm` assertion (or `-Wl,-u,_qfli_web_syntax_check`) for Apple Release.
5. B3/M5/M6/M2/M4 — cheap hardening once the above are settled.

## 7. What this review did not establish

- No build was executed for Windows, Linux, macOS, iOS, or Android; all statements about
  those are from configuration analysis only.
- OHOS packaging of the new `.so` is **unverified** (no device target, artifacts stale).
- Runtime `dlopen` success on Android/OHOS device was not observed (B3 reason).
- iOS Release dead-strip behaviour for `qfli_web_syntax_check` was not measured (M1).
