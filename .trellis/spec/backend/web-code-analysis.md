# Offline Web Code Analysis

## 1. Scope / Trigger

Read when changing `WebCodeAnalyzer`, JavaScript FFI, parser dependencies,
`native/web_syntax`, retained QuickJS inputs, or native delivery. WebForge owns
the parser adapter; `qfli_studio_core/services/code_analysis.dart` owns the
snapshot/diagnostic contract and shared editor presentation. `webProfile` wires
`codeAnalyzer: WebCodeAnalyzer()`; do not replace the preview runner with it.

Use actual `html`/`csslib` parsers and QuickJS compilation. Capability scans only
recognize known unsupported grammar; they must never invent syntax diagnostics.

## 2. Signatures

```dart
const WebCodeAnalyzer({String? nativeLibraryPath});
Future<CodeAnalysisResult> WebCodeAnalyzer.analyze(CodeAnalysisRequest request);

// Core public request types, all offsets measured against exact String text.
CodeDocumentSnapshot({required String path, required String text,
  required int revision});
CodeAnalysisRequest({required String projectPath, required String activeFilePath,
  required String language, required int revision,
  required List<CodeDocumentSnapshot> documents});
CodeAnalysisResult({List<CodeDiagnostic> diagnostics = const [],
  String? unavailableReason});
```

```c
const char *qfli_web_syntax_version(void);
int32_t qfli_web_syntax_check(const char *source, size_t length,
    int32_t is_module, int32_t *start_offset, int32_t *end_offset,
    char *message, size_t message_capacity);
/* 0 parsed; 1 genuine SyntaxError with source range; -1 unavailable/resource */
```

```text
python scripts/build_web_syntax.py --platform windows|linux|macos|ohos|android|ios
  [--cc COMPILER] [--sdk SDK_OR_MINGW_ROOT] [--link-cc LINK_DRIVER]
  [--abi arm64-v8a|x86_64] [--arch arm64|x86_64]
  [--apple-sdk iphoneos|iphonesimulator|macosx] [--output DIRECTORY]
python native/web_syntax/test_native.py ABSOLUTE_NATIVE_LIBRARY
```

Native CMake exports `qfli_web_syntax`, shared by default and static with
`-DQFLI_WEB_SYNTAX_STATIC=ON`. Windows CMake uses `QFLI_SYNTAX_CC`, optional
`QFLI_SYNTAX_WINDOWS_SYSROOT` and `QFLI_SYNTAX_LINK_CC`. Desktop service tests may
set `QFLI_WEB_SYNTAX_LIBRARY` to a real bridge path.

## 3. Contracts

- Accept normalized absolute project/snapshot paths; every snapshot and the
  active path must be lexically within the project. Reject duplicate canonical
  snapshot paths and missing/stale active revisions. The adapter parses only
  the exact active buffer; it performs no project source reads or writes.
- Bound requests to 64 snapshots, 2 Mi UTF-16 code units in aggregate, and
  512 KiB UTF-8 for the active source. Parser work runs through `Isolate.run`.
  Core owns debounce, revision invalidation and dropping stale responses.
- A native parse creates a fresh runtime with 32 MiB heap and 512 KiB stack
  limits. Source is length-bounded and NUL terminated. The only `JS_Eval` call
  always includes `JS_EVAL_FLAG_COMPILE_ONLY`; discard its compiled value.
  Never call `JS_EvalFunction`, execute jobs, register a module loader, link
  `quickjs-libc`, or execute user code. No network/runtime fallback is allowed.
- Official QuickJS 2026-06-04 is retained with its MIT license and archive.
  Upstream resolves module imports before its compile-only return. Keep the
  exact recorded `compile-only-no-module-resolution.patch` so imports are
  syntax-checked without resolving/loading anything. Python verifies archive
  and `SOURCE.json` build-input SHA-256; CMake verifies `HASHES.sha256` at
  configure. Source changes require updating provenance and both manifests.
  Keep `vendor/quickjs/.gitattributes` disabling text conversion so Windows
  `core.autocrlf=true` checkouts preserve the pinned upstream bytes.
