# Embedded Nginx Verification (2026-10-02)

## Delivered Source Boundary

Retained upstream Nginx 1.31.6, source SHA-256
`974ed5298a5e398e008704ed5db284e655fc270c596493dbccada452448fc9f1`.
The isolated upstream embedding patch SHA-256 is
`ad724d52db77c22867741571e43bf9f275bf5bef9a5f20140022b6752764ba37`.

Native pthread/token/stop/cleanup ABI, Linux verification library and iOS static
archive recipes are implemented. The iOS Runner links the archive and calls its
ABI through EmbeddedNginxBridge.swift. NginxSession now owns NginxInstance and
retains its existing middleware, config, health, proxy and diagnostics behavior.
Automatic/explicit native iOS selection uses the channel; explicit WebForge
continues to use its Dart server. Apple execution has not been established.

## Actual Native Results

Build host: existing WSL qfli-java-build, Linux x86_64, system C compiler. Each
recipe run creates a separate /tmp source tree; retained source is not changed.
The generated output/evidence directory is
`build/native/platform-audit/nginx-embedded/`.

- Nine real-library tests pass: actual upstream version/header and static/404;
  configuration check then run; invalid config and prohibited daemon/master/
  timer recovery; port conflict/rebind; busy/stale tokens; early/repeated stop;
  actual HTTP proxy body/path/query/status fidelity; active proxy/partial HTTP
  stop; environment, stdio, current directory and descriptor preservation.
- Those nine cases pass with AddressSanitizer and UndefinedBehaviorSanitizer.
  Python leak checking is disabled for its allocator. The separate native C
  harness keeps LeakSanitizer enabled and passes 100 config/start/HTTP/active-stop
  cycles with no sanitizer report. It independently checks native sigaction
  handler/mask/flags, stdio inode/device identity and descriptor counts.
- Static archive SHA-256 with sanitizers:
  `b62f9d44768b51cfdcd755597af4785fc9c49b29589182c33ef29b9ac381b707`.
- Final source/artifact hashes are in `sanitized/HASHES.sha256`; build details
  are in `sanitized-build.log`; final execution is in `final-native-test.log`.

Reproduction:

```bash
QFLI_NGINX_SANITIZE=1 bash scripts/build_nginx_embedded.sh linux /absolute/output
QFLI_NGINX_SANITIZE=1 bash scripts/test_nginx_embedded.sh /absolute/output
```

## Failures Resolved

The initial object-list parser treated tab-indented dependency continuations as
make recipes. It now follows the generated nginx target until its blank separator.
The first native test config omitted the prefix-local pid path; the fixture now
matches the real application's `pid nginx.pid` configuration. The environment
test records its pointer after setting its sentinel, avoiding its own setenv
allocation changing the baseline.

Active proxy Stop initially segfaulted. Direct ngx_http_free_request invokes
upstream cleanup, which finalizes request references and can recursively close
the same request pool. The final hook increments the main reference, invokes
ngx_http_terminate_request, then runs ngx_http_terminate_handler synchronously.
The exact active-proxy and partial-request regressions pass. Repeated Stop also
treats control-socket EPIPE during worker cleanup as a completed stop request.

## Product Regression And Android

- Owning Windows Flutter suite: 38 tests pass, including real upstream Nginx
  process integration and five embedded-channel lifecycle/error/diagnostic cases.
- `flutter analyze --no-pub lib test tool/nginx_smoke.dart`: clean. The initial
  unscoped analyzer scanned retained unrelated build copies and SDK internals,
  reporting 268831 issues. This is recorded separately from source analysis;
  no analyzer configuration was changed to hide it.
- Android debug smoke APKs built for all three existing ABIs. Actual execution
  is only emulator-5560, API 37, x86_64, 16 KiB. Process 7203 emitted:

```text
[NGINX_SMOKE] PASS HTML CSS 404 proxy WebSocket SSE diagnostics log port-conflict stop restart auto
```

The exact PID-filtered output is `android-smoke.log`. Native executable path is
the extracted APK native-library directory. This verifies the changed shared
process-host integration inside the application; it does not test the Swift host.

