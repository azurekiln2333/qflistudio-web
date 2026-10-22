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
import 'package:qfli_web/widgets/web_tools/web_source_inspector_view.dart';

void main() {
  late Directory temp;
  late ProjectStore store;
  late StudioProfile? previousProfile;

  setUp(() {
    previousProfile = StudioProfile.current;
    StudioProfile.current = webProfile;
    temp = Directory.systemTemp.createTempSync('webforge-tools-inline-');
    store = ProjectStore(storageFile: File('${temp.path}/projects.json'));
  });

  tearDown(() {
    StudioProfile.current = previousProfile;
    store.dispose();
    temp.deleteSync(recursive: true);
  });

  /// Registers a local project with [files] (path -> content) and loads it.
  Future<String> seedProject(
    WidgetTester tester,
    Map<String, String> files, {
    String name = 'Site',
  }) async {
    final root = Directory(p.join(temp.path, name))..createSync();
    files.forEach((relative, content) {
      final file = File(p.join(root.path, p.fromUri(relative)));
      file.parent.createSync(recursive: true);
      file.writeAsStringSync(content);
    });
    File('${temp.path}/projects.json').writeAsStringSync(
      jsonEncode({
        'version': 1,
        'projects': [Project.create(name: name, path: root.path).toJson()],
      }),
    );
    await tester.runAsync(store.load);
    return root.path;
  }

  Future<void> finishInspection(WidgetTester tester) async {
    // Drive real filesystem/isolate work outside the test fake clock, observing
    // the public busy indicator instead of private State fields.
    await tester.runAsync(() async {
      for (var attempt = 0; attempt < 500; attempt++) {
        await Future<void>.delayed(const Duration(milliseconds: 5));
        await tester.pump();
        if (find.byType(LinearProgressIndicator).evaluate().isEmpty) return;
      }
    });
    expect(find.byType(LinearProgressIndicator), findsNothing);
  }

  Future<void> pumpOverview(
    WidgetTester tester, {
    VoidCallback? onOpenTerminal,
    Size? surface,
    double textScale = 1,
  }) async {
    if (surface != null) {
      tester.view.physicalSize = surface;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
    }
    await tester.pumpWidget(
      MaterialApp(
        home: MediaQuery(
          data: MediaQueryData(textScaler: TextScaler.linear(textScale)),
          child: Scaffold(
            body: WebToolsOverview(
              store: store,
              onOpenTerminal: onOpenTerminal,
            ),
          ),
        ),
      ),
    );
    await finishInspection(tester);
    await tester.pumpAndSettle();
  }

  /// The page's own scroll view; the embedded views add their own.
  Finder outerScrollable() => find
      .descendant(
        of: find.byType(CustomScrollView),
        matching: find.byType(Scrollable),
      )
      .first;

  /// Scrolls the single page scroll view until [target] is built.
  ///
  /// A plain `scrollUntilVisible` drag is unreliable here because the embedded
  /// server/codec views own their own scrollables in the middle of the page, so
  /// the test drives the real [ScrollPosition] instead.
  Future<void> scrollTo(WidgetTester tester, Finder target) async {
    final state = tester.state<ScrollableState>(outerScrollable());
    for (var step = 0; step < 40 && target.evaluate().isEmpty; step++) {
      final position = state.position;
      if (position.pixels >= position.maxScrollExtent) break;
      position.jumpTo(
        (position.pixels + 240).clamp(0, position.maxScrollExtent),
      );
      await tester.pumpAndSettle();
    }
    expect(target, findsWidgets, reason: '目标控件没有出现在工具页里');
    await tester.ensureVisible(target.first);
    await tester.pumpAndSettle();
  }

  testWidgets('every Web tool is inline on the tools page', (tester) async {
    await seedProject(tester, {'index.html': '<html></html>'});
    await pumpOverview(tester, onOpenTerminal: () {});

    // The page itself is the tools surface: no second "hub" route.
    expect(find.text('Web 工具'), findsNothing);
    expect(find.text('终端'), findsWidgets);
    expect(find.text('本地服务'), findsOneWidget);
    // Real controls, not gateway cards: the embedded server view is live.
    expect(find.text('启动'), findsOneWidget);

    // Everything else is built by the same single scroll view, further down.
    await scrollTo(tester, find.widgetWithText(TextField, '输入'));
    expect(find.text('Web 编解码'), findsOneWidget);
    for (final title in ['文档资源检查', 'CSS 颜色与盒子', '结构检查与格式化']) {
      await scrollTo(tester, find.text(title));
      expect(find.text(title), findsOneWidget);
    }
    await scrollTo(tester, find.text('通用工具'));
    expect(tester.takeException(), isNull);
  });

  testWidgets('terminal entry calls the shell route', (tester) async {
    var opened = 0;
    await pumpOverview(tester, onOpenTerminal: () => opened++);
    await tester.tap(find.text('打开终端'));
    await tester.pump();
    expect(opened, 1);
  });

  testWidgets('codec converts inline without navigation', (tester) async {
    await pumpOverview(tester);
    await scrollTo(tester, find.widgetWithText(TextField, '输入'));
    await tester.enterText(find.widgetWithText(TextField, '输入'), '{"ok":true}');
    await tester.tap(find.text('格式化'));
    await tester.pump();
    expect(find.text('{\n  "ok": true\n}'), findsOneWidget);
    expect(find.byType(BackButton), findsNothing);
  });

  testWidgets(
    'CSS panel reports colours, contrast, box model and specificity',
    (tester) async {
      await pumpOverview(tester);
      await scrollTo(tester, find.widgetWithText(TextField, '样式表'));

      // Default sample: rebeccapurple and its WCAG contrast against white.
      expect(find.textContaining('#663399'), findsWidgets);
      expect(find.textContaining(':1'), findsWidgets);

      await tester.tap(find.text('盒模型'));
      await tester.pumpAndSettle();
      expect(find.textContaining('外框宽度'), findsWidgets);
      // 320 content + 2*20 padding + 2*1 border = 362 px in content-box.
      expect(find.textContaining('362'), findsWidgets);

      await tester.tap(find.text('优先级'));
      await tester.pumpAndSettle();
      expect(find.textContaining('(0, 2, 0)'), findsWidgets);

      await tester.tap(find.text('重复声明'));
      await tester.pumpAndSettle();
      expect(find.text('没有重复声明'), findsOneWidget);
    },
  );

  testWidgets('CSS panel finds duplicate declarations', (tester) async {
    await pumpOverview(tester);
    await scrollTo(tester, find.widgetWithText(TextField, '样式表'));
    await tester.enterText(
      find.widgetWithText(TextField, '样式表'),
      '.a { color: red; margin: 0; color: blue; }',
    );
    await tester.tap(find.text('重复声明'));
    await tester.pumpAndSettle();
    expect(find.textContaining('color  ×2'), findsOneWidget);
    expect(find.textContaining('1:29'), findsOneWidget);
  });

  testWidgets('markup panel checks structure, accessibility and formats', (
    tester,
  ) async {
    await pumpOverview(tester);
    await scrollTo(tester, find.widgetWithText(TextField, 'HTML 片段'));

    expect(find.textContaining('没有闭合'), findsWidgets);
    expect(find.textContaining('alt'), findsWidgets);

    await tester.tap(find.text('重排缩进'));
    await tester.pumpAndSettle();
    expect(find.text('重排结果（逐标签重排）'), findsOneWidget);
    expect(find.textContaining('<html>'), findsWidgets);

    // Switching to CSS re-runs the other scanner on the same buffer.
    await scrollTo(tester, find.text('CSS'));
    await tester.tap(find.text('CSS'));
    await tester.pumpAndSettle();
    expect(find.widgetWithText(TextField, 'CSS 片段'), findsOneWidget);
  });

  testWidgets('document inspector resolves real project references', (
    tester,
  ) async {
    await seedProject(tester, {
      'index.html':
          '<html lang="zh-CN"><head><title>站点</title>'
          '<meta name="viewport" content="width=device-width">'
          '<link rel="stylesheet" href="css/app.css"></head>'
          '<body><img src="assets/a.png" alt="a">'
          '<img src="assets/missing.png" alt="m">'
          '<img src="https://cdn.example.com/x.png" alt="c"></body></html>',
      'css/app.css': '.hero { background: url("../assets/a.png"); }',
      'assets/a.png': 'png',
    });
    await pumpOverview(tester);
    await scrollTo(tester, find.text('文档资源检查'));

    expect(find.text('缺失 1'), findsOneWidget);
    expect(find.text('外部 1'), findsOneWidget);
    expect(find.text('本地 3'), findsOneWidget);
    expect(find.textContaining('https://cdn.example.com/x.png'), findsWidgets);
    expect(find.textContaining('assets/missing.png'), findsWidgets);
    expect(find.textContaining('离线检查未通过'), findsOneWidget);
  });

  testWidgets('document inspector reports an offline-clean project', (
    tester,
  ) async {
    await seedProject(tester, {
      'index.html':
          '<html lang="zh-CN"><head><title>站点</title>'
          '<meta name="viewport" content="width=device-width"></head>'
          '<body><h1>你好</h1><img src="a.png" alt="图"></body></html>',
      'a.png': 'png',
    });
    await pumpOverview(tester);
    await scrollTo(tester, find.text('文档资源检查'));
    expect(find.text('缺失 0'), findsOneWidget);
    expect(find.text('外部 0'), findsOneWidget);
    expect(find.textContaining('可直接离线预览'), findsOneWidget);
  });

  testWidgets('the integrated page survives a narrow 2x-text viewport', (
    tester,
  ) async {
    await seedProject(tester, {'index.html': '<html></html>'});
    await pumpOverview(tester, surface: const Size(320, 640), textScale: 2);
    expect(tester.takeException(), isNull);

    // Everything stays reachable by scrolling the single page.
    for (final label in ['Web 编解码', '文档资源检查', '结构检查与格式化', '通用工具']) {
      await scrollTo(tester, find.text(label));
      expect(tester.takeException(), isNull);
    }
  });

  testWidgets('resource inspector updates after project load and removal', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SingleChildScrollView(
            child: WebSourceInspectorInlineView(store: store),
          ),
        ),
      ),
    );
    expect(find.textContaining('还没有本地项目'), findsOneWidget);
    await seedProject(tester, {'index.html': '<img src="missing.png" alt="">'});
    await tester.pump();
    await finishInspection(tester);
    expect(find.text('缺失 1'), findsOneWidget);
    expect(find.textContaining('可直接离线预览'), findsNothing);
    File(
      '${temp.path}/projects.json',
    ).writeAsStringSync(jsonEncode({'version': 1, 'projects': []}));
    await tester.runAsync(store.load);
    await tester.pumpAndSettle();
    expect(find.textContaining('还没有本地项目'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('disposing an in-flight resource scan does not set state later', (
    tester,
  ) async {
    await seedProject(tester, {'index.html': '<html></html>'});
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: WebSourceInspectorInlineView(store: store)),
      ),
    );
    // Dispose immediately, while real async directory discovery is pending.
    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 50)),
    );
    await tester.pump();
    expect(tester.takeException(), isNull);
  });
}
