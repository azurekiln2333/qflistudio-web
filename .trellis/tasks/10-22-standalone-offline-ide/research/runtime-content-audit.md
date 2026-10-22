# Standalone runtime and bundled-content audit

Captured 2026-10-22; local source evidence, not a release or device pass. Scope: every `D:/MyNewProjects/qfli_*` repository. This worker changes only this research artifact. Other product coordinators are editing these worktrees concurrently; all counts and dirty snapshots below are time-specific. Recount from the final assets before signing, committing, or claiming completion.

## Source requirements retained

The attachment requires: audit **all existing examples against the actual OHOS runtime** before adding more than 100 substantive tested examples; all standalone editions; language chips and title badges; useful language tools directly in the tools tab; editor diagnostics and wave marks; persistent explorer expansion and multi-project workspace investigation; feasible run/debug/log/Problems/Output/Terminal/Ports functionality; complete language highlighting; working local C/C++ headers and Python modules; completely offline product flows; standard commits and push where possible. A host interpreter/compiler pass or a packaged filename cannot establish the OHOS requirement.

## Environment observed

- `hdc list targets` returned `[Empty]` on 2026-10-22. No OHOS target is currently available to this worker. This prevents current-artifact on-device runtime evidence; it does not prevent host auditing, compiling HAPs, or fixing source.
- Flutter: `D:/ProgramFiles/flutter_ohos/bin/flutter.bat`, 3.27.5-ohos-1.0.1; framework `12587c79e8`, engine `9161402dc0e134b3fb5adee5046b6e84b1a5e1c1`; Dart 3.11.5.
- HDC: `D:/ProgramFiles/Huawei/OpenHarmony/Sdk/23/toolchains/hdc.exe`.
- Hvigor and OHPM: `D:/ProgramFiles/Huawei/DevEco Studio/tools/{hvigor,ohpm}/bin/`.
- `DEVECO_SDK_HOME` and `HOS_SDK_HOME`: `D:/ProgramFiles/Huawei/DevEco Studio/sdk`; SDK trees include `default`, `hmscore`, `openharmony`; separate OpenHarmony SDKs `20` and `23` are installed.
- PATH tools: Node, Python 3.13, Java/javac 24.0.2, sqlite3, WSL. `clang`, `clang++`, `cmake`, `go`, `rustc`, `lua` were not found on Windows PATH, but project-local toolchains exist.
- WSL distributions: Ubuntu, qfli-terminal-test, qfli-terminal-al3-clean, qfli-terminal-al3-test, qfli-java-build. Presence is not proof their runtime/tool versions still match final app assets.
- Real host runtime files found: Python `native/build/windows/qfli_py_ffi.dll`; Lua `native/build/{host,windows}/libqfli_lua.dll`; C `native/build/compiler-linux/qfli_compiler_probe`, `native/build/ohos-wasi-thread-probe/runtime-probe-reviewed`, packaged WASI SDK resources; Go `native/build/verify-ohos/libqfli_go_runtime.so`. These require version/hash checks at execution time.

## Product and runtime map

The shared package `qfli_studio_core` is not a standalone app. Eleven standalone app repos were found. The shared product registry also names the online all-language QFLIStudio+ product; it is outside this standalone-only request unless its independent root is supplied.

| Repo / product | Catalog actually selected at inspection | OHOS execution route and material gap |
| --- | --- | --- |
| qfli_c / QFLIForge | Own `tool/forge_content/staging/forge_{tutorials,examples}.json`: 200 pairs, C100 + C++100, 200 lessons; `ForgeContentRepository` is wired in profile | Signed LLVM22.1/LLD compile C17/C++20 to WASI SDK33; signed WasmEdge interpreter, no JIT. OHOS ABI/SDK APIs are not WASI. Complete host WASI matrix exists as a verifier but must rerun against current binaries; target device still required. |
| qfli_dart / QFLIDartWing | Own `assets/content/dart_{tutorials,examples}.json`:120 pairs/120 lessons | OHOS uses `dart_eval`, not official Dart VM. `NativeDartToolchain.supported` includes Android/Windows/Linux/macOS only. Official host SDK verification alone misses OHOS language/library gaps; use portable verifier as separate gate. |
| qfli_go / QFLIGoShift | Shared Go slice120 pairs/120 lessons | Mobile FFI embeds patched vendored Yaegi; desktop uses official Go. All120 source topics currently declare `runtime:"desktop"`:87 single-file,15 module-project,18 test-package. Known Yaegi panics/output differences are recorded in `mobile_check/README.md`. A host Go pass cannot prove these all run in OHOS. |
| qfli_java / QFLIJVMX | Shared Java slice100 pairs/100 lessons; legacy Java catalog also exists | OpenJDK Zero native child via fork + dlopen/JLI_Launch, no ELF exec; `qfli_jvmx/jdk` prepare/start/poll/cancel. Check source target version against bundled JDK, run entire catalog inside final OHOS app. Spring Boot jars exist separately; not automatic evidence for base examples. |
| qfli_json / QFLIJson | Own `assets/content/{tutorials,examples}.json`:340 pairs/340 lessons | Product pure-Dart JSON validation/runner; use shipped service for examples, lessons, exercise answers, and exact offsets. Host parser tests establish logic; target HAP/UI still distinct. |
| qfli_lua / QFLIScript | Current profile has no contentRepositoryFactory and shared script filter includes Lua/JS/TS/shell:100 pairs each (400 pairs). Own Lua assets have140 examples +14 tutorial chapters containing140 lessons; own repository exists but was not wired in main at inspection | Native Lua5.4 works through FFI; LuaProgramRunner explicitly returns unavailable for JS/TS/shell on mobile, though these templates/content are exposed. Intended Lua repository retains non-Lua fallback: if connected unchanged it would yield440 examples/314 tutorial rows. All Script languages require an honest OHOS solution or explicit scope reconciliation; do not silently audit Lua only. |
| qfli_note / QFLINote | Current profile has no contentRepositoryFactory. Shared Markdown slice100 pairs is selected by common pages. New own assets currently220 examples over8 files +4 tutorial rows; `NoteContentRepository` has no other lib references yet | Pure-Dart Markdown parser/preview/export. Target checks concern rendering, local resources, interaction and no external requests, not native code execution. Own content wiring must be verified before counts can be claimed delivered. |
| qfli_python / QFLIPyFlow | Shared Python slice120 pairs/120 lessons plus legacy Python catalog | Embedded MicroPython1.24.1 (`ecfdd5d`), not CPython.4 authored topics explicitly require CPython and verifier runs them externally;116 default embedded topics. User's all-OHOS-runnable requirement is not met by relabeling those4. Project source/bytecode imports already work; pip/CPython extensions do not. |
| qfli_rust / QFLIRustCore | Own `assets/content_rust/{tutorials,examples}.json`:166 pairs/166 lessons | Pinned Rust1.98.1 compiler + Miri interpreter with fixed x86_64 Linux guest, native OHOS adapter. Existing spec says OHOS final HAP packaged but runtime-unverified without matched signed execution. Host rustc execution is separate from Miri and OHOS. External Cargo dependencies are not established. |
| qfli_sql / QFLISQLab | `SqlHomeShell`/workbench directly inject own SQL repo:126 pairs/126 lessons | SQLite and Oracle MySQL dialect paths are separate. Existing Python curriculum validator explicitly skips MySQL-only lessons; current profile `oracle-mysql-native` is unavailable. `sql_curriculum_native_test.dart` must exercise applicable bundled engines in app; SQLite host pass cannot cover MySQL. |
| qfli_web / QFLIWebForge | Own301 pairs/301 lessons:HTML100,CSS100,JS101 | Embedded upstream Nginx1.31.6 + local web preview/ArkWeb. Chromium behavior harness exists, but Chromium is not the target ArkWeb. Historical Oct12 signed phone pass does not establish fresh Oct15/Oct22 HAP execution. |

