# Native QuickJS web-syntax packaging — follow-up re-check (2026-10-22, second pass)

> **Superseded by `native-packaging-resolution.md` (third pass).** Everything this pass listed
> as open has since been closed and verified: B1 (analyzer now constructed at
> `editor_page.dart:202` and consumed at `:2370`), B2 (`compiler_preflight` now exists at
> `build_web_syntax.py:26`), B3 (loader paths rewritten), and OHOS packaging (both ABIs present
> in an inspected HAP, ELF/16 KiB/exports re-verified). Read this file for the historical
> reasoning only; use the resolution document for current status.

Read-only verification of the three items root reported as addressed, plus the status of
every finding still open from `native-packaging-review.md`. **No source was modified, no
build was run.** Line numbers are from the current working tree.

> **Scope caution.** Several findings below concern code that is *in flight and not yet
> integrated end to end*. Nothing here should be read as a final delivery verdict on the
> JavaScript diagnostics feature. In particular B1 is a statement about the *current
> wiring state at this commit*, not a claim that the feature cannot ship.

## Status of root's three claims

| Claim | Verdict | Evidence |
| --- | --- | --- |
| B1: `WebCodeAnalyzer` wired into `webProfile.codeAnalyzer`, profile test added | **Partially addressed — pipeline still not wired** | `lib/main.dart:38` sets it; `test/web_app_test.dart:61` asserts `isNotNull`; but nothing constructs `EditorAnalysisController`, so no diagnostics reach a surface. |
| iOS `-u` symbol added | **Addressed** | `ios/Flutter/WebSyntax.xcconfig` now appends `-Wl,-u,_qfli_web_syntax_check`. |
| B2: silent-skip rejected; will declare compiler prerequisite and pre-check clang GNU target/sysroot | **Accepted as design decision; not yet implemented** | `windows/CMakeLists.txt:57-61` and `scripts/build_web_syntax.py:80-84` are unchanged from the reviewed state; no pre-check exists yet. |

### B1 detail — from "not injected" to "injected but unconsumed"

`lib/main.dart:38`:

```dart
  codeAnalyzer: WebCodeAnalyzer(),
```

`lib/main.dart:18` imports `services/web_code_analyzer.dart`, and `WebCodeAnalyzer` implements
`CodeAnalyzer` from core (`lib/services/web_code_analyzer.dart:15`). The value flows into
`StudioProfile.codeAnalyzer` (`core/lib/services/studio_profile.dart:99,135`).

The consumer, however, is never instantiated:

```
$ Get-ChildItem <core>\lib -Recurse -Filter *.dart |
    Select-String -Pattern "EditorAnalysisController"
core\editor\editor_analysis_controller.dart:14: class EditorAnalysisController extends ChangeNotifier {
core\editor\editor_analysis_controller.dart:15:   EditorAnalysisController({required this.editor, required this.analyzer,
```

Two references, both the declaration. No import of `editor_analysis_controller.dart` exists
anywhere in `core/lib` or `lib/`, so `analyzer` never reaches `_run()` and
`file.diagnostics` is never populated. The class is fully built — debounce
(`duration: 300ms`), a watchdog, a generation counter, `maxDiagnostics = 1000`, and
`unavailableReason` for `analyzer == null` (`editor_analysis_controller.dart:73-90,109-158`)
— so the remaining work is a constructor call plus a surface for `problems` / `navigate()`.

Encouragingly, the controller already covers the operational risks raised elsewhere in this
review: `unavailableReason` distinguishes "no analyzer installed" from "open an editable
source file" (`:81-82`), a watchdog turns a hung backend into a retryable message instead of a
frozen panel (`:87-92`), and `pending`/generation are reset per request (`:72-73`). That is a
good host for a backend that may legitimately be absent on an unpackaged platform — which is
exactly what `checkJavaScriptSyntax`'s `unavailableReason` contract exists for. The two halves
fit; only the join is missing.

And the new test asserts configuration, not capability:

```dart
// test/web_app_test.dart:61
expect(webProfile.codeAnalyzer, isNotNull);
```

`isNotNull` passes for any `CodeAnalyzer`, including a no-op. It does not prove that a
`.js` buffer produces a diagnostic on any platform, nor that a missing library degrades to
`unavailableReason` rather than to silence. Suggested minimum that would actually cover the
wiring: construct `EditorAnalysisController` against a fake `StudioEditorState` with
`analyzer: webProfile.codeAnalyzer`, feed a `.js` file containing `var = ;`, and assert
`problems` is non-empty — plus the inverse case where the analyzer reports
`unavailableReason` and `problems` stays empty without claiming the file is clean.

