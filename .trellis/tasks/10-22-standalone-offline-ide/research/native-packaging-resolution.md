# Native QuickJS web-syntax packaging — resolution pass (2026-10-22, third pass)

Read-only verification of the items root reported as fixed since the second pass. **No source
was modified, no build and no Flutter command was run.** Every claim below was re-derived from
the current working tree; where a claim was checkable against artifacts, I recomputed the hash,
the ELF header, the export set, or the count myself rather than trusting the recorded report.

Supersedes the "stale artifacts" section of `native-packaging-review.md` §2 and the B1/B3/M1
findings of `native-packaging-recheck.md`. Findings not listed as resolved here remain open.

## 1. Resolved

### B1 — resolved: analysis is now constructed and consumed

The controller has a call site and a consumer:

```
core\editor\editor_page.dart:113   late final EditorAnalysisController _analysis;
core\editor\editor_page.dart:202   _analysis = EditorAnalysisController(
core\editor\editor_page.dart:203     editor: _editor,
core\editor\editor_page.dart:204     analyzer: StudioProfile.current?.codeAnalyzer,
core\editor\editor_page.dart:205   );
core\editor\editor_problems_bar.dart:22  final EditorAnalysisController analysis;
```

`editor_page.dart:2370-2371` passes `_analysis` into `EditorProblemsBar`, and
`editor_problems_bar.dart:6` renders status from `analysis.pending`. The chain
`webProfile.codeAnalyzer` → `StudioProfile.current` → `EditorAnalysisController` → Problems bar
is complete, so the QuickJS backend is now user-reachable through the editor's Problems panel.

This retires the second pass's central caveat: the parser is no longer dormant infrastructure.

**What that rests on, and what it does not.** Two separate kinds of evidence are involved and
they should not be conflated:

- *Structural evidence (verified by me, this pass).* The call site, the profile field, and the
  consumer exist at the lines quoted above. I read those statements in the current tree. This
  establishes the chain is **wired**.
- *Assertion content (read by me, executed by nobody in this review).*
  `test/web_editor_analysis_test.dart:23` is written to drive the full path and assert the
  outcome rather than the configuration: a saved-clean state (`:31-32`), then an invalid
  unsaved buffer expected to yield exactly one problem whose `source` starts with `QuickJS`
  and whose `code` is `SyntaxError` (`:42-50`), with `startOffset`/`endOffset` on the offending
  token (`:47-48`); plus squiggle decoration (`:59-60`), the Problems panel opening from the
  status tap (`:69-72`), `navigate()` landing on the right line and column (`:88-91`), and the
  on-disk file being left unmodified (`:52`). **I read these assertions; I did not run them.**
  I ran no `flutter test`, no build and no browser command in this pass, so I am not a witness
  to their passing.
