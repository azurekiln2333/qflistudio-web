import 'dart:io';

import 'package:flutter/services.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path_provider_platform_interface/path_provider_platform_interface.dart';
import 'package:qfli_studio_core/app.dart';
import 'package:qfli_studio_core/layout/app_form_factor.dart';
import 'package:qfli_studio_core/pages/home_page.dart';
import 'package:qfli_studio_core/services/app_paths.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/shell/large_screen_workbench.dart';
import 'package:qfli_studio_core/splash_screen.dart';
import 'package:qfli_web/main.dart' as app;

void main() {
  final binding = TestWidgetsFlutterBinding.ensureInitialized();
  const channel = MethodChannel('qflistudio/platform');
  final messenger = binding.defaultBinaryMessenger;
  late Directory directory;
  late PathProviderPlatform originalPaths;
  StudioProfile? originalProfile;

  setUpAll(() async {
    directory = await Directory.systemTemp.createTemp('qfli_web_startup_');
    originalPaths = PathProviderPlatform.instance;
    PathProviderPlatform.instance = _TemporaryPaths(directory.path);
    await AppPaths.storageDirectory();
  });

  tearDownAll(() async {
    PathProviderPlatform.instance = originalPaths;
    await directory.delete(recursive: true);
  });

  setUp(() {
    binding.resetFirstFrameSent();
    originalProfile = StudioProfile.current;
  });

  tearDown(() {
    messenger.setMockMethodCallHandler(channel, null);
    StudioProfile.current = originalProfile;
  });

  Future<void> waitForBootstrap(WidgetTester tester) async {
    final root = tester.widget<QfliApp>(find.byType(QfliApp));
    for (var attempt = 0; !root.ready!.value && attempt < 100; attempt++) {
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 10)),
      );
      await tester.pump();
    }
    expect(root.ready!.value, isTrue);
  }

  void expectHostShell(WidgetTester tester) {
    // TargetPlatformVariant selects the startup path, not the host OS that
    // QfliApp uses to choose its device family. Desktop hosts keep a workbench.
    final shell = find.byType(LargeScreenWorkbench);
    expect(
      shell,
      findsOneWidget,
      reason: '${Platform.operatingSystem} must retain its real desktop shell',
    );
    expect(
      tester.widget<LargeScreenWorkbench>(shell).formFactor,
      AppFormFactor.desktop,
    );
    expect(find.byType(HomePage), findsNothing);
    expect(find.byType(SplashScreen), findsNothing);
  }

  Future<void> finishStartupAndUnmount(WidgetTester tester) async {
    try {
      // Start bootstrap even if an assertion failed before the first pump.
      // Keep the app and progress handler alive until real store I/O finishes.
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 160));
      await waitForBootstrap(tester);
    } finally {
      try {
        // Drain both native display delays and endOfFrame on failure too.
        // Observe production's release; never call allowFirstFrame in the test
        // to conceal a leaked deferral from the following Android assertion.
        await tester.pump(const Duration(milliseconds: 1100));
        await tester.pump();
        expect(
          binding.sendFramesToEngine,
          isTrue,
          reason: 'Startup must release its own first-frame deferral',
        );
      } finally {
        await tester.pumpWidget(const SizedBox.shrink());
      }
    }
  }

  for (final bridge in ['available', 'missing', 'error']) {
    testWidgets(
      'OHOS keeps native startup through home layout with $bridge progress bridge',
      (tester) async {
        final progress = <double>[];
        if (bridge != 'missing') {
          messenger.setMockMethodCallHandler(channel, (call) async {
            expect(call.method, 'startupProgress');
            if (bridge == 'error') {
              throw PlatformException(code: 'PROGRESS_UNAVAILABLE');
            }
            progress.add((call.arguments as Map)['progress'] as double);
            return null;
          });
        }

        try {
          await app.main();
          expect(binding.sendFramesToEngine, isFalse);
          await tester.pump();
          expect(find.byType(SplashScreen), findsOneWidget);
          await tester.pump(const Duration(milliseconds: 160));
          await waitForBootstrap(tester);
          await tester.pump();

          expectHostShell(tester);
          expect(binding.sendFramesToEngine, isFalse);
          if (bridge == 'available') {
            expect(progress, isNotEmpty);
            expect(progress.first, 0.05);
            expect(progress.last, 1.0);
            expect(progress, orderedEquals([...progress]..sort()));
          }

          await tester.pump(const Duration(milliseconds: 1100));
          await tester.pump();
          expect(binding.sendFramesToEngine, isTrue);
          expect(tester.takeException(), isNull);
        } finally {
          await finishStartupAndUnmount(tester);
        }
      },
      variant: TargetPlatformVariant({TargetPlatform.ohos}),
    );
  }

  testWidgets(
    'Android renders its Flutter loading frame immediately',
    (tester) async {
      messenger.setMockMethodCallHandler(channel, (call) async {
        fail('Android startup must not use the OHOS progress bridge');
      });

      try {
        await app.main();
        expect(binding.sendFramesToEngine, isTrue);
        await tester.pump();
        expect(find.byType(SplashScreen), findsOneWidget);
        await waitForBootstrap(tester);
        await tester.pump();
        expectHostShell(tester);
        expect(tester.takeException(), isNull);
      } finally {
        await finishStartupAndUnmount(tester);
      }
    },
    variant: TargetPlatformVariant({TargetPlatform.android}),
  );
}

class _TemporaryPaths extends PathProviderPlatform {
  _TemporaryPaths(this.path);

  final String path;

  @override
  Future<String?> getApplicationSupportPath() async => path;

  @override
  Future<String?> getApplicationDocumentsPath() async => path;
}