Shared aggregate `assets/content/{examples,tutorials}.json` each contains1640 entries: C100, C++100, Lua100, JavaScript100, TypeScript100, shell100, Rust100, Go120, HTML100, CSS100, Dart100, SQL100, JSON100, Markdown100, Java100, Python120. Product-owned catalogs replace or override only their own paths; do not count unrelated shared rows as delivered examples of each app.

Legacy catalogs additionally exist under core `assets/tutorials/{c,cpp,dart,java,lua,python,web}.json`. Python has120 legacy examples and Java100. They must either be included in the all-content inventory or shown unreachable in the current UI; do not discard them solely because aggregate assets also exist.

## C/C++ project headers and multi-file evidence

- Source-selection implementation: `qfli_c/lib/source_selection.dart`. It retains selected entry and helper units while excluding another unambiguous top-level main; C++ units remain `.cpp` and C units `.c`.
- Portable compiler implementation: `native/compiler/compiler.cpp` adds both `-I <project>` and `-I <project>/include`; terminal command path also appends user-supplied confined include dirs. Clang itself resolves quoted headers relative to each source file.
- Portable compiler compiles translation units separately, then links. Header files are not themselves translation units. Canonical source/working/include/output paths must stay inside project; source existence/uniqueness/selected-entry membership are validated.
- Existing curriculum schema has no extra-file field; all200 samples must be self-contained. This proves nothing about actual imported multi-file projects.
- Required current-device fixtures: C `include/math_utils.h` + `src/math_utils.c` + `src/main.c`; C++ `include/widget.hpp` + `src/widget.cpp` + `src/main.cpp`; both execute and compare output. Include `extern "C"` mixed C/C++, duplicate-main selection, a missing header, compile/link diagnostics, nested directory quoted includes, non-ASCII/spaced project paths, and confinement rejection. Exercise both run button and terminal compiler/explicit program execution. Reuse runner/native bridge tests where coverage exists rather than source-string checks.

## Python modules and pip constraints

- `native/micropython_embed/port/mpconfigport.h` has persistent bytecode LOAD/SAVE enabled; `MICROPY_PY_OS=0`, HASHLIB/SELECT/UCTYPES/ASYNCIO/DEFLATE/FRAMEBUF/PLATFORM disabled. VFS is disabled but custom/POSIX project readers exist. Final built runtime `help('modules')`/actual imports should be the authoritative capability list.
- Native runtime initializes `sys.path` with entry directory and project root. Upstream `.py` and compatible `.mpy` imports are implemented and VM/module state is reset per invocation. Existing specs/tests cover helper/package import, file I/O, source-free bytecode, cancellation and stale-import refresh.
- `checkSyntax` compiles only; it does not resolve imports. A green syntax check cannot prove modules available.
- No shipped pip or CPython extension ABI. CPython wheels and common native libraries cannot simply be copied into this VM. Existing MicroPython config also lacks the filesystem/network/deflate facilities a normal pip installation assumes.
- Practical offline module management: enumerate real builtins and project-local packages; import an already downloaded local directory/archive of compatible pure `.py`/`.mpy` files; validate actual imports with the same embedded runtime; show failed imports accurately; no index lookup/download. Archive extraction should reject traversal/conflicting destinations and preserve project data. Native modules require an intentional rebuild/integration for the MicroPython port, with licenses and target tests.
- This is a proposed scope, not an implemented package manager. Ask the Python coordinator to select actual compatible common modules based on all shipped imports and ensure each runnable lesson executes on the embedded target. Do not substitute CPython tests for the four known incompatible lessons.

## Executable validation commands