- *Execution evidence (root's, pending in a final log).* Root reports having run the two
  actual-QuickJS tests at 2/2, and reports the wider suites green. That is root's execution
  result, attributed as such. It is not mine, and the final log is still to be supplied.

So the correct statement is: B1 is **resolved on wiring (verified) and has an assertion set
written to cover the behaviour (author-reviewed, not run by me)**, with the execution result
resting on root's report and the forthcoming log. The prior wording — "test-backed rather than
merely wired" and "closes B1 on behaviour" — overstated the strength of what a read-only pass
can establish. B1 is **not** downgraded: the wiring is real and independently confirmed; only
the *degree of proof* is restated to match the evidence available to this review.

### B3 — resolved, and cleaner than proposed

`lib/services/web_javascript_syntax_native.dart` now branches before building candidate paths:

```dart
if (Platform.isIOS) {
  return DynamicLibrary.process().lookupFunction<...>('qfli_web_syntax_check');
}
...
: Platform.isLinux
? [ p.join(executableDirectory, 'lib', 'libqfli_web_syntax.so'),
    'libqfli_web_syntax.so' ]
// Android/OHOS resolve packaged libraries through their native linker
// namespace; the executable's directory is not the app library root.
: ['libqfli_web_syntax.so'];
```

All three sub-findings are closed:

- iOS goes straight to `DynamicLibrary.process()` with no wasted file probes — correct for the
  `-force_load` static archive, and better than probing then falling back.
- Linux keeps exactly the exe-relative `lib/` candidate plus the soname, matching
  `install(TARGETS qfli_web_syntax LIBRARY DESTINATION <bundle>/lib)`.
- Android/OHOS use only the bare soname, and the dead
  `executableDirectory/lib/libqfli_web_syntax.so` candidate I flagged is gone. The comment now
  records *why*, so the next reader will not "restore" it.

### M1 — resolved (confirmed again): symbol retained on Apple

`ios/Flutter/WebSyntax.xcconfig` is unchanged from the second pass and still carries both
halves of the retention guarantee:

```
OTHER_LDFLAGS = $(inherited) -force_load "$(BUILT_PRODUCTS_DIR)/qfli-web-syntax/libqfli_web_syntax.a" -Wl,-u,_qfli_web_syntax_check
```

`-force_load` includes every archive member; `-Wl,-u,_qfli_web_syntax_check` makes the symbol a
required reference and therefore a GC root under `DEAD_CODE_STRIPPING = YES`.

### B2 — resolved: a real preflight replaces the bare `FATAL_ERROR`

`scripts/build_web_syntax.py:26-57` now defines `compiler_preflight(cc, platform, flags, sdk)`,
called at `:122` before any compilation. It does three things, all offline:

1. `--version` and `-dumpmachine` on the actual compiler with the actual flags
   (`:29-30`), failing with a diagnostic if the compiler cannot be identified (`:32`).
2. A Windows target gate (`:33-38`): rejects anything whose triple is not MinGW / windows-gnu,
   and the message names the remedy — `--sdk <MinGW-root>`, `--link-cc <MinGW-gcc>`, or a
   GNU-target Clang. It also states that the backend cannot be omitted, which matches root's
   decision to refuse silent skipping.
3. A real compile probe (`:39-57`): a translation unit that includes `<stdint.h>` and
   `<sys/time.h>`, then `#error`s unless the compiler is Clang or GCC >= 9, compiled with
   `-fsyntax-only`. This proves both the version floor *and* that headers actually resolve,
   which is stronger than the version-string check I suggested — a clang with an MSVC default
   target and no sysroot fails here at probe time rather than at link time.

The returned version string is recorded as `metadata["compilerVersion"]` (`:149`), so the
provenance values that used to be merely logged are now gated. `compiler_preflight` also
rejects the old-GCC case that motivated root's objection: the documented failure was GCC 4.9.2
producing a DLL that crashed in `JS_DupAtom` on valid imports
(`.trellis/spec/backend/web-code-analysis.md:71-73`), and the probe's `#error` blocks it
before that can ship.

Residual, minor, and by design: the probe uses `-fsyntax-only`, so it validates compilation,
not linking. A MinGW-compile/`link.exe`-link mismatch still surfaces at the link step (`:147`)
rather than in preflight — which is what `--link-cc` exists for. Not a defect; worth knowing
when diagnosing a Windows failure.

## 2. OHOS packaging — previously unproven, now proven

The second pass could only say "plausible but unverified" because the build artifacts
predated the CMake change. That is no longer the situation:

```
ohos/entry/src/main/cpp/CMakeLists.txt          2026-10-22 12:48:05
ohos/entry/.cxx/.../arm64-v8a/CMakeCache.txt    2026-10-22 13:39:42   <- now newer than the change
```

The `.so` is present at every stage of the packaging chain, both ABIs:

```
ohos/entry/build/default/intermediates/cmake/default/obj/{arm64-v8a,x86_64}/libqfli_web_syntax.so
ohos/entry/build/default/intermediates/libs/default/{arm64-v8a,x86_64}/libqfli_web_syntax.so
ohos/entry/build/default/intermediates/stripped_native_libs/default/{arm64-v8a,x86_64}/libqfli_web_syntax.so
```

This confirms the prediction in `native-packaging-review.md` §2: hvigor copies the whole
`obj/<abi>` directory, so a second project `.so` ships without any `nativeLib` declaration.

**The stale "artifacts predate the change" status is withdrawn.** Current evidence:

| Check | Result | How I verified |
| --- | --- | --- |
| HAP exists | `entry-default-unsigned.hap`, 48,492,468 bytes, 2026-10-22 13:56:17 | `Get-Item` |
| HAP sha256 matches report | `356370bf…1176` | `Get-FileHash -Algorithm SHA256` |
| Both ABIs contain the bridge | `libs/arm64-v8a/` and `libs/x86_64/` | HAP central directory |
| ELF class/type | 64-bit little-endian, `ET_DYN` | `e_ident`, `e_type` |
| Machine | arm64 = 183 (`EM_AARCH64`), x86_64 = 62 (`EM_X86_64`) | `e_machine` at offset 18 |
| No entry point | `e_entry == 0` | offset 24 |
| 16 KiB page alignment | 4 `PT_LOAD` segments, all `p_align == 16384`, both ABIs | program headers |
| Exports | `qfli_web_syntax_check`, `qfli_web_syntax_version` in both ABIs | symbol table |
| Byte sizes match report | stripped 947,808 / 1,056,384 | `Get-Item` on `stripped_native_libs` |
| QuickJS license shipped | `resources/rawfile/flutter_assets/vendor/quickjs/LICENSE` (1,130 B) | HAP central directory |

Every value in `research/hap-481-inspection.json` reproduced exactly. The `loadAlignment`
array being 16,384 across all four segments in both ABIs is the substantive result: it is what
makes the library loadable on 16 KiB-page OHOS kernels, and it is now measured on the shipped
artifact rather than assumed from the link flag.

### The inspection is reproducible, not a one-off transcript

`research/audit_hap.py` regenerates the report from the HAP itself and asserts the properties
instead of describing them: ELF magic and class (`:27`), machine per ABI (`:28`), zero entry
(`:29`), every `PT_LOAD` alignment `>= 16384` (`:37-40`), and — the strongest check — the
export set must be **exactly** `{qfli_web_syntax_check, qfli_web_syntax_version}` once the
optional CRT `_init`/`_fini` are removed (`:47-48`). An exact-set equality catches accidental
extra exports that a substring test would miss, which matters given
`C_VISIBILITY_PRESET hidden` is the mechanism protecting the ABI surface. It also asserts the
QuickJS license is packaged (`:53`) and re-derives the expected catalogs from
`prepare_ohos_catalog.staged_files(ROOT)` rather than hard-coding hashes, so a drifted catalog
fails the audit.

## 3. Catalog and test-separation claims

Verified independently:

- Both catalogs parse to **exactly 481** entries (`entries` array, not top-level keys):
  `examples.entries = 481`, `tutorials.entries = 481`, `product = webforge` for both.
- 481/481 unique ids within each set, **0** overlapping ids across sets — the two catalogs are
  disjoint, so "481 examples + 481 tutorials" is 962 distinct items, not a duplicated set.
- HAP catalog bytes (796,590 / 1,389,546) match the on-disk JSON sizes exactly.
- Test separation holds: production ships catalogs at
  `resources/rawfile/flutter_assets/assets/content/`, the ohosTest HAP ships them at
  `resources/rawfile/ohos_catalog/`. Different paths, identical hashes — the test bundle has its
  own copy and cannot silently shadow the production path.
- The browser-run catalogs hash-identically to the HAP-packaged catalogs
  (`2d8f8c0a…eeb1c` / `10e750b7…acb36` in all three places: `browser-481-*.json`,
  `hap-481-inspection.json`, and the files on disk). The 3,986/3,985 assertions were therefore
  executed against exactly the content that ships, which is the cross-check that makes those
  numbers meaningful rather than merely green.

### Recorded test counts, and the 1-check delta explained

These figures are read from root's run artifacts; this pass executed nothing:

```
browser-481-desktop.json : passed=481 failed=0 totalChecks=3986 mappingIssues=[] viewport=1280x720
browser-481-mobile.json  : passed=481 failed=0 totalChecks=3985 mappingIssues=[] viewport=390x844
```

I diffed per-case `checks` between the two runs: exactly **one** case differs,
`css-example-044` (desktop 11, mobile 10), and it is correct behaviour rather than a coverage
gap. At 1280 px the article is 609.875 px wide inside 1232 px, so the desktop run asserts
"centred with equal side margins" (311.062/311.062) and "horizontally centred on the page"
(640). At 390 px the article clamps to 342 px, and those two assertions are replaced by one
mobile-appropriate assertion, "at a narrow width the article fills the available width"
(342 vs 342). Same `codeSha256` (`e7c2292b…fd0c`) in both runs. Net −1 check, all passing.

## 4. Backend documentation

`.trellis/spec/backend/web-code-analysis.md` records the prerequisites root promised, and
records them with the reasoning rather than just the rule:

- `:71-75` — GCC 9+ or Clang required; the installed GCC 4.9.2 produced a DLL that crashed on
  valid imports in `JS_DupAtom`; Windows Clang must target GNU/MinGW, and a default MSVC target
  needs `--sdk <MinGW-root>` (plus optional `--link-cc`) or an explicitly GNU-target Clang.
- `:39-43` — the build and test invocations, including
  `python native/web_syntax/test_native.py ABSOLUTE_NATIVE_LIBRARY`.
- `:46-49` — CMake target shape: shared by default, static with `-DQFLI_WEB_SYNTAX_STATIC=ON`,
  Windows `QFLI_SYNTAX_CC`, and `QFLI_WEB_SYNTAX_LIBRARY` for pointing at a real bridge.
- `:108-112` — per-platform delivery table, including OHOS "package
  `libqfli_web_syntax.so` in both HAP ABI directories", which §2 above now verifies as fact.
- `:128` — the degradation contract: "Native library absent → QuickJS unavailable;
  independently checked HTML/CSS errors may remain". That is the honest-labelling behaviour the
  feature needs, and it matches what the loader does.

## 5. Still open — genuine gaps, not paperwork

> M2 is **not** in this list: it was re-assessed this pass and closed as working-as-designed.
> See §5a.

These are runtime/Apple/signing matters that no amount of archive inspection settles, and I
did not attempt to close them:

- **macOS / iOS runtime load unobserved.** `-force_load` + `-u` is correct by construction and
  the phase ordering was verified in the first pass, but no Apple build or launch was run. The
  symbol being present in the link is not the same as `DynamicLibrary.process()` finding it at
  runtime on a signed, hardened-runtime build.
- **macOS codesigning of the injected dylib.** `bundle_web_syntax_apple.sh` installs into
  `Contents/Frameworks` and signs with `--timestamp --options runtime` for a real identity,
  ad-hoc for `-`. Whether a Developer ID + notarization pass accepts the nested dylib is
  untested here.
- **Android/OHOS `dlopen` by bare soname on hardware.** The loader now intentionally relies on
  the linker namespace for both platforms (`:65-67`). The OHOS `.so` demonstrably ships and is
  correctly aligned, but no device run confirmed the symbol resolves.
- **M2 — assessed and withdrawn as a defect; it is a deliberate fail-closed platform guard.**
  Detail in §5a below. Not an actionable risk under the current build contract.
- **M3/M4/M5/M6/M7/M8 — unchanged.** Device/simulator output co-location still depends on
  per-platform `BUILT_PRODUCTS_DIR`; Windows still shares one DLL across configurations
  (`windows/CMakeLists.txt:72`); embedded NUL is still untested though unreachable from Dart;
  `error_offsets()` still assumes well-formed UTF-8; per-call `JSRuntime` creation is now
  driven by the controller's 300 ms debounce and is fine as designed; the hash manifest scope
  is unchanged.
- **Signed installation not verified.** The inspected HAP is `entry-default-unsigned.hap`, and
  `audit_hap.py` records `signedInstallation: "not verified by archive inspection"` rather than
  claiming otherwise. Correctly honest.
- **Dual-Flutter ABI rebuild** is still to follow the shared-sliver and widget acceptance work;
  the HAP inspected here is the current single-ABI-pair artifact, so those numbers should be
  re-taken after that rebuild rather than assumed to carry over.

## 5a. M2 — `vtool` guard: closed as working-as-designed

The earlier passes listed the `vtool -show-build` assertion as "brittle". On re-reading it
against the build contract, that framing was wrong and is withdrawn. It is a **fail-closed
platform guard doing exactly what it should**.

**Why the guard exists.** `lipo -verify_arch` checks only the architecture. On Apple Silicon an
iPhone device archive and an iPhone simulator archive are both `arm64`, so architecture alone
cannot tell them apart — mixing them produces a library that links cleanly and then fails at
load time. The script therefore extracts each member and asserts its `LC_BUILD_VERSION`
platform matches the target (`IOS` / `IOSSIMULATOR` / `MACOS`). That is a real hazard, not a
hypothetical one.

**Why failing hard is correct here.** The awk check at `:34-37` requires `seen > 0` **and**
every platform line to match. So a missing load command, an unreadable member, or an empty
extraction all abort the build. Under this project's stated contract — a shipping diagnostics
feature must be reproducible, and a missing compiler or malformed archive must fail the build
rather than silently ship a dead feature — aborting is the intended behaviour, and it is the
same trade already accepted for the Windows preflight. A guard that warned and continued would
be the actual defect.

**Why it is not a novel risk.** The identical pattern already ships in
`scripts/bundle_nginx_ios.sh:15-28` — same `mktemp -d` / `ar -x` / `vtool -show-build` /
awk-verify sequence, in the completed embedded-nginx iOS delivery. The syntax bridge copies an
already-exercised mechanism rather than introducing an untested one. Both scripts also pass an
explicit `-target <arch>-apple-ios13.0[-simulator]` (`build_web_syntax.py:112-113`), which is
what makes clang emit `LC_BUILD_VERSION` into the objects in the first place.

**Only actionable residual (low, UX not correctness).** When the guard trips, the failure is an
opaque `xcrun vtool` error or an awk non-zero exit, so the operator sees "Command PhaseScriptExecution
failed" rather than "this object is MACOS, expected IOSSIMULATOR". Two cheap improvements,
neither required: keep `platform.txt` on failure for inspection, and echo the expected-vs-seen
platform before exiting. This is a diagnostics nicety on an already-correct gate — not a bug,
and not worth a change on its own.

**Verdict:** M2 closed as *working as designed*. No code change recommended.

## 6. Verdict on the reviewed findings

| Finding | State |
| --- | --- |
| B1 analyzer unreachable | **Resolved** — wiring verified at `editor_page.dart:202` / `:2370`; behavioural coverage written in `test/web_editor_analysis_test.dart` and read by me, execution result pending root's final log |
| B2 Windows `FATAL_ERROR` / no preflight | **Resolved** — `compiler_preflight` at `build_web_syntax.py:26`, called at `:122` |
| B3 dead FFI path on Android/OHOS | **Resolved** — iOS process-upfront, Linux exe+lib, mobile bare soname |
| OHOS packaging unproven | **Resolved** — both ABIs in the HAP, ELF/16 KiB/exports verified, hash reproduced |
| M1 Apple symbol retention | **Resolved** — `-force_load` + `-Wl,-u` |
| M2 `vtool` brittleness | **Closed as designed** — deliberate fail-closed platform guard; same pattern already ships in `bundle_nginx_ios.sh:15-28`. No change recommended |
| M3/M4/M5/M6/M7/M8 | Open, all minor (unchanged) |
| Apple/macOS runtime + signing | Open — genuinely unverified |
| Android/OHOS on-device `dlopen` | Open — genuinely unverified |
| Signed HAP installation | Open — artifact inspected is unsigned |

No source was modified in producing this pass; the only writes were research documents under
`.trellis/tasks/10-22-standalone-offline-ide/research/`.

## 7. Proof standard used for this pass

Because this review is read-only, three evidence classes are kept distinct throughout:

1. **Verified by me** — facts I recomputed from artifacts: HAP sha256, ELF `e_machine`, `PT_LOAD`
   alignments, export set, stripped byte sizes, catalog counts and cross-hashes, file line
   numbers, and the freshness of build caches. These are stated without hedging.
2. **Read by me, executed by nobody here** — the content of `test/web_editor_analysis_test.dart`
   and of `audit_hap.py`. I can confirm an assertion is *written* to check something; I cannot
   confirm it *passes*. Stated as "written to assert".
3. **Reported by root, log pending** — test suite results (the two actual-QuickJS tests at 2/2,
   desktop 3,986 / mobile 3,985, 481 catalogs), and the dual-Flutter ABIs rebuild. Attributed
   to root and not treated as my finding until the final log lands.

The earlier two passes did not maintain this distinction cleanly for B1. The correction is in
§1: the wiring is verified, the assertion set is author-reviewed, and the pass result is root's
to evidence.

## 8. Current evidence boundaries (2026-10-22, fourth pass)

Log paths are relative to `.trellis/tasks/10-22-standalone-offline-ide/research/`.

### 8.1 Host-side suites — recorded, not re-run here

| Evidence | Path | Value |
| --- | --- | --- |
| Flutter suite | `integration-tests-final.log` | `+172: All tests passed!` (tail) |
| Dart analyze | `integration-analyze-final.log` | 98 bytes, clean |
| Desktop catalog run | `browser-481-desktop.json` | 481 passed / 0 failed / 3,986 checks |
| Mobile catalog run | `browser-481-mobile.{json,md,log}` | 481 passed / 0 failed / 3,985 checks |

### 8.2 Actual native ArkWeb run — this is the only device evidence

| Evidence | Path | Value |
| --- | --- | --- |
| Semantic run | `ohos-481-initial.json` / `.md` / `.runner.log` | 481 cases, **443 pass / 38 fail**, 3,985 checks |
| Device identity | `ohos-481-initial.device.json` | `ohos-arkweb`, x86_64 emulator, `unsigned-emulator`, ArkWeb 144.0.7559.59 |
| Driver | `ohos-481-initial-driver.log` | `OHOS catalog verification failed` (exit non-zero) |
| Artifact under test | `ohos-481-initial.device.json` → `artifacts.production` | `entry-default-unsigned.hap`, 80,682,576 B, sha256 `7b16610e9efe667eb3c838a204fab1c53441f8d17e4e997c0a13325a455cd346` |

The HAP digest matches the reported dual-Flutter-ABI archive (`7b16610e…`, 80,682,576 B), so the
443/38 numbers describe the same artifact the build produced. `audit_hap.py`'s structural
assertions and the ArkWeb semantic run are different gates and both matter: the former proves
the archive is well-formed and the parser ships, the latter proves the *content* behaves.

### 8.3 What these boundaries do not cover

- 38 ArkWeb failures are **real device behaviour**, not flake: 34 CSS (owned elsewhere),
  2 HTML (`html-example-135`, `html-example-144`), 2 JS (`js-example-052`, `js-example-095`).
- The host 481/481 result and the ArkWeb 443/481 result are not contradictory: the emulator
  lacks geolocation, reports `navigator.onLine === false`, scales computed lengths, and has a
  different layout viewport. Host green does **not** imply device green, which is exactly what
  this run demonstrates.
- Signed installation remains unverified (`signedInstallation: "not verified by archive
  inspection"`; the run used `unsigned-emulator`).
- macOS/iOS runtime load and signing remain unverified at runtime (§5).

## 9. Review of the HTML/JS ArkWeb fixes — one critical finding

Scope: `html-example-135`, `html-example-144`, `js-example-052`, `js-example-095`. The 34 CSS
failures are owned by another reviewer and were not assessed.

### 9.1 CRITICAL — the fixes are generator-side only; every packaged catalog is stale

All four fixes landed in the **generators** and the **assertions**, but the emitted catalogs
were never regenerated. Timestamps:

```
scripts/curriculum/html_expansion.py          2026-10-22 19:48:43
scripts/curriculum/js_data4.py                2026-10-22 19:48:18
scripts/curriculum/js_data5.py                2026-10-22 19:48:32
scripts/html_expansion_assertions.mjs         2026-10-22 19:48:54
scripts/js_example_assertions.mjs             2026-10-22 19:49:38
assets/content/examples.json                  2026-10-22 13:48:34   <- 6h stale
assets/content/tutorials.json                 2026-10-22 13:48:34   <- 6h stale
ohos/entry/src/main/resources/rawfile/.../examples.json        2026-10-22 13:48:34   <- stale
ohos/entry/src/ohosTest/resources/rawfile/ohos_catalog/examples.json  2026-10-22 13:48:34   <- stale
```

All four copies still hash to `2d8f8c0aa321f3e861af5f46cd0a9b2b1430010b513d3c3eea106c0eca2eeb1c`,
which is byte-identical to the `examples.json` recorded inside the HAP the emulator ran. So the
443/38 measurement, and the HAP itself, both predate every fix in this set.

Concrete consequences, verified against the shipped code:

- **`js-example-052`** — the packaged example has **no watchdog** (`TIMEOUT_MS` absent, no
  `setTimeout`, no `timeout` option) and never renders `定位中`. The repaired generator
  (`scripts/curriculum/js_data4.py:83`) does emit an 800 ms watchdog with `定位中` / `定位超时`.
- **`html-example-135`** — the packaged example **lacks `<meta name="viewport">`**, which the
  repaired generator adds. Without it the layout viewport defaults to 980 px, so `matchMedia`
  reports `wide:true` while the device is narrow — precisely the `{expectedWidth:300,
  width:200, wide:true}` signature in the failure record.
- **`js-example-095`** — the packaged example logs `console.log(navigator.onLine)` (the bare
  `false` seen in the failure console); the repaired generator logs `'online=' + navigator.onLine`.

**Actionable risk:** repackaging **without** re-running `scripts/emit_content.py` would ship the
old code again and reproduce the same 38 failures, while *appearing* to include the fixes.
The regeneration step is a hard prerequisite for the next HAP, not a follow-up.

### 9.2 CRITICAL — the new `js-052` assertions pass on host for the wrong reason

`scripts/js_example_assertions.mjs` now accepts `定位超时` as a documented terminal state, and
that state is reachable **only** from the repaired generator. Run against the *currently
packaged* (stale) example on a host browser, geolocation fails immediately with
`定位失败：<message>`, which satisfies `/^定位失败：.+$/` and `not stuck in progress` — so the case
goes green without exercising the watchdog at all.

This makes "host-verified" non-transferable for `js-052`: host Chromium always answers (success
or error), whereas the device failure mode is *no callback ever*. The new assertions are
correctly written, but they cannot distinguish "watchdog works" from "host happened to error",
and they will fail on device until the regenerated catalog ships. Recommended: assert the
`定位中` intermediate state is observed **before** the terminal state on at least one path, so
the watchdog is provably the thing that settled the UI.

### 9.3 Minor but real — `html-example-135`'s probe check became self-referential

The third check changed from cross-validating against the media-query expectation to comparing
the page's own report with the runner's own read of the same DOM property:

```js
// before: cross-check against the expected width for this viewport
probe.includes(`实际宽=${crop.expectedWidth}`)
// after: compare the page's naturalWidth report with the runner's naturalWidth read
probe.includes(`实际宽=${crop.width}`)   // crop.width === img.naturalWidth
```

Both sides now derive from `img.naturalWidth`, so this specific check can no longer detect an
incorrect `<picture>` selection. It is not a coverage hole in aggregate — the unchanged checks
`crop matches actual viewport media query` (`crop.width === crop.expectedWidth`) and
`currentSrc is the matching candidate` still perform the real cross-validation, and both remain
in the case. But the probe check is now tautological and should not be cited as evidence that
selection is correct.

### 9.4 Accepted as correct — no weakening, no offline violation

- **`html-example-144`** — replacing `=== '1px'` with exact parity against a page-level `1px`
  control measured in the same engine is *stronger*, not weaker: it removes a platform-scaled
  literal (ArkWeb reports `0.857143px`) while staying exact, and it adds `solid` style, padding
  and `display:block` checks. The `:host` declaration is still proven to be applied, because a
  UA default border would have `border-style: none`.
- **`js-example-095`** — deriving the expected label from live `navigator.onLine` instead of
  hardcoding `在线` is the correct fix for an offline emulator and is **not** a tautology: the
  check still fails if the page renders a stale label, and the forced `offline`/`online`
  `dispatchEvent` calls additionally prove both listeners repaint. No network access is required
  or performed, so there is no offline violation.
- **`js-example-052` generator code** — the 800 ms watchdog, `settled` guard, `err.code === 1`
  branch and `{timeout, maximumAge}` option are a genuine root-cause fix for a callback that may
  never arrive. Correct once emitted.
- **No offline violation anywhere in this set.** The repaired `html-example-135` still uses only
  inline `data:` `srcset` values; `js-095` reads `navigator.onLine` without making requests;
  `js-052` touches geolocation only. No new external URLs were introduced.

## 10. `vendor/quickjs/.gitattributes` — verified correct

```gitattributes
# These retained upstream inputs are verified byte-for-byte by SHA-256.
* -text
```

Verified independently:

- `git check-attr text` reports `unset` for every pinned path, so no CRLF translation or filter
  runs on checkout — which is what protects the SHA-256 pins on a Windows worktree.
- For all 17 `buildInputSha256` entries, the **index blob id equals `git hash-object` of the
  worktree file**, i.e. no EOL or filter divergence between what is committed and what is on
  disk. `git status` reports `vendor/quickjs` clean.
- All 17 files' SHA-256 match `SOURCE.json`; `quickjs-2026-06-04.tar.xz` matches its pinned
  `b376e839…ad2a`.
- The count is **18 pinned digests** = 17 in `SOURCE.json.buildInputSha256` + the tarball, which
  is also the line count of `vendor/quickjs/HASHES.sha256`. The two manifests agree.
- Retaining upstream whitespace is correct: these are third-party byte-exact inputs whose
  digests are checked by `build_web_syntax.py` before every compile (`:74-80`, which now also
  verifies the upstream tarball against `archiveSha256` at `:74-75` before checking each
  extracted input), so normalising whitespace would either break the build or silently change
  what is compiled. `-text` is the right and minimal mechanism.

