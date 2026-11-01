import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/models/project.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/store/project_store.dart';
import 'package:qfli_web/main.dart' show webProfile;
import 'package:qfli_web/pages/web_tools_overview.dart';
import 'package:qfli_web/pages/web_tools_page.dart';

import 'web_dev_server_test.dart' show request;

Finder _serverItem(Finder matching) =>
    find.descendant(of: find.byType(WebServerToolsView), matching: matching);

Finder _serverIconButton(String tooltip) => _serverItem(
  find.byWidgetPredicate(
    (widget) => widget is IconButton && widget.tooltip == tooltip,
  ),
);

Future<void> _waitFor(
  WidgetTester tester,
  bool Function() ready, {
  required String reason,
}) async {
  for (var attempt = 0; attempt < 250; attempt++) {
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 20)),
    );
    await tester.pump();
    if (ready()) return;
  }
  expect(ready(), isTrue, reason: reason);
}

Future<void> _reveal(WidgetTester tester, Finder target) async {
  await tester.ensureVisible(find.byType(WebServerToolsView));
  await tester.pumpAndSettle();
  final scrollable = _serverItem(find.byType(Scrollable)).first;
  final position = tester.state<ScrollableState>(scrollable).position;
  // Only the public scroll position is used. The embedded ListView builds log
  // rows lazily, especially at 2x text scale. A completed HTTP response can also
  // precede its request-stream event, so scan again after bounded real I/O waits.
  // Keep the outer panel aligned above, then reveal only within this ListView.
  // tester.ensureVisible(target) also scrolls the outer overview and can move
  // an otherwise built control beyond the screen before the following tap.
  position.jumpTo(0);
  await tester.pump();
  for (var step = 0; step < 250; step++) {
    if (target.evaluate().isNotEmpty) {
      await position.ensureVisible(
        tester.renderObject(target.first),
        alignment: 0.5,
      );
      await tester.pumpAndSettle();
      if (target.hitTestable().evaluate().isNotEmpty) return;
    }
    position.jumpTo(
      position.pixels >= position.maxScrollExtent
          ? 0
          : (position.pixels + 160).clamp(0, position.maxScrollExtent),
    );
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 20)),
    );
    await tester.pump();
  }
  expect(
    target.hitTestable(),
    findsWidgets,
    reason: 'Inline server control/log was not hit-testable',
  );
}

Future<void> _expectRefused(WidgetTester tester, String url) async {
  final uri = Uri.parse(url);
  // Darwin/POSIX ECONNREFUSED and Windows ERROR_CONNECTION_REFUSED /
  // WSAECONNREFUSED. A timeout or any other socket error is not refusal.
  const connectionRefusedCodes = <int>{61, 111, 1225, 10061};
  var refused = false;
  for (var attempt = 0; attempt < 100 && !refused; attempt++) {
    final observation = await tester.runAsync(() async {
      Socket? socket;
      try {
        socket = await Socket.connect(
          uri.host,
          uri.port,
          // This Windows host's closed-loopback control needed just over 2s
          // to produce native10061; Dart synthesizes10060 at a shorter cap.
          timeout: const Duration(seconds: 5),
        );
        return (refused: false, error: null, trace: null);
      } on Object catch (error, trace) {
        final connectionRefused =
            error is SocketException &&
            connectionRefusedCodes.contains(error.osError?.errorCode);
        return (
          refused: connectionRefused,
          error: connectionRefused ? null : error,
          trace: connectionRefused ? null : trace,
        );
      } finally {
        socket?.destroy();
      }
    });
    expect(observation, isNotNull, reason: 'Real TCP probe did not complete');
    final probe = observation!;
    if (probe.error case final error?) {
      Error.throwWithStackTrace(error, probe.trace!);
    }
    refused = probe.refused;
    // dispose starts stop without awaiting it. Its watcher-cancellation
    // continuation belongs to the widget fake-async zone. A TCP probe needs no
    // HTTP handler response, so it returns while the listener is still open and
    // lets this pump advance cleanup before the next connection attempt.
    await tester.pump();
    if (!refused) {
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 10)),
      );
    }
  }
  expect(refused, isTrue, reason: 'Owned preview endpoint still accepts TCP');
}