Commands below are discovered interfaces, not new pass claims. Run from each indicated repo; preserve serialized Flutter pub/build/test ownership. No Flutter test/build was launched by this read-only research worker.

Common per repo:

```powershell
flutter analyze --no-pub lib test
flutter test --no-pub --concurrency=1
hdc list targets
```

C/C++:

```powershell
dart run tool/verify_forge_content.dart
flutter test --no-pub --concurrency=1 test/forge_content_repository_test.dart test/forge_content_integration_test.dart test/ohos_native_runner_test.dart
wsl -d qfli-java-build python3 /mnt/d/MyNewProjects/qfli_c/native/toolchain/tests/portable-curriculum-regression.py --compiler /mnt/d/MyNewProjects/qfli_c/native/build/compiler-linux/qfli_compiler_probe --runtime /mnt/d/MyNewProjects/qfli_c/native/build/ohos-wasi-thread-probe/runtime-probe-reviewed --sdk /mnt/d/MyNewProjects/qfli_c/native/build/portable-deps/wasi-sdk-33.0-x86_64-linux --report /mnt/d/MyNewProjects/qfli_c/native/build/portable-curriculum-current.json
```

The C matrix currently hardcodes exactly100+100 IDs; expansion must update its manifest/expected inventory from reviewed authored data, while retaining full-set equality and no partial-prefix passes.

Dart:

```powershell
dart run tool/verify_dart_content.dart
dart run tool/verify_portable_content.dart --report build/portable-content-current.json
```

Go:

```powershell
python tool/go_curriculum/verify.py --go native/build/go-sdk-1.27.1/go/bin/go.exe --json
python tool/go_curriculum/dedup.py
python tool/go_curriculum/mobile_check/run_yagi.py
flutter test -d <ohos-device> integration_test/go_native_test.dart
```

Use `mobile_check/run_native_check.sh` with its samples/output arguments to run shipped patched `runGo` on host. Bare Yaegi is only a screen, not shipped-runtime or device proof. Native module gates are `go test -mod=vendor ./...` and `go vet -mod=vendor ./...` inside `native/go_runtime`.

Java (core and app respectively):

```powershell
dart run tool/verify_java_content.dart <actual-jdk-home> --report build/java-content-current.json
flutter run -d <ohos-device> -t tools/java_catalog_ohos_smoke.dart
flutter run -d <ohos-device> -t tools/jdk_smoke.dart
```

Check smoke source entry/protocol before deployment; restore/rebuild the normal app afterwards and coordinate device windows. Actual runtime version and all catalog case IDs must be recorded.

Python (core, then app):

```powershell
dart run tool/verify_python_content.dart ../qfli_python/native/build/windows/qfli_py_ffi.dll python
node native/tests/ohos_channel_test.cjs
dart run tool/python_ffi_smoke.dart
```

Core verifier explicitly separates embedded and CPython totals. Require embedded result per shipped runnable topic; do not sum separate totals as an OHOS pass. Native real-library suite: `sh native/tests/run_host.sh` under a valid POSIX host.

Lua:

```powershell
dart run tool/verify_lua_content.dart --quiet --json build/lua-content-current.json
dart run tools/lua_stdin_smoke.dart
flutter run -d <ohos-device> -t tool/lua_device_probe.dart
```

Inspect runtime/DLL discovery override in source before running. Current verifier covers Lua only; Script JS/TS/shell need their own actual OHOS backends and full inventories.

Rust:

```powershell
python scripts/verify_rust_content.py --report build/rust-content-current.json
python scripts/test_rust_content.py
flutter test -d <ohos-device> integration_test/rust_native_test.dart
```

Confirm actual integration filename first (`integration_test/` has runtime tests under nested dirs); host compiler verifier compiles/runs native programs, not Miri. Do not use `--structure-only` as execution proof.

SQL:

```powershell
python tool/sql_curriculum/validate_content.py
flutter test --no-pub --concurrency=1 test/sql_curriculum_test.dart test/sql_offline_policy_test.dart
flutter test -d <ohos-device> integration_test/sql_curriculum_native_test.dart
```

The Python validator names and excludes MySQL-only lessons. A complete SQL audit must separately execute every dialect on its applicable shipped engine.

JSON / Markdown:

```powershell
# qfli_json
flutter test --no-pub --concurrency=1 test/json_content_test.dart test/json_runner_test.dart
# qfli_note
dart run tool/verify_note_content.dart
flutter test --no-pub --concurrency=1 test/markdown_analysis_test.dart test/markdown_offline_test.dart
```

Web:

```powershell
python scripts/audit_web_content.py --product
node scripts/run_examples.mjs --report build/content/example-execution-current.md
flutter test -d <ohos-device> integration_test/nginx_runtime_test.dart
flutter test -d <ohos-device> integration_test/content_import_test.dart
```

Actually run by this worker: `python scripts/audit_web_content.py --product` returned exit0,301 examples,301 tutorials,301 distinct normalized lesson/example bodies, zero structural/content issues. This is not browser execution. Other commands above were discovered/read, not executed here.

## Browser harness coverage and OHOS JS bridge research

`qfli_web/scripts/run_examples.mjs` loads current301 examples and all tutorial lessons, checks paired code after removing the injected marker, starts a loopback HTTP server, creates fresh Chromium contexts, captures page errors/console/resource failures, aborts and fails every nonlocal request, and delegates behavior to independent `js_example_assertions.mjs` and `web_markup_assertions.mjs`. JS oracle currently covers101 JS IDs; HTML/CSS oracle has per-topic DOM/computed-style/layout checks. One deliberate missing image is exactly allowlisted (`html-example-006`, `/missing.png`). Playwright is installed locally under node_modules.

