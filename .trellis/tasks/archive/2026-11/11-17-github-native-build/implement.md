# Execution

1. Inspect native builders, specs, Git state, remote access and local sizes.
2. Add workflow, explicit artifact packaging and download documentation.
3. Verify YAML/actions, script syntax and artifact contents with local fixtures.
4. Review changes against native/runtime contracts.
5. Commit task-owned files and push the CI branch to GitHub as requested.
6. Observe the actual hosted build; fix failures and rerun until complete or an
   external prerequisite is conclusively unavailable.
7. Record exact run URLs, artifacts, SHA and limitations.

Do not run local platform builds: the user wants their resource use moved off the
host. Native behavior tests execute in the hosted Linux job. Flutter sources are
unchanged, so app compilation and Flutter-wide regression tests are out of scope.

Rollback consists of reverting the task commit. No local data cleanup is included.