**Restated finding (not a defect in anyone's code, a sequencing fact):** the native parser is
packaged for six platforms and injected into the profile, but the controller that turns
analysis results into editor diagnostics has no caller. Until that call site exists, shipping
the DLL/`.so`/`.a` changes no user-visible behaviour. Whether that lands in this release is
root's call — it just should not be described as delivered until it does.

### iOS `-u` detail — addressed, and why it matters

```xcconfig
OTHER_LDFLAGS = $(inherited) -force_load "$(BUILT_PRODUCTS_DIR)/qfli-web-syntax/libqfli_web_syntax.a" -Wl,-u,_qfli_web_syntax_check
```

`-force_load` pulls every archive member; `-u _qfli_web_syntax_check` additionally declares
the symbol as a required undefined reference, which makes it a GC root. That closes the M1
gap for the failure mode that actually mattered (`DEAD_CODE_STRIPPING = YES` under Release).
Note this makes a missing/broken archive a **link-time error** for every iOS build rather than
a silent runtime degradation — which is the correct trade for a shipped feature, and is
consistent with rejecting the silent-skip option on Windows. M1 can be marked resolved; the
belt-and-braces `nm` assertion is now optional rather than necessary.

### B2 detail — decision accepted, implementation still pending

Root's reasoning is sound and I withdraw the "degrade to unavailable" suggestion: a shipped
diagnostics feature must be reproducible, so a missing toolchain should fail the build rather
than silently ship a product where the feature is dead. The 4.9 GCC note is also a good
catch — `native/web_syntax/qfli_web_syntax.c:7-9` hard-errors below GCC 9
(`GCC 4.9 miscompiles module atoms`), so "prefer gcc" would have traded a clean failure for a
miscompile. Retracting that specific recommendation.

What is still open is the *implementation* of the stated plan. As of this tree:

- `windows/CMakeLists.txt:58` still prefers `clang` over `gcc` with no version gate.
- `windows/CMakeLists.txt:60` still emits the generic `FATAL_ERROR`, so a developer with no
  compiler on `PATH` gets a message that does not say what to install.
- `scripts/build_web_syntax.py:80` still gates the GNU target purely on `args.sdk` being
  truthy; nothing inspects the compiler's default target, and nothing validates that the
  supplied sysroot contains usable headers before compiling.
- New since the first review: `build_web_syntax.py:110-114` now records `compilerVersion`,
  `sdk`, and `linkCompiler` into `build.json`. That is good provenance and a natural place to
  hang the pre-check — the same values could be asserted instead of merely logged.

Concrete suggestion for the pre-check, since it is cheap and offline: before compiling,
run `--version` and reject a compiler whose reported target is MSVC-ish when no sysroot was
given (e.g. clang reporting `x86_64-pc-windows-msvc` with `--sdk` empty), and verify the
sysroot actually resolves one MinGW header. Both are single `subprocess` calls in the code
path that already shells out at line 109.

## Findings still open, unchanged from the first pass

Verified unchanged in this tree:

- **B3 — FFI first candidate still never resolves on Android/OHOS.**
  `lib/services/web_javascript_syntax_native.dart:56` still builds
  `p.join(executableDirectory, 'lib', 'libqfli_web_syntax.so')`, which under
  `useLegacyPackaging = true` becomes `.../lib/lib/libqfli_web_syntax.so`. `ArgumentError`
  is swallowed at line 64, so behaviour rests on the bare-name fallback. Unverified on device.
- **OHOS packaging unproven.** `ohos/entry/src/main/cpp/CMakeLists.txt:9-10` added the
  subdirectory and `:17-22` still branches on `OHOS_ARCH`; the file timestamp is
  `2026-10-22 12:48:05` while `ohos/entry/.cxx/.../CMakeCache.txt` remains `2026-10-15
  18:54:55`, and `libqfli_web_syntax.so` appears nowhere under `ohos/entry/build`. Artifacts
  still predate the change. Root's plan to run a real `flutter build hap` + HAP listing on
  the next Flutter slot is the right gate; nothing else can settle it.
- **M2 — `vtool` assertion remains brittle** (`bundle_web_syntax_apple.sh`, unguarded under
  `set -euo pipefail`).
- **M3 — device/simulator output co-location** still relies on per-platform
  `BUILT_PRODUCTS_DIR`; worth a comment, not a bug.
- **M4 — Windows shares one DLL across configurations** (`windows/CMakeLists.txt:72`).
- **M5/M6 — embedded NUL untested; `error_offsets()` assumes well-formed UTF-8.** Both
  unreachable from Dart today; unchanged.
- **M7 — no call-level caching.** Now slightly more relevant: with B1 wired the analyzer will
  be driven by `EditorAnalysisController`'s 300 ms debounce
  (`editor_analysis_controller.dart:16`), which is a comfortable interval for one
  `JSRuntime` per call. Downgrade to "fine as designed, revisit only if the debounce is
  removed".
- **M8 — hash manifest scope** unchanged; `build_web_syntax.py:38-42` still verifies every
  pinned source on each invocation.

## Corrected / retracted from the first pass (kept for audit)

- The `.js` ES-module fallback is correct (`lib/services/web_code_analyzer.dart:186` passes
  `module: true`). Retracted as a false positive.
- Embedded NUL does not truncate the parse: `JS_Eval` receives an explicit `length`
  (`native/web_syntax/qfli_web_syntax.c:109`). Downgraded to a test gap.
- "Prefer gcc over clang on Windows" retracted — GCC 4.9 is rejected by design and would
  miscompile (see B2 detail).

## What this pass did not establish

- No build was executed on any platform; all statements are from source inspection.
- OHOS packaging of `libqfli_web_syntax.so` remains **unverified** pending the real
  `flutter build hap` and HAP content listing.
- `dlopen` success on Android/OHOS hardware remains unobserved.
- Whether root intends `EditorAnalysisController` wiring in this release is unknown; the B1
  note is a wiring-state observation, not a scope ruling.