Limitations: `--limit` intentionally executes only a prefix, so it must never support the full-inventory acceptance claim. Lessons are deduplicated/paired, not separately executed; exercise answers are not looped by this harness. Chromium API/CSS support differs from OHOS ArkWeb. A full run report should include exact301 IDs, browser version, source/catalog hashes, assertion totals and no missing oracle; future expanded inventory must drive oracle completeness explicitly. No current run of this full harness was performed by the research worker.

The installed local OHOS SDK primary declaration `D:/ProgramFiles/Huawei/DevEco Studio/sdk/default/openharmony/ets/api/@ohos.web.webview.d.ts` exposes:

- `loadData(data,mimeType,encoding,baseUrl?,historyUrl?)` (line3004)
- `registerJavaScriptProxy(jsObject,name,methodList,asyncMethodList?,permission?)` (line3280)
- `deleteJavaScriptRegister(name)` (line3295)
- `runJavaScript(script): Promise<string>` and callback overload (lines3384/3409)

ArkUI `component/web.d.ts` exposes `onConsole` (line6393), `onInterceptRequest` (6612), `onOverrideUrlLoading` (7486). The repo's `ohos/entry/src/main/ets/pages/AgreementReader.ets` already instantiates ArkWeb with JavaScript enabled, but it is a remote-agreement reader and is not an offline curriculum execution bridge.

A product-owned local verification page can load exact example HTML using the existing local server/loadData, use a narrowly scoped JS proxy to return structured assertions, capture native console/errors, and intercept every request to allow only app-local data/blob/loopback resources. A probe must not depend on Playwright or downloaded scripts on device. Test actual required APIs (canvas, Intl, URL, Blob/object URLs, ResizeObserver, requestAnimationFrame, DOM/CSS selectors) against the installed ArkWeb version; do not infer them from the SDK API existing. JS-only evaluator can test syntax/runtime primitives but does not substitute for DOM/CSS example behavior. Implement under WebForge ownership with final HAP/device gates.

## Evidence gates and fixes needed

1. Freeze a reviewed final per-app inventory of every example, tutorial lesson and exercise answer, with language, executable backend, input fixture, expected output/behavior and SHA256. Resolve local catalogs not yet selected by profiles before counting delivered content.
2. First audit unchanged existing data through actual embedded backend equivalents; repair incompatible Python4, all Go desktop-only classifications/runtime gaps, Script JS/TS/shell mobile absence, and SQL MySQL exclusions. Do not conceal incompatible runnable examples under labels or desktop-only test reports.
3. Add substantive more-than100 examples only after the full existing set has a known result. Widen exact-ID verifiers with full authored manifests; never loosen to `>=100` alone or keep fixed old200 IDs after C expansion.
4. Run host/embedded matrices, build current target HAPs, inspect native ABI and asset counts/hashes, then execute each case in the signed packaged app on OHOS. No connected OHOS device now means this last gate is pending, not green.
5. Preserve global single shared-core writer and serialized platform tooling. Existing dirty state below belongs to coordinators/user; research does not own it. Final commits use explicit reviewed paths and each repo's recent commit conventions; push is root/coordinator scope, not this worker.

## Snapshot of repositories and dirty paths

The following snapshot was collected when this report was written; multiple live product coordinators may change it later. It is an ownership baseline, not a list of files this worker edited.


### qfli_c

Branch `main`; HEAD `35854d9`.

```text
M .trellis/spec/backend/ohos-runtime.md
 M .trellis/spec/backend/portable-runtime.md
 M .trellis/workspace/lichengyu/index.md
 M .trellis/workspace/lichengyu/journal-1.md
 M README.md
 M assets/app_icon.png
 M lib/forge_tools_page.dart
 M lib/main.dart
 M lib/native_clang_runner.dart
 M native/compiler/compiler.cpp
 M native/compiler/include/qfli_compiler.h
 M native/portable/include/qfli_wasm.h
 M native/portable/wasm_runtime.cpp
 M native/toolchain/tests/ohos-portable-bridge-regression.py
 M native/toolchain/tests/portable-curriculum-regression.py
 M ohos/AppScope/app.json5
 M ohos/AppScope/resources/base/media/app_icon.png
 M ohos/build-profile.json5
 M ohos/entry/build-profile.json5
 M ohos/entry/src/main/cpp/qfli_ohos_portable.cpp
 M ohos/entry/src/main/cpp/types/libqfli_ohos_runner/index.d.ts
 M ohos/entry/src/main/ets/entryability/EntryAbility.ets
 M ohos/entry/src/main/ets/pages/Index.ets
 M ohos/entry/src/main/ets/plugins/QfliCNative.ets
 M ohos/entry/src/main/module.json5
 M test/forge_tools_test.dart
 M tool/forge_content/verify_forge_content.dart
?? .trellis/tasks/10-22-offline-standalone-ide/
?? .trellis/tasks/archive/2026-10/10-17-forge-ohos-startup-icon/
?? .trellis/tasks/archive/2026-10/10-17-forge-terminal-ui-delivery/
?? LICENSE
?? lib/forge_development_tools.dart
?? lib/forge_terminal.dart
?? lib/forge_terminal_browser.dart
?? lib/forge_terminal_native.dart
?? lib/ohos_startup.dart
?? test/forge_development_tools_test.dart
?? test/forge_terminal_lifecycle_test.dart
?? test/forge_terminal_test.dart
?? test/ohos_startup_test.dart
?? tool/build_ohos_release.ps1
?? tool/ohos_terminal_audit.dart
```


### qfli_dart

Branch `main`; HEAD `788a519`.