The ordinary `lib/main.dart` app was rebuilt and restored without uninstall or
data clearing. A build-number-1 install was rejected as a downgrade from the
installed build 4001; the ordinary build 4002 then installed successfully. Its
home view was inspected and retained in `android-ordinary.png` and XML.
Ordinary APK SHA-256:
`6b45494d03a481f666a73d1498968261d1a79d78072d45ce5f22c15c01c77e37`.
APK path: `build/app/outputs/flutter-apk/app-debug.apk`.

## Unavailable Gates And Delivery

No Xcode/Apple SDK/device/simulator is available. iOS target configure, compilation,
Mach-O object platform validation, final app link/signing, Safari/native preview
and device Stop are unverified and were not run. Linux engine, Windows process,
mocked channel and Android evidence do not establish those Apple gates. Android
ARM/32-bit execution and full Windows/Linux GUI builds remain unavailable here.

The source/spec/evidence slice awaits the workflow-required concrete commit plan.
Unrelated OHOS/startup/Trellis files and other product delivery artifacts remain
outside this slice. The whole cross-product goal stays active: native iOS Dart,
Java and Oracle requirements and other recorded delivery/build gaps remain.

## Portability Follow-up (2026-10-03)

Review found that upstream process/daemon source files still compiled fork even
when the runtime configuration disabled master/daemon. The iOS SDK forbids fork.
The embedded addon now excludes ngx_process.c, ngx_process_cycle.c, ngx_daemon.c
and ngx_setproctitle.c. It supplies the event/HTTP globals, rejects ngx_execute
and ngx_os_signal_process, and keeps ngx_debug_point from signaling the host.
The build rejects the four process-management objects and scans undefined archive
symbols for fork/vfork/exec/posix_spawn/kill/raise/system/popen/exit/abort/setproctitle.

Actual follow-up results:

- Linux ordinary build: nine library tests and 100 lifecycle cycles passed.
  Logs: process-free-build.log and process-free-test.log.
- Fresh ASan/UBSan build with the import gate: nine library tests passed; the
  native C harness passed 100 cycles with LeakSanitizer enabled. Descriptors,
  sigaction state and stdio were preserved. Logs: process-free-sanitized-build.log
  and process-free-sanitized-test.log.
- Latest sanitizer archive SHA-256:
  `d846937007a4b239e2a30970eedd65231454477c8189178738b4ce99d03b8df4`.
  Source/artifact hashes and the import list are in process-free-sanitized/
  HASHES.sha256 and undefined-symbols.txt. This supersedes the earlier archive.
- Reused-output regression: seeded process-free/libqfli_nginx.a with the original
  sanitizer archive containing all four process-management objects. The final
  builder creates a fresh archive in its unique build directory and replaces
  the output after verification. The rebuilt archive contains none of those
  members and passes the import gate. Evidence: reused-archive-before.txt,
  reused-archive-after.txt, process-free-reused-build.log and
  process-free-reused-test.log. This prevents ar rcs from preserving removed
  members across repeated Xcode builds.
- All 22 retained vendor input hashes and the four Bash syntax checks pass.
- Android was disconnected at resume. Started Pixel_10 using a read-only overlay,
  port 5560, without modifying the saved emulator state. Confirmed API 37 and
  16384-byte pages. Actual smoke build 4003, PID 15110, emitted:

```text
[NGINX_SMOKE] PASS HTML CSS 404 proxy WebSocket SSE diagnostics log port-conflict stop restart auto
```

PID-filtered evidence is android-smoke-2026-10-03.log; the device clock records
October 2. Smoke APK SHA-256:
`3702aaa0c8fc0d79150df90c02a9b4ee4c5aa07841134986cb11024441671f5f`.
Ordinary lib/main.dart build 4004 was rebuilt, installed with replacement and
launched. APK SHA-256:
`82f0f840ae7ea0fdf3e572fc26c5f9d988582bb3a8a6838a4a25797c183741c9`.
The ordinary home view and its four navigation tabs were inspected in
android-ordinary-2026-10-03.png and android-ordinary-2026-10-03.xml; installed
versionCode is 4004 and the displayed product is QFLIWebForge.
Neither uninstall nor app-data clearing was used. Android evidence validates the
process host; Linux evidence validates the changed embedded engine. Neither
establishes an Apple compiler/device pass. The same 30-file commit plan remains
pending its existing confirmation; no files have been staged or committed.
