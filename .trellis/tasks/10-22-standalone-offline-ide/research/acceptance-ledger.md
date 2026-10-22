# Acceptance ledger — 2026-10-22

This is an evidence ledger, not a completion declaration. Preserve the complete source request. All gates start open and need actual current-artifact proof.

| Requirement | Owner | Current evidence | State |
| --- | --- | --- | --- |
| R1 Trellis/commit/push | Web root, each product coordinator | Parent artifacts active; feature branch `feat/offline-web-ide`; original WIP preserved; explicit-path commits/push pending | In progress |
| R2 all OHOS examples/tutorial code | Each product coordinator | Web host baseline301/301 and expanded481/481 pass; current HAPs compile; Java has exclusive live HarmonyOS7 API26 emulator window, Web next | Open: native exhaustive execution |
| R3 >100 newly authored examples | Each product coordinator; Web +180 | Web481 unique matched topics:160HTML/160CSS/161JS, including180 new; desktop3986/mobile3985 semantic assertions, mapping0 | Web host complete; native/all-products open |
| R4 filters/title circles | C common-core coordinator | Real481 UI check found core prioritizes executable `type: html` over HTML/CSS/JS subject; correction requested in channel108 | Open: confirmed core defect |
| R5 direct useful language Tools | Each product coordinator | Web controls inline with bounded async resource inspection, CSS/markup tools;70 affected tests passed in earlier165 suite;16 browser formatter assertions; public ToolsGridSliver now consumed | Web implemented; final regression and all-products pending |
| R6 inline syntax diagnostics | C common-core coordinator + product adapters | Real HTML/csslib/compile-only QuickJS adapter wired;19 service cases passed; actual EditorPage tests fail at both sizes when 3 lines become 2 due to synchronous decoration repaint | Open: confirmed core defect, 0/2 new UI cases |
| R7 retained tree/multi-root | C common-core coordinator | Existing dirty explorer/history changes; verify after handoff | Open |
| R8 feasible debug/panels/logs | C common-core coordinator + native product owners | Web request/console streams exist; no new acceptance evidence | Open |
| R9 highlights/headers/Python modules | C common-core and Python coordinators | Scope confirmed in global channel; need fresh evidence | Open |
| R10 offline independent products | Each coordinator | Web481 desktop/mobile run blocks external requests; all165 app tests pass including offline surface gates; native harness is test-only | Web host verified; native/all-products open |

| Product | Coordinator / evidence task | Current acceptance |
| --- | --- | --- |
| C/C++ | C w1R:p1; common-core sole integrator | Current native/WASI host200/200 reported; phone and expanded catalog pending |
| Dart | .trellis/tasks/10-22-offline-ide-completeness in qfli_dart | App116 tests/commit b90f4b9 reported; shipped portable43/120 pairs remains open; alternate host candidate is not production proof |
| Go | .trellis/tasks/10-22-standalone-ide-completeness in qfli_go | Host baseline 120/120 reported; OHOS pending |
| Java | Java w28:p1 | Expanded280 topics authored/hostJDK17 verification active; native target127.0.0.1:5555 is exclusive Java window; main/test signing and actual target evidence pending |
| JSON | JSON w29:p1 | Pending current handoff |
| Lua | .trellis/tasks/10-22-offline-ide-completeness in qfli_lua | Pending |
| Markdown | .trellis/tasks/10-22-offline-note-completeness in qfli_note | Pending |
| Python | .trellis/tasks/10-22-offline-language-apps in qfli_python | ActualMicroPython1.24.1 host116/120 examples;117–120 incompatible imports and tutorial008 fixture loss reported; fixture core repair under review |
| Rust | Rust w2B:p1 | Pending current handoff |
| SQL | SQL w2C:p1 | Pending current handoff |
| Web | This task | Baseline301/301; expanded481/481 desktop/mobile;165 tests+analysis pass; unsigned exact-content HAPs and native dual-ABI parser inspected; final dualFlutterABI build, signing and actualArkWeb execution pending |

## Evidence boundaries

- Full current host reports: `browser-481-desktop.{md,json}` and
  `browser-481-mobile.{md,json}`. Both cover481 examples and481 tutorial mappings,
  not a filtered prefix. Catalog schema audit has0 issues and481 distinct bodies.
- Earlier app165 tests include analyzer19 and tools70. Original86-test baseline
  was independently saved before changes. Two later actual EditorPage tests
  reproduce a line-shrink repaint crash; the earlier165 result does not establish
  a current green suite. See `core-acceptance-defects.md` and
  `web-editor-analysis.md`; final catalog UI tests are also pending.
- `hap-481-inspection.json` proves current source/staging/main/test catalog byte
  equality, bundle identities, test-source separation, MIT license and both
  native parserABIs with16KiB LOAD alignment. Current archives are unsigned.
  A later source change or dualFlutterABI rebuild must refresh this report.
- Flutter's installed `build hap` default includes only `ohos-arm64` even when
  native `abiFilters` listsx86_64. Emulator main acceptance must explicitly build
  `--target-platform ohos-arm64,ohos-x64` and inspect bothlibapp/libflutter pairs.
- Java owns the live emulator until explicit release; Web has performed no
  install, native launch or forwarding. Host/cross-build/unsigned packaging
  evidence does not satisfy the user's OHOS execution requirement.
- Shared core and other products remain coordinator-owned. No other product's
  acceptance is inferred from Web results. R1–R10 remain open where marked.
