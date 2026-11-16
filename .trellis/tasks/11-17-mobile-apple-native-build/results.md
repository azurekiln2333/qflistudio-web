# Mobile and Apple native delivery — 2026-11-17

## License alignment

The user requested GPL v3 alignment with `D:/MyNewProjects/qflistudio` and
authorized commit/push. Both root LICENSE files already contain identical GPL
version 3 text. Their SHA-256 is
`3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986`.

Commit `ffe90f1` makes the project-level declaration explicit in the simplified
Chinese, English and traditional Chinese READMEs. It preserves the separately
declared Nginx/QuickJS licenses and CC BY 4.0 curriculum. No sibling files changed.

## Delivery scope

Commit `d8c9bc0592e5076c12e1751e693a063d5326a4bb` publishes Android, OHOS, iOS
and macOS native components using existing toolchains. Linux only publishes
regression logs. Windows retains its existing prebuilt Nginx. Both commits were
pushed to `ci/native-build-20261117` using the explicit GitHub repository URL.

No main merge or other configured push destination was used.

## Hosted checks

- Android/Linux run: https://github.com/azurekiln2333/qflistudio-web/actions/runs/43939931188
  at `d8c9bc0`, all four jobs passed.
- OHOS run: https://github.com/azurekiln2333/qflistudio-web/actions/runs/43939931954
  at `d8c9bc0`, both ABIs passed.
- Initial Apple run: https://github.com/azurekiln2333/qflistudio-web/actions/runs/43939931369
  at `d8c9bc0`; iOS simulator x86_64 failed at Darwin `sem_init`/`sem_destroy`
  warnings treated as errors. macOS x86_64 failed the initial compiler probe.
  The run was canceled after recording these failures, freeing queued targets.
- Commit `30927b6` corrects iOS semaphore feature detection and prints the
  configure error log on failure, without disabling warnings or symbol gates.
- Android/Linux rerun: https://github.com/azurekiln2333/qflistudio-web/actions/runs/43941454536
  at `30927b6`, all jobs passed.
- OHOS rerun: https://github.com/azurekiln2333/qflistudio-web/actions/runs/43941454542
  at `30927b6`, passed.
- Apple rerun: https://github.com/azurekiln2333/qflistudio-web/actions/runs/43941454332
  at `30927b6` remained queued for more than 15 minutes. It was canceled after
  the newer configuration was pushed, avoiding duplicate obsolete builds.
- Commit `a7989dc796473fb5cf4ee7701d08115f565ee9ff` scopes deployment variables
  to their matching Apple jobs and exports the explicitly selected macOS SDK to
  the initial compiler probe. The previous x86_64 failure's exact diagnostic
  remains unavailable; this SDK correction is not recorded as a proven root cause.
- Latest Apple rerun: https://github.com/azurekiln2333/qflistudio-web/actions/runs/43943840834
  at `a7989dc`, queued. No Apple artifact or host runtime pass is claimed.
- Latest Android/Linux rerun: https://github.com/azurekiln2333/qflistudio-web/actions/runs/43943840838
  at `a7989dc`, all four jobs passed. The macOS-only change did not trigger OHOS;
  its latest successful run remains `43941454542` at `30927b6`.

The Apple acceptance criteria remain open while hosted runners are unavailable.
Do not archive this task or replace pending status with success based on static
checks alone. The license request is complete and pushed independently.

## Download verification

All three Android ZIPs, the dual-ABI OHOS ZIP and the Linux logs ZIP from
`d8c9bc0` were downloaded. All five ZIP sizes and GitHub digests matched. All
five tar archives matched their sidecar checksums, and all 83 inner file hashes
matched. Commit, ABI, ELF machine/class and license bytes matched the source.
`mobile-download-verification.json` records the artifacts and archive hashes.

Linux publishes only six `.log` files. They record QuickJS syntax checks,
embedded lifecycle tests, four access-log sequences and seven Linux CDP cases.

## Local checks and limits

Actionlint, Python compilation and Chinese prose lint passed before push.
Root LICENSE equality was checked independently. No local native or Flutter
build was run. Cloud builds do not remove existing local caches or automatically
make the application consume downloaded libraries. These artifacts are native
components, not APK/HAP/IPA installers or device/signing acceptance evidence.
