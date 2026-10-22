import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qfli_studio_core/app.dart';
import 'package:qfli_studio_core/models/project.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/store/auth_store.dart';
import 'package:qfli_studio_core/store/project_store.dart';
import 'package:qfli_studio_core/store/settings_store.dart';
import 'package:qfli_web/main.dart' show webProfile;
import 'package:qfli_web/pages/web_tools_overview.dart';

void main() {
  /// 用真实 stores 起一台 QfliApp，并注册完整的 teardown 清理。
  Future<
    ({
      ProjectStore store,
      AuthStore auth,
      SettingsStore settings,
      Directory temp,
    })
  >
  pumpApp(
    WidgetTester tester, {
    bool withProject = false,
    TextScaler? textScaler,
  }) async {
    final previous = StudioProfile.current;
    StudioProfile.current = webProfile;
    final temp = Directory.systemTemp.createTempSync('webforge-navigation-');
    final registry = File('${temp.path}/projects.json');
    if (withProject) {
      final projectDirectory = Directory('${temp.path}/site')..createSync();
      File(
        '${projectDirectory.path}/index.html',
      ).writeAsStringSync('<html></html>');
      registry.writeAsStringSync(
        jsonEncode({
          'version': 1,
          'projects': [
            Project.create(name: 'Site', path: projectDirectory.path).toJson(),
          ],
        }),
      );
    }
    final store = ProjectStore(storageFile: registry);
    if (withProject) await tester.runAsync(store.load);
    final auth = AuthStore();
    final settings = SettingsStore();
    addTearDown(() {
      StudioProfile.current = previous;
      store.dispose();
      auth.dispose();
      settings.dispose();
      temp.deleteSync(recursive: true);
    });
    await tester.pumpWidget(
      textScaler == null
          ? QfliApp(store: store, auth: auth, settings: settings)
          : MediaQuery(
              data: MediaQueryData(textScaler: textScaler),
              child: QfliApp(store: store, auth: auth, settings: settings),
            ),
    );
    await tester.pumpAndSettle();
    return (store: store, auth: auth, settings: settings, temp: temp);
  }

  /// 通过内核底部导航进入工具 tab。
  Future<void> openTools(WidgetTester tester) async {
    await tester.tap(find.byIcon(Icons.apps_outlined).first);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));
    // The inline resource panel now performs real asynchronous disk/isolate
    // work. Let that work advance outside the fake test clock before settling
    // the route and its loading animation.
    await tester.runAsync(() async {
      for (var attempt = 0; attempt < 500; attempt++) {
        await Future<void>.delayed(const Duration(milliseconds: 5));
        await tester.pump();
        if (find.byType(LinearProgressIndicator).evaluate().isEmpty) return;
      }
    });
    await tester.pumpAndSettle();
  }

  /// 切到目标页后推进几帧。教程/示例页含（或等待）内容加载，
  /// `pumpAndSettle` 可能一直不 settle，因此用有界的 pump 序列。
  Future<void> selectPage(WidgetTester tester, IconData icon) async {
    await tester.tap(find.byIcon(icon).first);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));
    await tester.pump(const Duration(milliseconds: 300));
  }

  testWidgets('tools tab is one integrated offline surface', (tester) async {
    await pumpApp(tester);
    await openTools(tester);

    // 工具 tab 本体即整合页面，不再有需要二次 push 的「Web 工具」入口卡片。
    expect(find.text('Web 工具'), findsNothing);
    expect(find.text('本地服务'), findsWidgets);
    expect(find.text('Web 编解码'), findsOneWidget);
    // 内核提供的终端入口仍在。
    expect(find.text('终端'), findsWidgets);

    // HTTP 工具是任意外部请求入口，离线产品下不可达。
    expect(find.text('HTTP'), findsNothing);
    expect(find.text('服务器'), findsNothing);
  });

  testWidgets('local server settings stay offline (no API proxy editor)', (
    tester,
  ) async {
    final app = await pumpApp(tester, withProject: true);
    await openTools(tester);
    await tester.tap(find.text('本地服务').first);
    await tester.pumpAndSettle();

    await tester.tap(find.byTooltip('项目服务设置'));
    await tester.pumpAndSettle();
    expect(find.text('SPA 路由回退'), findsOneWidget);
    // 代理会把请求转发到任意外部主机，离线产品不展示也不提供添加入口。
    expect(find.text('API 代理'), findsNothing);
    expect(find.byTooltip('添加代理'), findsNothing);

    await tester.tap(find.text('SPA 路由回退'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('保存'));
    await tester.pumpAndSettle();

    final projectDirectory = app.store.projects.first.path;
    final config =
        jsonDecode(File('$projectDirectory/.qfli/web.json').readAsStringSync())
            as Map<String, dynamic>;
    expect(config['spaFallback'], true);
    expect(config.containsKey('proxies'), isFalse);
  });

  testWidgets('pre-existing proxy rules are preserved when saving offline', (
    tester,
  ) async {
    final app = await pumpApp(tester, withProject: true);
    final projectDirectory = app.store.projects.first.path;
    final configFile = File('$projectDirectory/.qfli/web.json');
    configFile.parent.createSync(recursive: true);
    configFile.writeAsStringSync(
      jsonEncode({
        'spaFallback': false,
        'engine': 'auto',
        'proxies': [
          {'prefix': '/api', 'target': 'http://127.0.0.1:3000/'},
        ],
      }),
    );

    await openTools(tester);
    await tester.tap(find.text('本地服务').first);
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('项目服务设置'));
    await tester.pumpAndSettle();
    expect(find.text('API 代理'), findsNothing);
    await tester.tap(find.text('保存'));
    await tester.pumpAndSettle();

    final config =
        jsonDecode(configFile.readAsStringSync()) as Map<String, dynamic>;
    expect(config['proxies'], [
      {'prefix': '/api', 'target': 'http://127.0.0.1:3000/'},
    ]);
  });

  testWidgets('all five pages are reachable in order', (tester) async {
    await pumpApp(tester);
    // 首页：内核 NavigationBar 存在且选中首页。
    expect(find.byType(NavigationBar), findsOneWidget);

    await openTools(tester);
    expect(find.text('本地服务'), findsWidgets);

    await selectPage(tester, Icons.menu_book_outlined);
    expect(find.byIcon(Icons.code_outlined), findsWidgets);

    await selectPage(tester, Icons.code_outlined);
    expect(find.byIcon(Icons.person_outline), findsWidgets);

    await selectPage(tester, Icons.person_outline);
    // 离线产品下「我的」隐藏登录/账号区，但本地设置入口仍在。
    expect(find.text('设置'), findsOneWidget);
    expect(find.text('未登录'), findsNothing);

    await selectPage(tester, Icons.home_outlined);
    expect(find.byIcon(Icons.create_new_folder_outlined), findsWidgets);
  });

  // 完整工具面（整合后的 ToolsGrid）必须在窄屏 + 2.0 大字下正常布局。
  // 这是完整的正向回归：核心 ToolCard 的自适应缺陷修复前，它会如实失败；
  // 修复后即通过，无需任何反向哨兵。
  testWidgets('integrated tools grid survives narrow large-text viewport', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(320, 640);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);
    final app = await pumpApp(tester);

    await tester.pumpWidget(
      MaterialApp(
        home: MediaQuery(
          data: const MediaQueryData(textScaler: TextScaler.linear(2.0)),
          child: Scaffold(body: WebToolsOverview(store: app.store)),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    // 工具卡片确实渲染出来了，而不是空布局假通过。
    expect(find.text('本地服务'), findsOneWidget);
    expect(find.text('Web 编解码'), findsOneWidget);
  });

  // 完整外壳在窄屏 + 2.0 大字下逐页浏览，全程无布局异常。
  testWidgets('all five pages survive narrow large-text viewport', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(320, 640);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);
    await pumpApp(tester, textScaler: const TextScaler.linear(2.0));
    expect(tester.takeException(), isNull);

    await openTools(tester);
    expect(tester.takeException(), isNull);

    for (final icon in <IconData>[
      Icons.menu_book_outlined,
      Icons.code_outlined,
      Icons.person_outline,
      Icons.home_outlined,
    ]) {
      await selectPage(tester, icon);
      expect(tester.takeException(), isNull);
    }
  });
}
