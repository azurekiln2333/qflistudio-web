# Web terminal and current-file preview

## Goal

Use the shared continuous terminal in WebForge and make long-press Run preview
the open HTML file while a normal tap retains the configured project entry.
The user requested implementation by pi in the right pane, supervised by Codex.

## Background

Both Java and Web use the sibling qfli_studio_core working tree. Java's workspace
is already delivering the shared terminal and Run gestures. The HTML branch
receives entryOverride but always opens server.url, losing the selected file.
WebForge's actual document root can differ from the project root.

## Requirements

- Commands, output and the next prompt share one top-aligned scrollback.
- Preserve program-authored output; do not inject Chinese success sentences,
  exit-code-zero messages or JDK implementation labels.
- Tap runs the configured entry, long press runs the active file, and a later
  tap still uses the default. Save changes before launch.
- Preview the selected HTML with working relative assets through WebForge and
  Nginx, using the session's actual document root and public endpoint.
- Invalid targets fail explicitly; never silently substitute the default page.
- Preserve existing factory signatures, navigation, project configuration and
  unrelated Nginx/iOS/OHOS changes.

## Acceptance criteria

- [x] Verify shared terminal and Java title changes against current source,
  available visuals and test evidence.
- [x] Serve index.html, main2.html, then index.html without rewriting config.
- [x] Cover derived src roots, explicit roots, nested files and URI escaping.
- [x] Reject inaccessible or outside-root current files explicitly.
- [x] Verify Nginx public URLs, diagnostics and clean session shutdown.
- [x] Relevant analysis and regression tests pass; record limitations separately.

## Scope and ownership

Web integration belongs to qfli_web. pi may write only inside this workspace.
Prepare any necessary core delta as a reviewable patch here and apply it only
through an approved filesystem operation. Preserve the existing shared-terminal
implementation owned by the Java workspace. No commits or pushes in this turn.
