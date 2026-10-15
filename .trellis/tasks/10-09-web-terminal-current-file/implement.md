# Implementation

1. [x] Inspect worktrees, shared-core changes and Java integration.
2. [x] Start pi-web-terminal in wD:p2 and obtain a read-only audit.
3. [x] Confirm HTML selection loss and choose the compatible session capability.
4. [x] pi captures current core inputs and prepares a narrow patch in research.
5. [x] Review and check the patch, then apply with sibling-directory approval.
6. [x] pi implements Web session capability and focused regression tests.
7. [x] Check selected-URL flow, failure cleanup, compatibility and visuals.
8. [x] Record exact results and preserve unrelated uncommitted changes.

## Validation commands

- flutter test --no-pub --concurrency=1 test/web_app_test.dart test/web_dev_server_test.dart
- Relevant test/nginx_session_test.dart cases with the existing native binary.
- flutter analyze --no-pub lib test
- Rerun shared editor_run_test.dart / terminal_pane_test.dart when the core
  delta or unresolved concerns justify it.

Broad analysis currently includes stale copies under build/native/platform-audit;
report that independently from targeted source validation.

## Rollback

Compare task deltas against captured working-tree inputs, not all of HEAD.
Never reset or overwrite sibling trees. Rebase the small patch if any affected
core file changes concurrently.
