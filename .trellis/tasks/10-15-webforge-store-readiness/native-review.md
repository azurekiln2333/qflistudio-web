# Native change boundary and baseline

The initial tree contains unfinished embedded-Nginx and current-file preview
work. Review that product delta, retain its actual native implementation, run
real process/HTTP tests and build platform packages before committing it.

Two release configuration gaps were confirmed:
- OHOS `build-profile.json5` references missing signing files. Installed profiles
  bind JVMX, Forge, PyFlow, cloudterminal or older Studio products, not WebForge.
  Preserve the local legacy configuration in ignored runtime storage, remove
  invalid signing material from the product configuration and build unsigned.
  User has been asked asynchronously for a WebForge signing profile.
- OHOS retains an AccountKit login bridge and placeholder client_id metadata even
  though the product is offline. Remove these unused product-native paths; the
  shared offline UI policy remains unchanged. Internet permission remains needed
  for the loopback preview server.

Expected edits: OHOS root build profile (unsigned portable configuration),
EntryAbility (remove unused account channel), module metadata (remove placeholder),
and page manifest (only the Flutter page). Keep the pre-existing AgreementReader
file local; it is untracked and becomes unreachable, and is not part of delivery.

Baseline: analyze of lib/test/integration_test/tool passes; product tests are
47 passed and 2 old navigation failures assigned to UI worker. Native Linux
rebuild attempt cannot start the default Ubuntu distribution because its VHDX is
missing. The lightweight qfli-terminal-test distribution has Python but no C
compiler. Native claims will use packaged platform builds/device results rather
than claiming a new Linux-native pass.

## Delivery checkpoint (2026-10-15)

- Reviewed the embedded C lifecycle, Dart host and OHOS/iOS bridges; p5 cross-review is under the nginx-integration child task.
- Product runtime/current-file tests passed within the full run (77 passing, three unrelated stale content-contract assertions pending correction). Real Windows Nginx transport/stop/restart tests passed. Scoped analyze is clean.
- All21 retained-source/archive/binary SHA-256 entries match. Android release and OHOS unsigned release builds succeeded before the final content freeze; final artifacts will be rebuilt. Apple source integration remains unbuilt on Windows.
- Commit all native sources, scripts, OHOS static archives and NAPI/iOS bridges together so a clean checkout has the complete native delivery. Preserve unrelated historical cross-product audit patches.

## Final metadata review

OHOS AppScope still carried the template vendor `example`. Replace it with
the existing product brand `QFLI`; retain the WebForge bundle identity and
version. The final unsigned HAP must contain this metadata.