```text
M .trellis/spec/backend/dart-native-runtime.md
 M .trellis/spec/frontend/index.md
 M README.md
 M lib/dart_tools.dart
 M lib/dart_tools_page.dart
 M lib/main.dart
 M ohos/AppScope/app.json5
 M ohos/build-profile.json5
 M ohos/entry/build-profile.json5
 M ohos/entry/src/main/ets/entryability/EntryAbility.ets
 M ohos/entry/src/main/ets/pages/Index.ets
 M ohos/entry/src/main/module.json5
 M test/dart_tools_page_test.dart
 M test/dart_tools_test.dart
?? .trellis/.runtime/sessions/codex_01a15fa0-eba3-7de1-b40c-6f88a3b2c1ca.json
?? .trellis/spec/frontend/ohos-startup.md
?? .trellis/tasks/10-22-offline-ide-completeness/
?? LICENSE
?? lib/dart_code_analyzer.dart
?? test/dart_code_analyzer_test.dart
?? test/dart_startup_test.dart
?? tool/portable_content_runner.dart
?? tool/verify_portable_content.dart
```


### qfli_go

Branch `fix/go-release-integrity`; HEAD `82e17af`.

```text
M ohos/AppScope/app.json5
 M ohos/AppScope/resources/base/media/app_icon.png
 M ohos/build-profile.json5
 M ohos/entry/build-profile.json5
 M ohos/entry/src/main/module.json5
 M ohos/entry/src/main/resources/base/media/icon.png
?? .codex/
?? .trellis/tasks/10-22-go-curriculum-ohos/
?? .trellis/tasks/10-22-go-offline-ide/
?? .trellis/tasks/10-22-standalone-ide-completeness/
?? .trellis/tasks/10-22-standalone-integration/
?? LICENSE
?? linux/flutter/generated_plugin_registrant.cc
?? linux/flutter/generated_plugin_registrant.h
?? macos/Flutter/GeneratedPluginRegistrant.swift
?? windows/flutter/generated_plugin_registrant.cc
?? windows/flutter/generated_plugin_registrant.h
```


### qfli_java

Branch `main`; HEAD `6216a3f`.

```text
M lib/java_runner.dart
 M lib/java_tools_page.dart
?? .trellis/tasks/10-22-offline-ide-completeness/
?? lib/java_catalog_audit.dart
?? lib/java_developer_tool_pages.dart
?? lib/java_developer_tools.dart
?? lib/java_diagnostics.dart
?? test/fixtures/
?? test/java_catalog_audit_test.dart
?? test/java_developer_tool_pages_test.dart
?? test/java_developer_tools_test.dart
?? test/java_diagnostics_test.dart
?? tools/java_catalog_ohos_smoke.dart
```


### qfli_json

Branch `feat/offline-json-workbench`; HEAD `aeff00f`.

```text
M .gitignore
 M lib/main.dart
 M ohos/build-profile.json5
 M ohos/entry/src/main/ets/entryability/EntryAbility.ets
 M ohos/entry/src/main/module.json5
 M ohos/entry/src/main/resources/base/profile/main_pages.json
 M pubspec.yaml
 M test/json_app_test.dart
?? .trellis/
?? LICENSE
?? assets/content/
?? lib/content/
?? lib/json/
?? linux/flutter/generated_plugin_registrant.cc
?? linux/flutter/generated_plugin_registrant.h
?? macos/Flutter/GeneratedPluginRegistrant.swift
?? ohos/entry/src/main/ets/pages/AgreementReader.ets
?? test/json_content_test.dart
?? test/json_editor_test.dart
?? test/json_offline_host_test.dart
?? test/json_runner_test.dart
?? test/json_workbench_test.dart
?? tool/
?? windows/flutter/generated_plugin_registrant.cc
?? windows/flutter/generated_plugin_registrant.h
```


### qfli_lua

Branch `main`; HEAD `327b7c5`.

```text
M assets/app_icon.png
 M lib/lua_runner.dart
 M lib/lua_toolchain.dart
 M lib/main.dart
 M native/README.md
 M native/src/qfli_lua.c
 M native/src/qfli_lua.h
 M native/src/qfli_lua_windows.c
 M native/src/qfli_lua_windows.h
 M native/test/qfli_lua_test.c
 M ohos/AppScope/resources/base/media/app_icon.png
 M ohos/build-profile.json5
 M ohos/entry/build-profile.json5
 M ohos/entry/hvigorfile.ts
 M ohos/entry/src/main/ets/entryability/EntryAbility.ets
 M ohos/entry/src/main/ets/pages/Index.ets
 M ohos/entry/src/main/module.json5
 M ohos/entry/src/main/resources/base/media/icon.png
 M pubspec.lock
 M pubspec.yaml
 M test/lua_app_test.dart
?? .codex/
?? .gitattributes
?? .tmp_bytecode_block.txt
?? .trae/
?? .trellis/tasks/10-01-content-code-import/
?? .trellis/tasks/10-08-ohpm-lock-repair/
?? .trellis/tasks/10-09-terminal-polish/
?? .trellis/tasks/10-22-offline-ide-completeness/
?? AGENTS.md
?? assets/content/
?? lib/lua_code_analyzer.dart
?? lib/lua_content_repository.dart
?? lib/lua_terminal_commands.dart
?? lib/lua_tools.dart
?? lib/lua_tools_page.dart
?? ohos/entry/src/main/ets/pages/AgreementReader.ets
?? test/code_import_service_test.dart
?? test/content_import_workflow_test.dart
?? test/lua_offline_platform_test.dart
?? test/lua_tools_page_test.dart
?? test/lua_tools_test.dart
?? test/startup_test.dart
?? tool/generate_lua_content.dart
?? tool/lua_content/
?? tool/verify_lua_content.dart
?? tools/
```


### qfli_note

Branch `main`; HEAD `06e998b`.

