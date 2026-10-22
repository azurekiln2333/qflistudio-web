# WebForge real-catalog language UI acceptance

## Boundary

This slice owns only `test/web_catalog_language_test.dart` and this evidence
record. The missing behavior is subject language selection/display through the
shared Home tutorial/example tabs when every runnable entry imports as HTML.
The source of that behavior is the shared local-content list/filter/title
mapping; its sole common-core owner receives findings. No product or core
implementation, generated assets, commits or other acceptance gates are changed
by this slice.

## Inputs and contract

- Read current parent PRD/design/implementation, frontend content-import and
  quality contracts, `test/content/webforge_content_test.dart`, shared
  `local_content_filters_test.dart` and `home_content_repository_test.dart`.
  The requested repository test is actually named
  `test/content/webforge_content_test.dart` in this checkout.
- The test reads the actual shipped `assets/content/tutorials.json` and
  `assets/content/examples.json` bytes. Only the Flutter asset transport is
  mocked; no replacement/reduced content or custom profile factory is used.
- The unmodified `webProfile` supplies its real `contentRepositoryFactory` to
  the shared `HomePage`; its normal tutorial/example navigation opens the real
  retained shared tabs and detail routes.
- Expected release snapshot: 481 tutorials, 481 examples, with 160 HTML,
  160 CSS and 161 JavaScript subjects. Every executable `type` stays `html`.
- Public repository checks prove subject counts, HTML filenames and separate
  `language: css` versus `type: css` filter behavior.
- UI checks click all three subject chips and All languages, assert visible
  result counts, combine a subject with real title search, inspect visible
  row/detail badge text, open the real import dialog and require `index.html`,
  cancel, then reset filters back to 481.
- Both tabs are exercised at 1000px and at 320px with 2x text. All interactions
  use the real widgets, labels, tooltips, routes and scrollables; no private
  state is used as evidence.

## Source finding

Initial review found
`../qfli_studio_core/lib/pages/local_content_pages.dart` `_contentLanguage`
preferring executable `type` over explicit subject `language`:

```dart
languageKey(type.trim().isEmpty ? language : type)
```

For WebForge this collapses all subjects to HTML. The required mapping prefers
nonempty `language`, using `type` only as a fallback. Reported to the root for
the sole common-core writer; no core source was edited here. The shared owner
delivered the correction before the focused run. The consumed implementation
at `local_content_pages.dart:418` now uses:

```dart
languageKey(language.trim().isEmpty ? type : language)
```

## Validation

2026-10-22, after the coordinator explicitly released the serialized Flutter
slot:

```text
flutter test --no-pub --concurrency=1 test/web_catalog_language_test.dart
00:08 +5: All tests passed!

D:/ProgramFiles/flutter_ohos/bin/cache/dart-sdk/bin/dart.exe analyze test/web_catalog_language_test.dart
No issues found!
```

All five cases passed: the public profile/repository contract and both real
Home catalogs at desktop and 320px/2x text. The narrow tests additionally assert
the inherited text scaler is actually 2x. Each of the four UI cases exercises
all three subjects, separate counts, All languages, combined title search,
visible list and route-title badges, the real `index.html` import dialog,
cancellation and reset to 481.

The initial focused run passed 4/5; its narrow tutorial case scrolled a
`RawTooltip` layout surrogate whose reported center remained outside the
viewport. The test now scrolls/taps the actual `IconButton` and explicitly
requires both a hit-testable button and its localized tooltip. No production
change or assertion weakening was needed for this test-harness correction.

`trellis-check` review found no remaining issues in the owned files. Existing
content-import specs already state the subject/import-format distinction; the
new fixture and source defect are captured here for the coordinating owner's
spec-sync review. No unrelated source, assets or specs were edited, no commits
were made, and the Flutter slot was released immediately after the passing run.

This is host Flutter UI and shipped-content evidence. It does not prove OHOS
execution or satisfy the other products' R4 gates.
