import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qfli_studio_core/app.dart';
import 'package:qfli_studio_core/layout/app_form_factor.dart';
import 'package:qfli_studio_core/models/project.dart';
import 'package:qfli_studio_core/pages/home_page.dart';
import 'package:qfli_studio_core/pages/local_content_pages.dart';
import 'package:qfli_studio_core/pages/profile_page.dart';
import 'package:qfli_studio_core/pages/settings_page.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/shell/large_screen_workbench.dart';
import 'package:qfli_studio_core/shell/workbench_chrome.dart';
import 'package:qfli_studio_core/store/auth_store.dart';
import 'package:qfli_studio_core/store/project_store.dart';
import 'package:qfli_studio_core/store/settings_store.dart';
import 'package:qfli_web/content/webforge_content_repository.dart';
import 'package:qfli_web/main.dart' show webProfile;
import 'package:qfli_web/pages/web_tools_overview.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late Map<String, ByteData> assetBytes;
  final assetRequests = <String>[];

  setUpAll(() {
    final tutorials = File(
      WebForgeContentRepository.tutorialAsset,
    ).readAsBytesSync();
    final examples = File(
      WebForgeContentRepository.exampleAsset,
    ).readAsBytesSync();
    assetBytes = {
      WebForgeContentRepository.tutorialAsset: ByteData.sublistView(tutorials),
      WebForgeContentRepository.exampleAsset: ByteData.sublistView(examples),
    };
  });

  setUp(() {
    assetRequests.clear();
    rootBundle.clear();
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMessageHandler('flutter/assets', (message) async {
          if (message == null) return null;
          final key = utf8.decode(
            message.buffer.asUint8List(
              message.offsetInBytes,
              message.lengthInBytes,
            ),
          );
          assetRequests.add(key);
          const productPrefix = 'packages/qfli_web/';
          final asset = key.startsWith(productPrefix)
              ? key.substring(productPrefix.length)
              : key;
          return assetBytes[asset];
        });
  });

  tearDown(() {
    rootBundle.clear();
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMessageHandler('flutter/assets', null);
  });

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
    AppFormFactor formFactor = AppFormFactor.phone,
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
    final auth = AuthStore(storageFile: File('${temp.path}/auth.json'));
    final settings = SettingsStore(
      storageFile: File('${temp.path}/settings.json'),
    );
    addTearDown(() async {
      await tester.pumpWidget(const SizedBox.shrink());
      StudioProfile.current = previous;
      store.dispose();
      auth.dispose();
      settings.dispose();
      temp.deleteSync(recursive: true);
    });
    if (textScaler != null) {
      tester.platformDispatcher.textScaleFactorTestValue = textScaler.scale(1);
      addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
    }
    await tester.pumpWidget(
      QfliApp(
        store: store,
        auth: auth,
        settings: settings,
        formFactor: formFactor,
      ),
    );
    await tester.pumpAndSettle();
    if (formFactor == AppFormFactor.phone) {
      expect(find.byType(HomePage), findsOneWidget);
      expect(find.byType(LargeScreenWorkbench), findsNothing);
    } else {
      expect(find.byType(LargeScreenWorkbench), findsOneWidget);
      expect(find.byType(HomePage), findsNothing);
      expect(find.byType(NavigationBar), findsNothing);
    }
    if (textScaler != null) {
      final shell = formFactor == AppFormFactor.phone
          ? find.byType(HomePage)
          : find.byType(LargeScreenWorkbench);
      expect(
        MediaQuery.textScalerOf(tester.element(shell)).scale(10),
        textScaler.scale(10),
      );
    }
    return (store: store, auth: auth, settings: settings, temp: temp);
  }

  /// 切到目标页后推进几帧。教程/示例页含（或等待）内容加载，
  /// `pumpAndSettle` 可能一直不 settle，因此用有界的 pump 序列。
  Future<void> selectPage(WidgetTester tester, IconData icon) async {
    final destination = find.descendant(
      of: find.byType(NavigationBar),
      matching: find.byIcon(icon),
    );
    expect(destination.hitTestable(), findsOneWidget);
    await tester.tap(destination);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));
    await tester.pump(const Duration(milliseconds: 300));
  }

  /// Use each shell's real navigation entry, even in a narrow desktop window.
  Future<void> openTools(WidgetTester tester) async {
    if (find.byType(LargeScreenWorkbench).evaluate().isNotEmpty) {
      await tester.tap(
        find.byKey(WorkbenchActivityRail.activityKey(WorkbenchActivity.tools)),
      );
    } else {
      await selectPage(tester, Icons.apps_outlined);
    }
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));
    // The inline resource panel now performs real asynchronous disk/isolate
    // work. Let that work advance outside the fake test clock before settling
    // the route and its loading animation.
    for (var attempt = 0; attempt < 500; attempt++) {
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 5)),
      );
      await tester.pump();
      if (find.byType(LinearProgressIndicator).evaluate().isEmpty) break;
    }
    expect(find.byType(LinearProgressIndicator), findsNothing);
    await tester.pumpAndSettle();
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

  testWidgets('all four main pages and both content tabs are reachable', (
    tester,
  ) async {
    await pumpApp(tester);
    final navigation = tester.widget<NavigationBar>(find.byType(NavigationBar));
    expect(navigation.destinations, hasLength(4));
    expect(navigation.selectedIndex, 0);
    expect(
      find.descendant(
        of: find.byType(NavigationBar),
        matching: find.byIcon(Icons.code_outlined),
      ),
      findsNothing,
      reason: 'Examples belong to the content center, not a fifth main page.',
    );

    await openTools(tester);
    expect(find.text('本地服务'), findsWidgets);
    expect(
      tester.widget<NavigationBar>(find.byType(NavigationBar)).selectedIndex,
      1,
    );

    await selectPage(tester, Icons.menu_book_outlined);
    await _expectContentSections(tester, assetRequests);
    expect(
      tester.widget<NavigationBar>(find.byType(NavigationBar)).selectedIndex,
      2,
    );

    await selectPage(tester, Icons.person_outline);
    expect(
      tester.widget<NavigationBar>(find.byType(NavigationBar)).selectedIndex,
      3,
    );
    await _expectOfflineSettings(tester);

    await selectPage(tester, Icons.home_outlined);
    expect(
      tester.widget<NavigationBar>(find.byType(NavigationBar)).selectedIndex,
      0,
    );
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

  // Explicit phone form factor keeps this distinct from a narrow desktop.
  testWidgets('all four phone pages survive 320px with 2x text', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(320, 640);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);
    await pumpApp(tester, textScaler: const TextScaler.linear(2.0));
    expect(tester.takeException(), isNull);

    await openTools(tester);
    expect(tester.takeException(), isNull);

    await selectPage(tester, Icons.menu_book_outlined);
    await _expectContentSections(tester, assetRequests);
    expect(tester.takeException(), isNull);
    await selectPage(tester, Icons.person_outline);
    await _expectOfflineSettings(tester);
    expect(tester.takeException(), isNull);
    await selectPage(tester, Icons.home_outlined);
    expect(find.byIcon(Icons.create_new_folder_outlined), findsWidgets);
    expect(tester.takeException(), isNull);
  });

  testWidgets('320px desktop keeps workbench navigation with 2x text', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(320, 640);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await pumpApp(
      tester,
      formFactor: AppFormFactor.desktop,
      textScaler: const TextScaler.linear(2),
    );
    expect(find.byType(NavigationBar), findsNothing);
    expect(find.byType(WorkbenchActivityRail), findsOneWidget);
    expect(
      tester.widget<NavigationRail>(find.byType(NavigationRail)).destinations,
      hasLength(4),
    );
    await openTools(tester);
    expect(find.text('本地服务'), findsWidgets);
    expect(find.text('Web 编解码'), findsOneWidget);
    expect(find.text('HTTP'), findsNothing);
    expect(find.text('服务器'), findsNothing);
    expect(tester.takeException(), isNull);

    await tester.tap(
      find.byKey(WorkbenchActivityRail.activityKey(WorkbenchActivity.tutorial)),
    );
    await tester.pump();
    await _expectContentSections(tester, assetRequests);
    expect(tester.takeException(), isNull);
    await tester.tap(find.byKey(WorkbenchActivityRail.avatarKey));
    await tester.pump();
    await _expectOfflineSettings(tester);
    await tester.tap(
      find.byKey(WorkbenchActivityRail.activityKey(WorkbenchActivity.settings)),
    );
    await tester.pump();
    expect(find.byType(SettingsPage), findsOneWidget);
    await tester.tap(
      find.byKey(WorkbenchActivityRail.activityKey(WorkbenchActivity.explorer)),
    );
    await tester.pump();
    expect(find.byType(HomeTab), findsOneWidget);
    expect(find.byType(NavigationBar), findsNothing);
    expect(tester.takeException(), isNull);
  });
}

