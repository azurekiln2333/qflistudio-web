# WebForge terminal integrity audit and release verification

## Context

Child task of `10-15-webforge-store-readiness`. Owns the terminal surface of the
WebForge store submission: the in-editor shared terminal (`TerminalPane`) and
the standalone full-screen Terminax workspace (`TerminaxTerminalPage`). The
shared implementation lives in the read-only sibling `qfli_studio_core`; this
task may only read it and write inside `qfli_web`.

## Deliverables

- `test/web_terminal_release_test.dart` — release verification of both surfaces.
- Web-scope defect fixes only where a verifiable defect exists.
- `research/core-terminal-findings.md` — read-only audit of the shared core.
- Spec updates under `.trellis/spec/`.

## Out of scope

- `lib/main.dart`, `lib/pages/web_tools_page.dart`, `pubspec.yaml`, content
  assets, platform configuration (owned by other owners).
- Any write under `../qfli_studio_core`.
- `flutter build` (owned by the main controller).

## Acceptance Criteria

- [ ] Both terminals are exercised through the real widget tree.
- [ ] Web toolchain wiring (html/css/js preview, no language delegate) verified.
- [ ] Built-in commands, execute, cancel/interrupt, exit verified.
- [ ] Current-file preview (tap default vs long-press current file) verified.
- [ ] Console error return (`appendDebug`) verified.
- [ ] Offline gating (no online/cloud/login/git entry) verified.
- [ ] `flutter analyze --no-pub lib test` and the release suite pass.
- [ ] Findings written to `research/core-terminal-findings.md`.
