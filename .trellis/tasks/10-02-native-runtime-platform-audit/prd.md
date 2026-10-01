# Complete native runtimes across QFLI products

## Goal

Provide real native language engines and working platform integration across
the QFLI products. Preserve the user's full request: inspect non-OHOS platforms,
implement missing support, test every environment available on this host, and
skip environments that cannot be run here with an explicit record.

## Requirements

- Cover C/C++, Lua, Python, Dart, Java, Go, Rust, SQL and WebForge. Existing
  platform tasks and other conversations do not establish completion.
- Use the actual upstream engine. Do not substitute a Dart evaluator or label
  an unrelated server/interpreter as a native upstream implementation.
- Complete the build, packaging, platform bridge and application execution
  chain for every supported native platform. Record OS restrictions as remaining
  implementation gaps rather than silently shrinking the scope.
- Preserve unrelated and concurrent work. Apply narrowly scoped changes and
  commit separately in each owning repository with conventional messages.
- Test functional outcomes on available platforms. Record an unavailable
  environment separately from a failing implementation or a test pass.

## Acceptance Criteria

- [x] A source-backed platform matrix identifies each product's real engine,
  build, package, bridge and runtime evidence.
- [ ] Every identified missing platform integration is implemented or retained
  as an explicit unresolved requirement. No whole-goal completion while gaps remain.
- [ ] Representative programs compile/execute with imports, actual output,
  errors and cancellation on available environments.
- [ ] Compiler artifacts can be reloaded and executed by the real engine.
- [ ] Platform build and runtime skips state the unavailable prerequisite.
- [ ] All delivered changes are committed in the owning repository. Tested
  source snapshots and patches are not presented as delivered product changes.

## Notes

The authoritative user request is the active cross-product goal. OHOS is not
the requested verification focus; existing unresolved OHOS records stay intact.
The current session can write only qfli_web. Sibling product changes require the
extra filesystem permission. Automatic permission review was unavailable (HTTP
503) during earlier WSL attempts; do not bypass the review mechanism.