Future<void> _expectContentSections(
  WidgetTester tester,
  List<String> assetRequests,
) async {
  final center = find.byType(TutorialCenterPage);
  expect(center, findsOneWidget);
  for (final section in TutorialCenterSection.values) {
    final key = section == TutorialCenterSection.tutorial
        ? TutorialCenterPage.tutorialSectionKey
        : TutorialCenterPage.examplesSectionKey;
    final tab = find.descendant(of: center, matching: find.byKey(key));
    await tester.ensureVisible(tab);
    expect(tab.hitTestable(), findsOneWidget);
    await tester.tap(tab);
    await tester.pump();
    for (var attempt = 0; attempt < 500; attempt++) {
      final loaded = find.descendant(
        of: center,
        matching: find.byKey(const ValueKey('content-language-all')),
      );
      if (loaded.evaluate().isNotEmpty) break;
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 10)),
      );
      await tester.pump(const Duration(milliseconds: 20));
    }
    expect(
      find.descendant(
        of: center,
        matching: find.byKey(const ValueKey('content-language-all')),
      ),
      findsOneWidget,
      reason: 'The real ${section.name} catalog must load.',
    );
    final tabs = tester.widget<TabBar>(
      find.byKey(const ValueKey('tutorial-center-sections')),
    );
    expect(tabs.controller!.index, section.index);
    expect(
      find.descendant(
        of: center,
        matching: find.byType(CircularProgressIndicator),
      ),
      findsNothing,
    );
  }
  _expectWebForgeAssetRequests(assetRequests);
}

void _expectWebForgeAssetRequests(List<String> requests) {
  for (final asset in [
    WebForgeContentRepository.tutorialAsset,
    WebForgeContentRepository.exampleAsset,
  ]) {
    expect(requests, contains('packages/qfli_web/$asset'));
  }
  expect(
    requests.where((key) => key.contains('packages/qfli_studio_core/assets/')),
    isEmpty,
  );
}

Future<void> _expectOfflineSettings(WidgetTester tester) async {
  final profile = find.byType(ProfileTab);
  expect(profile, findsOneWidget);
  final settings = find.descendant(
    of: profile,
    matching: find.widgetWithText(ListTile, '设置'),
  );
  await tester.scrollUntilVisible(
    settings,
    200,
    scrollable: find.descendant(of: profile, matching: find.byType(Scrollable)),
  );
  expect(settings.hitTestable(), findsOneWidget);
  expect(find.text('未登录'), findsNothing);
  expect(find.text('退出登录'), findsNothing);
  await tester.tap(settings);
  await tester.pumpAndSettle();
  expect(find.byType(SettingsPage), findsOneWidget);
  await tester.pageBack();
  await tester.pumpAndSettle();
}