```text
M android/app/src/main/AndroidManifest.xml
 M android/app/src/main/kotlin/com/example/qflistudio/c/MainActivity.kt
 M ios/Runner/AppDelegate.swift
 M ios/Runner/Info.plist
 M lib/main.dart
 M macos/Runner/AppDelegate.swift
 M macos/Runner/DebugProfile.entitlements
 M macos/Runner/Info.plist
 M macos/Runner/Release.entitlements
 M ohos/entry/src/main/ets/entryability/EntryAbility.ets
 M ohos/entry/src/main/ets/entryability/PickerBridge.ets
 M ohos/entry/src/main/module.json5
 M ohos/entry/src/main/resources/base/profile/main_pages.json
 M pubspec.lock
 M pubspec.yaml
 M windows/runner/Runner.rc
?? .codex/
?? .gitattributes
?? .opencode/
?? .trae/
?? .trellis/
?? AGENTS.md
?? assets/content/
?? lib/content/
?? lib/document/
?? lib/markdown/
?? lib/workspace/
?? linux/flutter/generated_plugin_registrant.cc
?? linux/flutter/generated_plugin_registrant.h
?? macos/Flutter/GeneratedPluginRegistrant.swift
?? ohos/entry/src/main/ets/entryability/DocumentBridge.ets
?? ohos/entry/src/main/ets/pages/AgreementReader.ets
?? test/_probe_link_test.dart
?? test/external_open_test.dart
?? test/markdown_analysis_test.dart
?? test/markdown_commands_test.dart
?? test/markdown_diagnostics_test.dart
?? test/markdown_offline_test.dart
?? test/markdown_tools_test.dart
?? test/markdown_widgets_test.dart
?? test/note_content_test.dart
?? test/offline_workspace_test.dart
?? tool/
?? windows/flutter/generated_plugin_registrant.cc
?? windows/flutter/generated_plugin_registrant.h
```


### qfli_python

Branch `release/python-storefront-20261015`; HEAD `5674a30`.

```text
M .trellis/spec/frontend/native-startup.md
 M .trellis/spec/frontend/python-workflow.md
 M README.md
 M assets/app_icon.png
 M lib/main.dart
 M lib/python_tools_page.dart
 M ohos/AppScope/resources/base/media/app_icon.png
 M ohos/build-profile.json5
 M ohos/entry/build-profile.json5
 M ohos/entry/src/main/ets/entryability/EntryAbility.ets
 M ohos/entry/src/main/ets/pages/Index.ets
 M ohos/entry/src/main/module.json5
 M ohos/entry/src/main/resources/base/media/icon.png
 M ohos/entry/src/main/resources/base/profile/main_pages.json
 M test/python_tools_page_test.dart
 M test/startup_test.dart
?? .codex/
?? .gitattributes
?? .trae/
?? .trellis/tasks/10-22-offline-language-apps/
?? .trellis/tasks/10-22-python-content-ohos/
?? .trellis/tasks/10-22-python-offline-debugger/
?? .trellis/tasks/10-22-python-offline-modules/
?? .trellis/tasks/10-22-python-offline-tools/
?? AGENTS.md
?? ohos/entry/src/main/ets/pages/AgreementReader.ets
```


### qfli_rust

Branch `main`; HEAD `78fb7b1`.

```text
M native/README.md
 M ohos/AppScope/app.json5
 M ohos/entry/build-profile.json5
?? .codex/
?? .gitattributes
?? .trae/
?? .trellis/tasks/10-09-terminal-run-controls/research/baseline-verification.md
?? .trellis/tasks/10-09-terminal-run-controls/research/baseline/
?? .trellis/tasks/10-09-terminal-run-controls/research/changed-files.json
?? .trellis/tasks/10-09-terminal-run-controls/research/commit-review.md
?? .trellis/tasks/10-09-terminal-run-controls/research/generate_review.py
?? .trellis/tasks/10-09-terminal-run-controls/research/integration-audit.md
?? .trellis/tasks/10-09-terminal-run-controls/research/pi-implementation-brief.txt
?? .trellis/tasks/10-09-terminal-run-controls/research/pi-implementation-report.md
?? .trellis/tasks/10-09-terminal-run-controls/research/pi-review-round1.txt
?? .trellis/tasks/10-09-terminal-run-controls/research/prepare_commit_review.py
?? .trellis/tasks/10-09-terminal-run-controls/research/screenshots/
?? .trellis/tasks/10-09-terminal-run-controls/research/task-only.patch
?? .trellis/tasks/10-09-terminal-run-controls/research/terminal_visual_test.dart
?? .trellis/tasks/archive/2026-10/10-01-tutorial-code-import/apply-shared.ps1
?? .trellis/tasks/archive/2026-10/10-01-tutorial-code-import/count.patch
?? .trellis/tasks/archive/2026-10/10-01-tutorial-code-import/evict.patch
?? .trellis/tasks/archive/2026-10/10-01-tutorial-code-import/generate-review.ps1
?? .trellis/tasks/archive/2026-10/10-01-tutorial-code-import/review.patch
?? .trellis/tasks/archive/2026-10/10-01-tutorial-code-import/review/
?? .trellis/tasks/archive/2026-10/10-01-tutorial-code-import/screenshots/
?? .trellis/tasks/archive/2026-10/10-01-tutorial-code-import/snapshots/
?? .trellis/tasks/archive/2026-10/10-01-tutorial-code-import/work/
?? AGENTS.md
?? linux/flutter/generated_plugin_registrant.cc
?? linux/flutter/generated_plugin_registrant.h
?? macos/Flutter/GeneratedPluginRegistrant.swift
?? windows/flutter/generated_plugin_registrant.cc
?? windows/flutter/generated_plugin_registrant.h
```


### qfli_sql

Branch `main`; HEAD `42602e3`.

