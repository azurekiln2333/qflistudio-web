# Web named workspace source handoff

Status: **SOURCE ONLY / UNRUN**. Observed UTC: **2026-10-24T01:36:19.258584+00:00**.

The new product-only `test/web_saved_workspaces_test.dart` consumes the actual
`webProfile` and `QfliApp`. It does not change the profile key, opt into the main
product, replace the workspace store, or add production test hooks. The fixture
adapts the corrected JSON named-workspace case, including the actual IconButton
finder, initial sidebar animation frame, and bounded fake-time/real-I/O waits.
It uses two real local HTML projects, each with `index.html` and a nested page.

The one regression is intended to prove:

- Home exposes four local scopes including named workspaces, while the cloud
  scope is absent and `webProfile` remains offline and non-main.
- A real project card opens the primary source, and the real explorer workspace
  dialog saves a name plus a second local root to a workspace document on disk.
- Both same-name HTML files retain distinct owning roots. Closing and reopening
  the tree preserves nested directory expansion.
- Destroying the whole app/controller, draining metadata writes, reloading the
  store from disk, and rebuilding Home allows the saved workspace card to reopen
  both documents with their cursor positions, active owner, and expanded trees.
- Project source bytes and the pre-existing standalone `history.json` remain
  unchanged by named-session edits and reconstruction. This does not replace the
  broader legacy cross-root migration suite.

## Shared dependency and publication boundary

The inspected shared HEAD is `36697b04836a9dc6178f96071eca010f1685218c`. At inspection, `studio_profile.dart`,
`home_page.dart`, and `file_explorer.dart` were modified and
`workspace/saved_workspaces_tab.dart` was untracked. The named capability requires
current `StudioProfile.supportsSavedWorkspaces`, the corresponding saved-workspace
helper and explorer dialog, Home scope/card plumbing, and retained editor/store
session handling. The table below records observed raw bytes, not a frozen
committed or staged candidate. Passing this test against a dirty shared worktree
would not prove those dependencies were published. C/main retain sole ownership
of shared implementation and publication; no core file was written here.

No Dart formatter, analyzer, Flutter test, compiler, browser, native build, HAP,
WSL or device command was run for this handoff. Source review/whitespace checks
are not executed acceptance. The global named host queue controls later checks.

An independent source-only review found no concrete API, selector, HTML owner
type, offline-scope or teardown defect. It confirmed that `showHomeTabs: false`
suppresses language chips while Home still offers the four local project scopes.
The test's raw source passed the whitespace check; compilation and execution
remain pending.

An independent final source review against core HEAD
`2f9039a3ba95449679b17257b0313c1ee3644a2c` found no concrete fixture defect.
The live `home_page.dart` still contains main-product WIP beyond that commit;
the next gate therefore binds raw live dependencies rather than claiming a
pure published-core-only run. The updated focused worker includes this test
before Tools and hashes234 inputs, including effective analysis options and
both runner files. Its snapshot-only preflight passed; execution is still unrun.

Planned coordinated commands:

```text
flutter test --no-pub --concurrency=1 --reporter expanded test/web_saved_workspaces_test.dart
flutter analyze --no-pub test/web_saved_workspaces_test.dart
```

## Observed source bytes

Execution update: [repair10](web-runtime-repair10-tests.log) actually passes the
real Web named-workspace case, including whole-app/controller reconstruction,
both owners/cursors/expanded nested roots, source bytes and strict standalone
history equality. The six-file gate ends57/57;11-file analysis is clean and
all234 raw source hashes match. [Job cleanup/publication](web-runtime-repair10-job.json)
is terminal/active0 and releases to Note549. The live Home WIP boundary above
still applies. The table below is the original source-handoff snapshot, not a
substitute for the run's full before/after manifests.

| Path | SHA-256 |
| --- | --- |
| `test/web_saved_workspaces_test.dart` | `e9d8e9ea0dabc5fa2703f78d942e5f40d0d0ad62115639feb781a8017a914d0a` |
| `lib/main.dart` | `7395a48e7e23fff17cc55ae23880b1d8fb9cfbb0a29ab34f9a1254c621d8c72b` |
| `pubspec.yaml` | `f85c0cd770a5c4aebd9f92ee3744e5a79d970b3606688943ba6cf2c371a15d2c` |
| `../qfli_studio_core/lib/app.dart` | `e1763de75de969a92fe039719d2846daa7456f2dd8d171854ff8020d2d19b59f` |
| `../qfli_studio_core/lib/services/studio_profile.dart` | `0368fe6860309229369814dedd656ec370f47d2db7f6f3d9e0141cd5cda9c81c` |
| `../qfli_studio_core/lib/pages/home_page.dart` | `84cdfc0f3e6fd16c001e2200b45447a470fe66e7eff363bbb54773f02085be3c` |
| `../qfli_studio_core/lib/editor/file_explorer.dart` | `6b99ad68a789e2a20d4f49f54ccbf9fa193e9eca852e34a8976bf0b13353a661` |
| `../qfli_studio_core/lib/editor/editor_page.dart` | `8549c7e4d00692c27876636d436811100a231d04cb842f263d50eaaab7c07ca4` |
| `../qfli_studio_core/lib/editor/editor_controller.dart` | `1f5c479936575046f6af374e1d41538b00c69af93124b0b0781a2c6d400311f2` |
| `../qfli_studio_core/lib/editor/editor_problems_bar.dart` | `dafbfc6aec077afb715484861198d269b564a2bf248bb13a78eea7c184fd470f` |
| `../qfli_studio_core/lib/editor/project_history.dart` | `d90e00a4a0ed7f92729dc1d19aac4331ed035ca881afc6924ce669aac3337eba` |
| `../qfli_studio_core/lib/editor/retained_editor_host.dart` | `58d91921b177173842222f1d2aecb1261f73633abe3a8fefeb4ae33f27e8ba78` |
| `../qfli_studio_core/lib/workspace/saved_workspace.dart` | `f658b3ddca9dcf8152282304428523836b4b3b93ab95a1d034b43316f3bc5720` |
| `../qfli_studio_core/lib/workspace/workspace_store.dart` | `1c1cd747f3b3c66b92399aa92a6f61703774a6e1754423ca61acf222a9fecf8d` |
| `../qfli_studio_core/lib/workspace/workspace_dialogs.dart` | `a947571b26fb23f513221e2955a5e81123beb0931d4031cd2ce2c3c424c00481` |
| `../qfli_studio_core/lib/workspace/saved_workspaces_tab.dart` | `d63e6e55d4cfadf4982ff841a2c3835d6d7ee727d966682a5a1914494b4536a5` |
| `../qfli_studio_core/lib/services/app_paths.dart` | `a16eff0376123dc467c7cf638bf55ab19e584305174f80d954ca82a7c20edb69` |
| `../qfli_studio_core/lib/services/task_activity_service.dart` | `d0675696eba2551360809658bb1a89957ee029bc0fa2f1a989d83f2fb2e18ea7` |
