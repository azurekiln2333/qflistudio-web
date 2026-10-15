import 'dart:io';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_web/services/nginx_host.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final messenger =
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
  const host = EmbeddedNginxHost();
  late Directory prefix;
  late List<MethodCall> calls;
  int? exitCode;
  bool pollingError = false;

  setUp(() async {
    prefix = await Directory.systemTemp.createTemp('embedded-host-contract-');
    calls = [];
    exitCode = null;
    pollingError = false;
    messenger.setMockMethodCallHandler(EmbeddedNginxHost.channel, (call) async {
      calls.add(call);
      switch (call.method) {
        case 'version':
          return '1.31.6';
        case 'start':
          return 41;
        case 'poll':
          if (pollingError) {
            pollingError = false;
            throw PlatformException(code: 'POLL_FAILED');
          }
          return exitCode;
        case 'stop':
          return null;
        case 'release':
          return null;
        default:
          throw MissingPluginException();
      }
    });
  });
  tearDown(() async {
    messenger.setMockMethodCallHandler(EmbeddedNginxHost.channel, null);
    await prefix.delete(recursive: true);
  });

  test(
    'checks the native version and config before releasing a completed worker',
    () async {
      expect(await host.version(), '1.31.6');
      exitCode = 0;
      await host.validate(prefix);
      expect(calls.map((call) => call.method), [
        'version',
        'start',
        'poll',
        'release',
      ]);
      expect(calls[1].arguments, {'prefix': prefix.path, 'test': true});
      expect(calls.last.arguments, {'token': 41});
    },
  );

  test('configuration failure includes bounded native diagnostics', () async {
    await File(
      p.join(prefix.path, 'error.log'),
    ).writeAsString('${'x' * 20000}\n[emerg] invalid native directive\n');
    exitCode = 1;
    await expectLater(
      host.validate(prefix),
      throwsA(
        isA<StateError>()
            .having(
              (error) => error.toString(),
              'diagnostic',
              contains('invalid native directive'),
            )
            .having(
              (error) => error.toString().length,
              'bounded length',
              lessThan(17000),
            ),
      ),
    );
    expect(calls.last.method, 'release');
  });

  test(
    'stop waits for completed native cleanup before releasing the token',
    () async {
      final instance = await host.start(prefix);
      var stopped = false;
      final stop = instance.stop().then((_) => stopped = true);
      await Future<void>.delayed(const Duration(milliseconds: 90));
      expect(stopped, false);
      expect(calls.any((call) => call.method == 'release'), false);
      expect(calls.first.arguments, {'prefix': prefix.path, 'test': false});
      exitCode = 0;
      await stop.timeout(const Duration(seconds: 2));
      expect(await instance.exitCode, 0);
      expect(calls.where((call) => call.method == 'release'), hasLength(1));
      await instance.stop();
      expect(calls.where((call) => call.method == 'stop'), hasLength(1));
    },
  );

  test(
    'a poll channel failure can still stop and reclaim the native session',
    () async {
      pollingError = true;
      final instance = await host.start(prefix);
      await expectLater(instance.exitCode, throwsA(isA<PlatformException>()));
      exitCode = 0;
      await instance.stop();
      expect(calls.last.method, 'release');
    },
  );

  test('native startup errors and invalid tokens propagate', () async {
    messenger.setMockMethodCallHandler(EmbeddedNginxHost.channel, (_) async {
      throw PlatformException(code: 'NGINX_START', details: -16);
    });
    await expectLater(host.start(prefix), throwsA(isA<PlatformException>()));
    messenger.setMockMethodCallHandler(
      EmbeddedNginxHost.channel,
      (_) async => -16,
    );
    await expectLater(host.start(prefix), throwsA(isA<StateError>()));
  });

  test('an absent embedded channel signals WebRuntime.auto to fall back', () async {
    // WebRuntime probes version() before selecting the embedded engine; a
    // missing channel must surface as MissingPluginException so `auto` can
    // degrade to the Dart middleware instead of failing startup.
    messenger.setMockMethodCallHandler(EmbeddedNginxHost.channel, null);
    await expectLater(host.version(), throwsA(isA<MissingPluginException>()));
  });

  test('a malformed embedded version never selects the native engine', () async {
    messenger.setMockMethodCallHandler(
      EmbeddedNginxHost.channel,
      (call) async => call.method == 'version' ? 'not-a-version' : null,
    );
    await expectLater(host.version(), throwsA(isA<StateError>()));
  });
}