```text
M .trellis/spec/backend/index.md
 M .trellis/spec/backend/mysql-desktop-runtime.md
 M .trellis/spec/frontend/index.md
 M .trellis/tasks/09-30-local-mysql-workbench/design.md
 M .trellis/tasks/09-30-local-mysql-workbench/implement.md
 M lib/local_mysql_runtime.dart
 M lib/main.dart
 M macos/Runner.xcodeproj/project.pbxproj
 M macos/Runner/DebugProfile.entitlements
 M macos/Runner/Release.entitlements
 M native/mysql/desktop/CMakeLists.txt
 M native/mysql/desktop/README.md
 M ohos/build-profile.json5
 M ohos/entry/.gitignore
 M ohos/entry/build-profile.json5
 M ohos/entry/src/main/ets/entryability/EntryAbility.ets
 M ohos/entry/src/main/ets/pages/Index.ets
 M ohos/entry/src/main/resources/base/media/icon.png
 M ohos/entry/src/main/resources/base/profile/main_pages.json
 M pubspec.lock
 M pubspec.yaml
?? .codex/
?? .opencode/
?? .trae/
?? .trellis/tasks/09-30-local-mysql-workbench/check.jsonl
?? .trellis/tasks/09-30-local-mysql-workbench/implement.jsonl
?? .trellis/tasks/09-30-local-mysql-workbench/research/baseline/
?? .trellis/tasks/09-30-local-mysql-workbench/research/home-tree-projects-page-design.md
?? .trellis/tasks/09-30-local-mysql-workbench/research/ohos-resume-2026-10-09.md
?? .trellis/tasks/09-30-local-mysql-workbench/research/option-b-private-preload-design.md
?? .trellis/tasks/09-30-local-mysql-workbench/research/phone-acceptance-main-2026-10-09.md
?? .trellis/tasks/09-30-local-mysql-workbench/research/phone-acceptance-probe.md
?? .trellis/tasks/09-30-local-mysql-workbench/research/phone-debug-progress.md
?? .trellis/tasks/09-30-local-mysql-workbench/research/phone-extension-companion-boundaries-2026-10-09.md
?? .trellis/tasks/09-30-local-mysql-workbench/research/phone-host-options-2026-10-09.md
?? .trellis/tasks/09-30-local-mysql-workbench/research/phone-musl-interpreter-support-2026-10-09.md
?? .trellis/tasks/09-30-local-mysql-workbench/research/phone-native-host.md
?? .trellis/tasks/09-30-local-mysql-workbench/research/phone-parent-preload-fork-safety-2026-10-09.md
?? .trellis/tasks/09-30-local-mysql-workbench/research/phone-process-host-capabilities-sdk26-2026-10-09.md
?? .trellis/tasks/09-30-local-mysql-workbench/research/phone-thread-host-lifecycle-2026-10-09.md
?? .trellis/tasks/09-30-local-mysql-workbench/research/provenance-summary-2026-10-09.md
?? .trellis/tasks/09-30-local-mysql-workbench/research/reviewer-stdio-fork-protocol-2026-10-09.md
?? .trellis/tasks/09-30-local-mysql-workbench/research/status-check-2026-10-15.md
?? .trellis/tasks/10-01-cross-platform-native-runtimes/
?? .trellis/tasks/10-01-tutorial-code-import/
?? .trellis/tasks/10-12-sql-curriculum-and-home/
?? .trellis/tasks/10-12-sql-home-tree/
?? .trellis/tasks/10-12-sql-lesson-curriculum/
?? .trellis/tasks/10-15-sql-release-readiness/research/android-fix-plan.md
?? .trellis/tasks/10-15-sql-release-readiness/research/android-release-run.png
?? .trellis/tasks/10-15-sql-release-readiness/research/baseline-git-status.txt
?? .trellis/tasks/10-15-sql-release-readiness/research/blocker-report.md
?? .trellis/tasks/10-15-sql-release-readiness/research/device-window-request.txt
?? .trellis/tasks/10-15-sql-release-readiness/research/emulator-5582.log.err
?? .trellis/tasks/10-15-sql-release-readiness/research/ohos-push-14u.md
?? .trellis/tasks/10-15-sql-release-readiness/research/platform-coordination-note.md
?? .trellis/tasks/10-15-sql-release-readiness/research/sdk-window-request-platform.md
?? .trellis/tasks/10-22-offline-ide-completeness/
?? AGENTS.md
?? SU5URUdSQVRJT05fVEVTVF9TSE9VTERfUkVQT1JUX1JFU1VMVFNfVE9fTkFUSVZFPWZhbHNl
?? SU5URUdSQVRJT05fVEVTVF9TSE9VTERfUkVQT1JUX1JFU1VMVFNfVE9fTkFUSVZFPXRydWU=
?? integration_test/mysql_ohos_probe.dart
?? linux/flutter/generated_plugin_registrant.cc
?? linux/flutter/generated_plugin_registrant.h
?? macos/Flutter/GeneratedPluginRegistrant.swift
?? native/mysql/macos/
?? native/mysql/qfli_mysql_server.map
?? native/tests/audit-ctor-sources.sh
?? native/tests/build-preload-prototype.sh
?? native/tests/build-with-fence.sh
?? native/tests/check-trace-markers.sh
?? native/tests/cold-backup-prod-mysql.sh
?? native/tests/cold-backup-verified.ps1
?? native/tests/debug-ctors.py
?? native/tests/experiment-private-binding.sh
?? native/tests/experiment-static-libcxx.sh
?? native/tests/find-warning-emitter.sh
?? native/tests/inspect-binding.sh
?? native/tests/inspect-ctors.sh
?? native/tests/inspect-fd-report.sh
?? native/tests/inspect-libcxx-archives.sh
?? native/tests/inspect-visibility.sh
?? native/tests/probe-atomic-fence.sh
?? native/tests/prove-fence-branch.sh
?? native/tests/qfli_mysql_ctor_audit.sh
?? native/tests/rebuild-ohos-package.sh
?? native/tests/resolve-ctors.py
?? native/tests/stage-back-package.sh
?? native/tests/stage-proto-dso.sh
?? native/tests/trace-fence-emitter.sh
?? native/tests/verify-package.sh
?? native/tests/verify-preload-prototype.sh
?? native/tests/verify-static-closure.sh
?? ohos/entry/src/main/ets/pages/AgreementReader.ets
?? research/
?? test/startup_test.dart
?? tool/sql_curriculum/COLLABORATOR_CONTRACT.md
?? tool/sql_curriculum/lessons/_collab_status-2.md
?? windows/flutter/generated_plugin_registrant.cc
?? windows/flutter/generated_plugin_registrant.h
```