- Require GCC 9+ or Clang. Installed GCC 4.9.2 compiled a DLL that crashed on
  valid imports in `JS_DupAtom`; Clang 15 Windows compilation plus MinGW as
  linker passes. The source and Python preflight reject old GCC. Windows Clang
  must target GNU/MinGW; a default MSVC target requires `--sdk <MinGW-root>`
  (and optional `--link-cc`) or an explicitly GNU-target Clang. Check compiler
  target and platform headers before expensive compilation; never omit the
  shipping backend when prerequisites fail. Preserve upstream `-fwrapv` and
  build `-fno-strict-aliasing`.
- Diagnostics are half-open UTF-16 offsets in the original buffer; EOF can be
  an empty insertion range. QuickJS supplies one-based LF-delimited Unicode
  scalar columns; the bridge converts original UTF-8 to UTF-16, retaining
  CRLF and supplementary characters. HTML5 internally normalizes CRLF: map
  every normalized span boundary back to the original text. Script/style
  `endSourceSpan` can be null even with a closing tag; use actual text-node
  spans to bound raw content. Add embedded offsets against the original text.
- CSS spans already index the original Dart string. csslib accepts some modern
  constructs but rejects other valid grammar. When real parser messages meet
  a known unsupported construct, suppress messages for that stylesheet and
  set unavailable reason. The capability gate reuses `stripCssComments` and
  `isInsideQuotedRun`, ignores strings/comments, and recognizes container/scope
  queries, layer-order statements, relational/list selectors, `nth-child of`
  and media ranges. This is a finite capability gate, not a modern validator.
  Independently parsed HTML/JavaScript diagnostics can remain available.
- HTML external script/style references are never loaded. Inline classic
  JavaScript uses classic grammar, `type=module` and `.mjs` use module grammar;
  standalone `.js` accepts either classic or module syntax. If both fail, use
  the parser error reaching farther into source. Data-block scripts such as
  `application/ld+json` are not JavaScript. Unsupported script/style MIME types
  are not passed to the wrong grammar. Cap emitted diagnostics at 100.
- `unavailableReason == null` with no diagnostics means actual parsing finished
  for the covered grammar. Missing library, unsupported language/grammar,
  resource limits or parser failure must never masquerade as clean source.

Native delivery is required by the shipping platform build:

| Platform | Build / package / lookup |
| --- | --- |
| OHOS | SDK23 CMake `add_subdirectory`; package `libqfli_web_syntax.so` in both HAP ABI directories; FFI loads its library name |
| Android | Gradle externalNativeBuild targets retained native CMake; package ABI `.so`; pthread comes from libc, so no `-lpthread` |
| Linux | Product CMake builds and installs `.so` into executable `lib/`; loader uses that absolute path first |
| Windows | Product CMake separately invokes Python with GNU compiler/sysroot; DLL installs beside executable; no MSVC compilation of QuickJS |
| macOS | `bundle_web_syntax_apple.sh` builds/validates each architecture and embeds/signs dylib in `Contents/Frameworks`; loader uses that absolute path first |
| iOS | Same Apple builder selects device/simulator platform and architecture, validates objects and force-loads static archive; FFI resolves process symbols |

OHOS/Android shared libraries use 16 KiB LOAD alignment. Apple builds require
Xcode; iPhone devices use arm64, iOS minimum 13.0, macOS minimum 11.0. A build
must fail when native prerequisites are missing rather than silently dropping
JavaScript support. Runtime availability still reports missing delivery honestly.

## 4. Validation & Error Matrix

