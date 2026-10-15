# Quality Guidelines

> Quality standards for `qfli_web` runtime and native work. Verification must be
> based on a real engine, not a mock channel or a filename.

---

## Required Checks

Run these before reporting a task complete (the `--no-pub` flag avoids a network
resolve and is the test convention; release mode transitions require pub-enabled
builds as described in [Release Verification](./release-verification.md)):

```bash
flutter analyze --no-pub lib test
flutter test --no-pub --concurrency=1 test/<affected>_test.dart
```

Native/device claims need their own evidence — see
[Web Runtime](./web-runtime.md) and
`.trellis/spec/backend/native-runtime.md`.

## Quality Expectations

- **Behavior tests over unit assertions.** Serve over a real loopback
  `HttpClient`, assert status and body, and check post-stop connection refusal.
  See `test/web_dev_server_test.dart` and `test/nginx_session_test.dart`.
- **One shared HTTP helper.** Reuse `request(...)` from
  `test/web_dev_server_test.dart` (`import 'web_dev_server_test.dart' show
  request;`) instead of copying a client into each file.
- **Every started session is stopped in teardown.** Use
  `addTearDown(server.stop)` even when the test stops it explicitly, so an
  assertion failure cannot leak a listener.
- **Unavailable platforms are recorded, never faked.** The application smoke
  fails on Android/OHOS/iOS when the required packaged engine is unavailable.
  An unsupported desktop host may record a visible skip (`markTestSkipped`).
  Missing device/signing/build environments remain explicit limits, never passes.

## Forbidden Patterns

- Labelling the Dart middleware as "Nginx". Advertise Nginx only when a real
  upstream `nginx` binary or embedded library is packaged, started and stopped.
- A second preview listener: the editor already owns one via
  `webProfile.webPreviewFactory`; do not also start one through
  `RunnerService.runProject`.
- Manual URL percent-encoding by string concatenation for the preview resolver;
  build the URL through `Uri`/`Uri.parse` (see the current-file preview contract
  in `test/web_preview_current_file_test.dart`).
- Loosening `WebProjectConfig.parse` to accept an invalid config at save time.
- Test-only hooks added to production code paths.

## Code Review Checklist

- Does the change keep exactly one public preview endpoint per run, and does it
  stop on editor exit?
- Are traversal, hidden-file and symlink-escape requests still rejected?
- Does an explicit engine selection still fail loudly instead of substituting?
- For native changes: is the ELF for the right ABI, and are build/bundle hashes
  updated (`vendor/nginx/HASHES.sha256`, `SOURCE.json`)?
- Do new tests assert real HTTP/engine behavior, not just that a URL string was
  produced?
