# Content Import Contracts

## 1. Scope / Trigger

Apply when changing offline tutorial/example catalogs or importing their code.
Shared UI and file operations live in `qfli_studio_core`; WebForge owns preview.

## 2. Signatures

```dart
CodeSnippet(example: example, controller: controller,
    store: projects, auth: auth, settings: settings);
CodeImportService.openInEditor(example: example, fileName: fileName);
CodeImportService.importIntoProject(project: project, example: example,
    fileName: fileName, overwrite: overwrite);
ProjectStore.createProjectFromExample(name: name, example: example,
    fileName: fileName);
EditorPage(project: project, auth: auth, store: projects, settings: settings,
    initialOpenPath: importedPath);
```

## 3. Contracts

- Catalogs use MD3 list rows with titles and summaries. Code is in detail routes.
- Code blocks provide copy, import to editor and import to project icon buttons
  with localized tooltips. Imports receive the real HomePage stores.
- Import accepts a basename. New projects record the chosen relative entry in
  `.qfli/project.json`, retain companion assets and remove default entry code.
- Editor imports create registered, persistent snippet projects. Existing project
  imports retain project identity and the original entry, and confirm replacement.
- Import uses the displayed code, including unsaved edits in example details.
- Success opens the actual imported file in the real editor, taking precedence
  over a restored editor session. Cancellation creates no files or navigation.

## 4. Validation & Error Matrix

| Condition | Result |
| --- | --- |
| Invalid filename or project name | Dialog stays open with validation error |
| Existing file | Confirm replacement; rejection preserves the file |
| Cloud, missing or unavailable project | Error; no editor opens |
| File or project registration I/O failure | Error; no false success |
| Missing optional stores | Import buttons are disabled |
| Small viewport or large text | Scrollable content and reachable dialog actions |

## 5. Good / Base / Bad Cases

- Good: edit an example, import as `lesson.html`, and inspect the same code in
  the automatically opened editor. HTML preview reads the custom entry.
- Base: import bundled code with its default suggested filename.
- Bad: show full code in the catalog, import the original instead of edited
  code, or restore an old file as the editor's active tab after importing.

## 6. Tests Required

- Core `test/content_code_import_test.dart`: both catalogs, four new-import
  combinations, existing project/session precedence, replacement, cancellation,
  I/O failures, edited code persistence and 320/1280px layouts at 2x text.
- Product `integration_test/content_import_test.dart`: run with
  `flutter test --no-pub -d <android-device> integration_test/content_import_test.dart`.
  It uses packaged content, real plugins and files, verifies the active editor
  file, imports to existing projects and requests custom HTML through Nginx.
- Widget tests evict cached content assets and reinstall the mock handler for
  each test. Pump route transitions before interacting with detail/dialog UI;
  settle and ensure icon buttons are visible before tapping.

## 7. Wrong vs Correct

Wrong: importing returns success but leaves a restored default file active, or
the server still assumes `index.html` after a custom HTML import.

Correct: pass `initialOpenPath` through to the editor and carry the configured
HTML entry through `WebProjectConfig.indexFile` to both preview engines.