### qfli_studio_core

Branch `main`; HEAD `6441a5a`.

```text
M lib/content/local_content_adapter.dart
 M lib/editor/file_explorer.dart
 M lib/editor/project_history.dart
 M lib/models/tutorial.dart
 M lib/pages/local_content_pages.dart
 M lib/services/example_code_store.dart
 M lib/services/studio_profile.dart
 M lib/services/tutorial_service.dart
 M lib/widgets/project_card.dart
 M test/local_content_lazy_catalog_test.dart
 M tool/verify_java_content.dart
?? .trellis/tasks/10-22-offline-content-explorer/
?? .trellis/tasks/10-22-offline-editor-analysis/
?? lib/content/java_catalog_audit.dart
?? lib/services/code_analysis.dart
?? lib/widgets/language_badge.dart
?? test/file_explorer_state_test.dart
?? test/local_content_filters_test.dart
?? test/project_history_concurrency_test.dart
?? tool/java_content/java_topics_io_time.dart
?? tool/java_content/java_topics_language.dart
```


### qfli_web

Branch `main`; HEAD `c6fedb0`.

```text
M .trellis/spec/frontend/index.md
 M .trellis/tasks/10-02-native-runtime-platform-audit/design.md
 M .trellis/tasks/10-02-native-runtime-platform-audit/implement.md
 M .trellis/tasks/10-02-native-runtime-platform-audit/research/platform-matrix.md
 M .trellis/tasks/10-02-native-runtime-platform-audit/research/verification-2026-10-02.md
 M lib/main.dart
 M ohos/entry/src/main/ets/entryability/EntryAbility.ets
 M ohos/entry/src/main/ets/pages/Index.ets
 M pubspec.lock
 M pubspec.yaml
 M scripts/run_examples.mjs
 M test/web_tools_navigation_test.dart
?? .gitattributes
?? .opencode/
?? .trellis/tasks/09-30-webforge-local-runtime/check.jsonl
?? .trellis/tasks/09-30-webforge-local-runtime/implement.jsonl
?? .trellis/tasks/10-01-content-code-import/check.jsonl
?? .trellis/tasks/10-01-content-code-import/implement.jsonl
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/c-android-audit.dart
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/c-android-editor-evidence.patch
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/c-android-verification-2026-10-02.md
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/dart-native-contract.patch
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/dart-native-desktop.patch
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/go-delivery-validation.patch
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/go-profile-delivery.patch
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/java-android-apk-audit.ps1
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/java-android-delivery.patch
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/java-android-elf-audit.ps1
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/java-arm64-commit-plan.json
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/java-arm64-evidence.patch
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/java-arm64-verification-2026-10-02.md
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/lua-android-validation.patch
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/lua-stdin-delivery.patch
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/mysql-desktop-delivery.patch
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/mysql-macos-commit-plan.json
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/mysql-macos-delivery.patch
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/mysql-macos-verification-2026-10-02.md
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/nginx-embedded-commit-plan.json
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/nginx-embedded-verification-2026-10-02.md
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/python-docs-routing.patch
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/python-lifecycle.patch
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/python-linux-lifecycle.py
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/python-linux-lifecycle.sh
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/python-native-runner-test.patch
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/python-windows-reader.patch
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/rust-android-verification-2026-10-02.md
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/rust-commit-plan.json
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/sqlite-commit-dispatch.patch
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/sqlite-default-runner.patch
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/sqlite-final-tests.patch
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/sqlite-frontend-contract.patch
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/sqlite-native-platforms.patch
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/sqlite-platform-dispatch.patch
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/sqlite-script-compatibility.patch
?? .trellis/tasks/10-02-native-runtime-platform-audit/research/sqlite-ui-script-delta.patch
?? .trellis/tasks/10-09-web-terminal-current-file/research/README-core-patch.md
?? .trellis/tasks/10-09-web-terminal-current-file/research/core-baseline/
?? .trellis/tasks/10-09-web-terminal-current-file/research/core-web-preview-file.patch
?? .trellis/tasks/10-09-web-terminal-current-file/research/proposed/
?? .trellis/tasks/10-09-web-terminal-current-file/research/web-baseline/
?? .trellis/tasks/10-09-web-terminal-current-file/research/web-implementation-results.md
?? .trellis/tasks/10-22-standalone-offline-ide/
?? AGENTS.md
?? LICENSE
?? lib/services/web_css_tools.dart
?? lib/services/web_markup_inspector.dart
?? lib/services/web_source_scan.dart
?? ohos/entry/src/main/ets/pages/AgreementReader.ets
?? scripts/css_expansion_assertions.mjs
?? scripts/curriculum/css_expansion.py
?? scripts/curriculum/html_expansion.py
?? scripts/curriculum/js_expansion.py
?? test/startup_test.dart
?? test/web_css_tools_test.dart
?? test/web_markup_inspector_test.dart
?? test/zz_debug_test.dart
```