void main() {
  for (final layout in [
    (
      name: 'regular light',
      size: const Size(800, 900),
      scale: 1.0,
      brightness: Brightness.light,
    ),
    (
      name: '320px dark with 2x text',
      size: const Size(320, 780),
      scale: 2.0,
      brightness: Brightness.dark,
    ),
  ]) {
    testWidgets('inline local server lifecycle: ${layout.name}', (
      tester,
    ) async {
      final previousProfile = StudioProfile.current;
      final previousOverrides = HttpOverrides.current;
      StudioProfile.current = webProfile;
      HttpOverrides.global = null;
      tester.view.physicalSize = layout.size;
      tester.view.devicePixelRatio = 1;
      final temp = Directory.systemTemp.createTempSync(
        'webforge-inline-server-lifecycle-',
      );
      final project = Directory(p.join(temp.path, 'site'))..createSync();
      File(p.join(project.path, 'index.html')).writeAsStringSync(
        '<!doctype html><html><head><title>Inline server</title></head>'
        '<body><h1>tools lifecycle page</h1></body></html>',
      );
      final config = File(p.join(project.path, '.qfli', 'web.json'));
      config.parent.createSync(recursive: true);
      config.writeAsStringSync(jsonEncode({'engine': 'webforge', 'port': 0}));
      final originalConfig = config.readAsStringSync();
      final registry = File(p.join(temp.path, 'projects.json'));
      registry.writeAsStringSync(
        jsonEncode({
          'version': 1,
          'projects': [
            Project.create(name: 'Lifecycle site', path: project.path).toJson(),
          ],
        }),
      );
      final store = ProjectStore(storageFile: registry);
      final ownedUrls = <String>{};
      addTearDown(() async {
        // Widget disposal owns production session cleanup even on assertions
        // that fail before the explicit Stop/restart checks below.
        await tester.pumpWidget(const SizedBox.shrink());
        await tester.runAsync(
          () => Future<void>.delayed(const Duration(milliseconds: 30)),
        );
        try {
          for (final url in ownedUrls) {
            await _expectRefused(tester, url);
          }
        } finally {
          store.dispose();
          StudioProfile.current = previousProfile;
          HttpOverrides.global = previousOverrides;
          tester.view.reset();
          temp.deleteSync(recursive: true);
        }
      });
      await tester.runAsync(store.load);
      await tester.pumpWidget(
        MaterialApp(
          theme: ThemeData(brightness: layout.brightness, useMaterial3: true),
          home: Builder(
            builder: (context) => MediaQuery(
              data: MediaQuery.of(
                context,
              ).copyWith(textScaler: TextScaler.linear(layout.scale)),
              child: Scaffold(
                // Exercise the shipped profile hook used by the shared Tools
                // tab, including its actual inline WebServerToolsView.
                body: webProfile.toolsTabBuilder!(store, () {}),
              ),
            ),
          ),
        ),
      );
      await _waitFor(
        tester,
        () => find.byType(LinearProgressIndicator).evaluate().isEmpty,
        reason: 'Real inline resource discovery did not finish',
      );
      expect(find.byType(WebToolsOverview), findsOneWidget);
      expect(find.byType(WebServerToolsView), findsOneWidget);
      expect(find.text('本地服务'), findsOneWidget);
      expect(find.text('Web 工具'), findsNothing);
      expect(find.text('HTTP'), findsNothing);
      expect(tester.takeException(), isNull);

      final start = _serverItem(find.widgetWithText(FilledButton, '启动'));
      final stop = _serverItem(find.widgetWithText(OutlinedButton, '停止'));
      final clear = _serverIconButton('清空记录');
      final copy = _serverIconButton('复制地址');
      final address = _serverItem(
        find.byWidgetPredicate(
          (widget) =>
              widget is SelectableText &&
              widget.data != null &&
              RegExp(r'^http://127\.0\.0\.1:\d+/$').hasMatch(widget.data!),
        ),
      );

      Future<String> startFromControl() async {
        await _reveal(tester, start);
        expect(tester.widget<FilledButton>(start).onPressed, isNotNull);
        await tester.runAsync(() => tester.tap(start));
        await _waitFor(
          tester,
          () =>
              stop.evaluate().isNotEmpty &&
              tester.widget<OutlinedButton>(stop).onPressed != null,
          reason: 'The real Start gesture did not reach a running session',
        );
        await _reveal(tester, address);
        expect(address, findsOneWidget);
        final url = tester.widget<SelectableText>(address).data!;
        ownedUrls.add(url);
        expect(Uri.parse(url).port, greaterThan(0));
        final engine = _serverItem(find.text('WebForge'));
        await _reveal(tester, engine);
        expect(engine, findsOneWidget);
        await _reveal(tester, copy);
        return url;
      }

      Future<void> expectLog(Pattern text) async {
        final line = _serverItem(find.textContaining(text));
        await _reveal(tester, line);
        expect(line, findsWidgets);
      }

      final firstUrl = await startFromControl();
      await expectLog('服务已启动 $firstUrl');
      await tester.runAsync(() async {
        final page = await request('${firstUrl}index.html');
        expect(page.status, HttpStatus.ok);
        expect(page.body, contains('<h1>tools lifecycle page</h1>'));
        final missing = await request('${firstUrl}missing.js');
        expect(missing.status, HttpStatus.notFound);
        expect(missing.body, isNot(contains('<h1>tools lifecycle page</h1>')));
        final diagnostic = await request(
          '${firstUrl}__webforge/debug',
          method: 'POST',
          headers: {
            'content-type': 'application/json',
            'origin': Uri.parse(firstUrl).origin,
          },
          body: jsonEncode({
            'level': 'warn',
            'message': 'inline console marker',
          }),
        );
        expect(diagnostic.status, HttpStatus.noContent);
      });
      await tester.pump();
      await expectLog(RegExp(r'^GET /index\.html\s+200\s+\d+ ms$'));
      await expectLog(RegExp(r'^GET /missing\.js\s+404\s+\d+ ms$'));
      await expectLog('[web.http] GET /missing.js');
      await expectLog('[web.warn] inline console marker');
      await expectLog(RegExp(r'^POST /__webforge/debug\s+204\s+\d+ ms$'));

      await _reveal(tester, clear);
      expect(tester.widget<IconButton>(clear).onPressed, isNotNull);
      await tester.tap(clear);
      await tester.pump();
      expect(tester.widget<IconButton>(clear).onPressed, isNull);
      expect(
        _serverItem(find.textContaining('inline console marker')),
        findsNothing,
      );
      expect(_serverItem(find.textContaining('GET /missing.js')), findsNothing);
      // Clearing only the visible transcript keeps the actual session and its
      // subscriptions alive, so a subsequent diagnostic must appear normally.
      await tester.runAsync(() async {
        final response = await request(
          '${firstUrl}__webforge/debug',
          method: 'POST',
          headers: {'content-type': 'application/json'},
          body: jsonEncode({'level': 'log', 'message': 'after clear marker'}),
        );
        expect(response.status, HttpStatus.noContent);
      });
      await tester.pump();
      await expectLog('[web.log] after clear marker');

      await _reveal(tester, stop);
      await tester.runAsync(() => tester.tap(stop));
      await _waitFor(
        tester,
        () =>
            start.evaluate().isNotEmpty &&
            tester.widget<FilledButton>(start).onPressed != null,
        reason: 'Stop did not return the inline controls to idle',
      );
      expect(tester.widget<OutlinedButton>(stop).onPressed, isNull);
      await _expectRefused(tester, firstUrl);

      final secondUrl = await startFromControl();
      await tester.runAsync(() async {
        expect(
          (await request(secondUrl)).body,
          contains('tools lifecycle page'),
        );
      });
      expect(config.readAsStringSync(), originalConfig);
      await tester.pumpWidget(const SizedBox.shrink());
      await _expectRefused(tester, secondUrl);
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 50)),
      );
      await tester.pump(const Duration(milliseconds: 250));
      expect(tester.takeException(), isNull);
    });
  }
}
