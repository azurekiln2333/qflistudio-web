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

void main() {
  testWidgets('Functions navigation opens the working Web tools', (
    tester,
  ) async {
    final previous = StudioProfile.current;
    StudioProfile.current = webProfile;
    final temp = Directory.systemTemp.createTempSync('webforge-navigation-');
    final store = ProjectStore(storageFile: File('${temp.path}/projects.json'));
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
      QfliApp(store: store, auth: auth, settings: settings),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byIcon(Icons.apps_outlined).first);
    await tester.pumpAndSettle();
    expect(find.text('Web 工具'), findsOneWidget);

    await tester.tap(find.text('Web 工具'));
    await tester.pumpAndSettle();
    expect(find.text('服务器'), findsOneWidget);
    expect(find.text('HTTP'), findsOneWidget);
    expect(find.text('编解码'), findsOneWidget);
  });

  testWidgets('project server settings are saved through the UI', (
    tester,
  ) async {
    final previous = StudioProfile.current;
    StudioProfile.current = webProfile;
    final temp = Directory.systemTemp.createTempSync('webforge-settings-');
    final projectDirectory = Directory('${temp.path}/site')..createSync();
    File(
      '${projectDirectory.path}/index.html',
    ).writeAsStringSync('<html></html>');
    final project = Project.create(name: 'Site', path: projectDirectory.path);
    final registry = File('${temp.path}/projects.json');
    registry.writeAsStringSync(
      jsonEncode({
        'version': 1,
        'projects': [project.toJson()],
      }),
    );
    final store = ProjectStore(storageFile: registry);
    await tester.runAsync(store.load);
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
      QfliApp(store: store, auth: auth, settings: settings),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byIcon(Icons.apps_outlined).first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Web 工具'));
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('项目服务设置'));
    await tester.pumpAndSettle();
    expect(
      find.text('SPA 路由回退'),
      findsOneWidget,
      reason: tester
          .widgetList<Text>(find.byType(Text))
          .map((text) => text.data)
          .join(' | '),
    );
    await tester.tap(find.text('SPA 路由回退'));
    await tester.tap(find.text('自动'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('WebForge').last);
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('添加代理'));
    await tester.pumpAndSettle();
    await tester.enterText(find.widgetWithText(TextField, '路径前缀'), '/api');
    await tester.enterText(
      find.widgetWithText(TextField, '目标 URL'),
      'http://127.0.0.1:3000/',
    );
    await tester.tap(find.text('保存'));
    await tester.pumpAndSettle();

    final config =
        jsonDecode(
              File(
                '${projectDirectory.path}/.qfli/web.json',
              ).readAsStringSync(),
            )
            as Map<String, dynamic>;
    expect(config['spaFallback'], true);
    expect(config['engine'], 'webforge');
    expect(config['proxies'], [
      {'prefix': '/api', 'target': 'http://127.0.0.1:3000/'},
    ]);
  });
}
