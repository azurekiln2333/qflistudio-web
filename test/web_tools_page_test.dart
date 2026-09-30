import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qfli_studio_core/store/project_store.dart';
import 'package:qfli_web/pages/web_tools_page.dart';

void main() {
  late Directory temp;
  late ProjectStore store;
  late HttpOverrides? previousOverrides;

  setUp(() {
    previousOverrides = HttpOverrides.current;
    HttpOverrides.global = null;
    temp = Directory.systemTemp.createTempSync('webforge-tools-');
    store = ProjectStore(storageFile: File('${temp.path}/projects.json'));
  });

  tearDown(() {
    HttpOverrides.global = previousOverrides;
    store.dispose();
    temp.deleteSync(recursive: true);
  });

  Future<void> open(WidgetTester tester, String tab) async {
    await tester.pumpWidget(MaterialApp(home: WebToolsPage(store: store)));
    await tester.tap(find.text(tab));
    await tester.pumpAndSettle();
  }

  testWidgets('HTTP tool sends the selected method, headers and body', (
    tester,
  ) async {
    final received = Completer<void>();
    final upstream = await tester.runAsync(() async {
      final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      server.listen((incoming) async {
        expect(incoming.method, 'POST');
        expect(incoming.headers.value('x-test'), 'webforge');
        expect(await utf8.decoder.bind(incoming).join(), 'request body');
        incoming.response.statusCode = HttpStatus.created;
        incoming.response.write('response body');
        await incoming.response.close();
        received.complete();
      });
      return server;
    });
    addTearDown(() => upstream!.close(force: true));
    await open(tester, 'HTTP');
    await tester.enterText(
      find.widgetWithText(TextField, 'URL'),
      'http://127.0.0.1:${upstream!.port}/',
    );
    await tester.tap(find.text('POST'));
    await tester.pump();
    await tester.enterText(
      find.widgetWithText(TextField, '请求头 JSON'),
      '{"x-test":"webforge"}',
    );
    await tester.enterText(
      find.widgetWithText(TextField, '请求体'),
      'request body',
    );
    await tester.ensureVisible(find.text('发送'));
    await tester.runAsync(() async {
      tester
          .widget<FilledButton>(find.widgetWithText(FilledButton, '发送'))
          .onPressed!();
    });
    for (
      var attempts = 0;
      attempts < 100 && !received.isCompleted;
      attempts++
    ) {
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 20)),
      );
      await tester.pump();
    }
    expect(received.isCompleted, isTrue);
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 100)),
    );
    await tester.pumpAndSettle();
    await tester.drag(find.text('发送'), const Offset(0, -400));
    await tester.pumpAndSettle();
    expect(
      find.textContaining('201 Created'),
      findsOneWidget,
      reason: tester
          .widgetList<SelectableText>(find.byType(SelectableText))
          .map((text) => text.data)
          .join('\n'),
    );
    expect(find.textContaining('response body'), findsOneWidget);
  });

  testWidgets('codec tools perform JSON, URL and Base64 conversions', (
    tester,
  ) async {
    await open(tester, '编解码');
    final input = find.widgetWithText(TextField, '输入');
    await tester.enterText(input, '{"ok":true}');
    await tester.tap(find.text('格式化'));
    await tester.pump();
    expect(find.text('{\n  "ok": true\n}'), findsOneWidget);

    await tester.tap(find.text('URL'));
    await tester.pump();
    await tester.enterText(input, 'a b&c');
    await tester.tap(find.text('编码'));
    await tester.pump();
    expect(find.text('a%20b%26c'), findsOneWidget);

    await tester.tap(find.text('Base64'));
    await tester.pump();
    await tester.enterText(input, 'aGVsbG8=');
    await tester.tap(find.text('解码'));
    await tester.pump();
    expect(find.text('hello'), findsOneWidget);
  });
}
