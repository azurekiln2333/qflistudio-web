import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:qfli_web/services/web_runtime.dart';

import '../tool/nginx_smoke.dart' as smoke;

/// Device gate for the real native Nginx runtime.
///
/// `tool/nginx_smoke.dart` is the only end-to-end native engine check (HTML,
/// CSS, 404, proxy, WebSocket, SSE, diagnostics, logging, stop/restart, engine
/// selection). It is a standalone tool, so a run that logs
/// `[NGINX_SMOKE] FAIL` must be turned into an actual test failure here;
/// otherwise a broken engine looks green.
///
/// The smoke is driven through [WidgetTester.runAsync] because it performs real
/// socket and file IO that the fake-async zone of `testWidgets` would stall.
/// `runAsync` reports an error thrown inside its callback through the binding
/// rather than failing the enclosing test, so the trailing
/// `tester.takeException()` assertion is what makes a thrown smoke error fail
/// this test instead of passing silently.
///
/// Run on a device/emulator that ships the native runtime:
///
/// ```bash
/// flutter test integration_test/nginx_runtime_test.dart -d <device>
/// ```
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('native Nginx runtime smoke passes end to end', (tester) async {
    // Only a desktop dev host may legitimately lack the packaged runtime. Every
    // platform that ships the native engine with the app — Android, iOS,
    // HarmonyOS — must have it: a missing runtime there is a broken package, so
    // the test must fail instead of skipping. A skip would let a runtime-less
    // build pass this gate.
    if (_desktopHostWithoutRuntime(await WebRuntime.nginxExecutable())) {
      markTestSkipped(
        'native Nginx runtime is not available on '
        '${Platform.operatingSystem}; run this on a device that ships it',
      );
      return;
    }

    // Android ships the executable as `jniLibs/<abi>/libnginx_exec.so` and the
    // platform channel reports its path. Require it explicitly so a package
    // missing the ABI-specific binary fails here with a clear message rather
    // than relying on the smoke's downstream error.
    if (Platform.isAndroid) {
      expect(
        await WebRuntime.nginxExecutable(),
        isNotNull,
        reason:
            'Android must ship the native Nginx executable; a null path means '
            'the package is missing libnginx_exec.so',
      );
    }

    await tester.runAsync(smoke.main);

    // A failure inside runAsync is surfaced here, not as a test failure on its
    // own. Without this expect() a broken engine could still report a green run.
    expect(
      tester.takeException(),
      isNull,
      reason: 'the native Nginx smoke reported a failure',
    );
  });
}

/// True only for a desktop development host that has no packaged runtime.
///
/// iOS, HarmonyOS and Android all ship the native engine with the app, so they
/// are never skipped: the caller treats their `null` path as a failure. iOS and
/// HarmonyOS deliver the engine as an embedded shared library rather than a
/// standalone executable, so they have no executable path to probe at all and
/// proceed straight to the smoke, which fails for real if the library is
/// absent.
bool _desktopHostWithoutRuntime(String? executable) {
  if (Platform.isIOS || Platform.operatingSystem == 'ohos') return false;
  if (!(Platform.isWindows || Platform.isLinux || Platform.isMacOS)) {
    return false;
  }
  return executable == null;
}
