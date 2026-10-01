# Tutorial and example code imports

## Goal

Simplify MD3 content catalogs and support custom-filename imports that open the project and imported file.

## Requirements

- Show tutorial/example catalogs as concise MD3 title and summary rows.
- Put code in detail pages with import-to-editor and import-to-project actions.
- Allow custom filenames and automatically open the project and imported file.
- Import the current edited example code; preserve existing project identity and entry.
- Confirm replacements and handle cancellation, invalid names and I/O errors.
- Preview imported HTML even when its entry uses a custom filename.

## Acceptance Criteria

- [x] Catalogs hide code; detail routes expose both import actions.
- [x] All four tutorial/example and editor/new-project combinations write and open custom files.
- [x] Existing-project import preserves identity/entry and activates the imported file.
- [x] Cancellation, replacement rejection and I/O failures do not report success.
- [x] Edited code imports correctly and custom HTML previews through real Nginx on Android.
- [x] Relevant analysis, 36 core tests, 32 product tests and Android integration passed.

## Notes

This is a retrospective record created after task-creation consent arrived.
The implementation and Android verification were already authorized and completed.
WebForge implementation commit: `d1ef042`. Shared core changes remain mixed with
other sessions' work and were not included in that product commit.
Detailed evidence lives in `research/content-import-validation.md`.