| Condition | Required result |
| --- | --- |
| Valid supported grammar | Real parser runs; empty diagnostics and null unavailable reason |
| Genuine syntax error | Parser-owned message, source name and validated exact range |
| Outside/duplicate/unnormalized path or stale active revision | Unavailable; no foreign or fabricated diagnostic |
| Unsupported language, oversized source, native stack/OOM | Explicit unavailable; no clean-source claim |
| Native library absent | QuickJS unavailable; independently checked HTML/CSS errors may remain |
| Valid CSS rejected because grammar is known unsupported | csslib unavailable for that stylesheet; no false source underline |
| Unsupported-marker text only inside CSS string/comment | Ignore marker; preserve real parser errors elsewhere |
| Changed retained QuickJS input | Python/CMake fail pin validation before shipping |
| Windows default MSVC Clang or GCC below 9 | Preflight failure with actionable compiler/sysroot requirement |
| Build/cross-compile succeeds without a device | Packaging evidence only; runtime/device acceptance stays open |

## 5. Good/Base/Bad Cases

- Good: unsaved `// 😀\r\nconst broken = ;` reports the semicolon's exact
  original UTF-16 position, leaves different disk contents untouched, and an
  imported module is compiled without opening its absent/remote dependency.
- Base: a supported CSS declaration error is reported by csslib; a valid modern
  `@scope` stylesheet rejected by csslib is explicitly unavailable.
- Bad: run user JavaScript for diagnostics, use a regex as a full parser, treat
  unavailable backends as no errors, underline valid CSS because csslib lacks
  its grammar, or feed closing/subsequent HTML into an embedded parser.

## 6. Tests Required

```text
flutter test --no-pub --concurrency=1 test/web_code_analyzer_test.dart
flutter analyze --no-pub lib/services/web_code_analyzer.dart lib/services/web_javascript_syntax.dart lib/services/web_javascript_syntax_native.dart lib/services/web_javascript_syntax_stub.dart test/web_code_analyzer_test.dart
python native/web_syntax/test_native.py build/native/web_syntax/windows/qfli_web_syntax.dll
```

Assert actual HTML/CSS errors, clean supported input, modern CSS capability
boundaries and string/comment exclusion, embedded CSS/JS offsets, CRLF/emoji/EOF,
unsaved-over-disk behavior/no writes, root/revision/size rejection, unavailable
native status and real classic/module/import grammar. Compile throw/infinite-loop,
fetch and filesystem statements without executing them. Exercise resource limits
and repeated fresh native contexts. An isolated mutated source fixture must fail
CMake's pin gate. Inspect ELF machine, DYN/entry zero, exports/imports, 16 KiB LOAD
alignment, and the fresh archive's native library entries before packaging claims.

Current evidence (2026-10-22): initial 15 service tests passed and scoped analysis
had no issues; native host probes passed; four modern-CSS regression tests were
added for the final integrated run. A separate real-adapter Dart probe passed
16 modern CSS cases plus comment/string exclusion. Windows DLL behavior passed;
SDK23 OHOS arm64/x86_64 and NDK28 Android arm64/x86_64 cross-builds passed;
SDK23 standalone CMake build and mutated-source rejection passed. See the active
task's `research/web-analysis-backend.md` for hashes and command evidence.

These do not prove signed installation or OHOS/Android device execution. Apple
compilation/runtime and Linux execution remain unverified on this host. Missing
platform evidence stays open; host results never substitute for those gates.

## 7. Wrong vs Correct

Wrong: call upstream `JS_Eval(..., JS_EVAL_FLAG_COMPILE_ONLY)` on modules and
assume it cannot load imports. Correct: retain and verify the no-resolution
patch, install no loader, and exercise imports of absent and remote modules.

Wrong: use `element.endSourceSpan ?? documentEnd` to extract script/style, or use
normalized HTML offsets directly. Correct: take raw text-node spans and map
their boundaries to the original unsaved UTF-16 string before parsing/offsetting.

Wrong: underline csslib's `expected {, but found (` for valid `@scope (.card)`.
Correct: detect the measured unsupported capability outside comments/strings,
report incomplete CSS analysis, and keep independently checked diagnostics.
