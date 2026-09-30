import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/content/asset_content_repository.dart';
import 'package:qfli_studio_core/content/local_content_adapter.dart';
import 'package:qfli_studio_core/editor/editor_controller.dart';
import 'package:qfli_studio_core/editor/editor_page.dart';
import 'package:qfli_studio_core/i18n/studio_localizations.dart';
import 'package:qfli_studio_core/models/project.dart';
import 'package:qfli_studio_core/pages/home_page.dart';
import 'package:qfli_studio_core/pages/local_content_pages.dart';
import 'package:qfli_studio_core/services/code_import_service.dart';
import 'package:qfli_studio_core/services/project_config.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/store/auth_store.dart';
import 'package:qfli_studio_core/store/project_store.dart';
import 'package:qfli_studio_core/store/settings_store.dart';
import 'package:qfli_studio_core/theme/app_theme.dart';
import 'package:qfli_studio_core/widgets/code_snippet.dart';
import 'package:qfli_web/main.dart' show webProfile;
import 'package:qfli_web/services/web_runtime.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('bundled content imports, opens custom files and previews HTML', (
    tester,
  ) async {
    StudioProfile.current = webProfile;
    final directory = await Directory.systemTemp.createTemp('webforge-import-');
    final projects = ProjectStore(
      storageFile: File(p.join(directory.path, 'projects.json')),
    );
    final auth = AuthStore(
      storageFile: File(p.join(directory.path, 'auth.json')),
    );
    final settings = SettingsStore(
      storageFile: File(p.join(directory.path, 'settings.json')),
    );
    await Future.wait([projects.load(), auth.load(), settings.load()]);
    addTearDown(() async {
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pumpAndSettle();
      final imported = projects.projects.toList();
      projects.dispose();
      auth.dispose();
      settings.dispose();
      for (final project in imported) {
        await Directory(project.path).delete(recursive: true);
      }
      await directory.delete(recursive: true);
      StudioProfile.current = null;
    });

    final repository = AssetContentRepository();
    final tutorial = (await LocalContentAdapter.loadTutorial(
      repository: repository,
      language: 'web',
      displayName: webProfile.appTitle,
      productKey: webProfile.productKey,
    ))!;
    final examples = await LocalContentAdapter.loadExamples(
      repository: repository,
      language: 'web',
      productKey: webProfile.productKey,
    );
    final lesson = tutorial.chapters.first.lessons.first;
    final example = examples.first;
    var sequence = 0;
    Project? existing;

    for (final examplePage in [false, true]) {
      for (final intoProject in [false, true]) {
        debugPrint(
          'CONTENT_IMPORT ${examplePage ? 'example' : 'lesson'} ${intoProject ? 'project' : 'editor'}',
        );
        await tester.pumpWidget(
          _app(
            HomePage(store: projects, auth: auth, settings: settings),
            sequence++,
          ),
        );
        await tester.pumpAndSettle();
        final l10n = StudioLocalizations.of(
          tester.element(find.byType(HomePage)),
        );
        await tester.tap(
          find.descendant(
            of: find.byType(NavigationBar),
            matching: find.text(examplePage ? l10n.examples : l10n.tutorial),
          ),
        );
        final title = examplePage ? example.title : lesson.title;
        await _waitFor(tester, () => find.text(title).evaluate().isNotEmpty);
        expect(find.byType(CodeSnippet), findsNothing);
        await tester.pumpAndSettle();
        await tester.tap(find.text(title).first);
        await tester.pumpAndSettle();
        final type = examplePage ? example.type : lesson.type;
        final code = examplePage ? example.code : lesson.code;
        final fileName =
            'android_${sequence}_${CodeImportService.suggestedFileName(type)}';
        await _import(tester, intoProject: intoProject, fileName: fileName);
        final opened = await _opened(tester, fileName, code);
        expect(projects.projects.any((p) => p.id == opened.id), isTrue);
        existing ??= opened;
      }
    }

    // This detail is loaded from the same packaged catalog as the HomePage.
    final html = examples.firstWhere((example) => example.type == 'html');
    final edited = '${html.code}\n<!-- Android edited import -->\n';
    await tester.pumpWidget(
      _app(
        ExampleDetailPage(
          example: html,
          store: projects,
          auth: auth,
          settings: settings,
        ),
        sequence++,
      ),
    );
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), edited);
    await _import(tester, intoProject: true, fileName: 'custom_preview.html');
    final htmlProject = await _opened(tester, 'custom_preview.html', edited);
    expect(
      ProjectConfig.read(htmlProject.path)?['entryFile'],
      'src/custom_preview.html',
    );
    final session = await WebRuntime.start(htmlProject.path);
    try {
      expect(session.engineName, startsWith('Nginx '));
      final client = HttpClient();
      try {
        final response = await (await client.getUrl(
          Uri.parse(session.url),
        )).close();
        expect(response.statusCode, HttpStatus.ok);
        expect(
          await utf8.decoder.bind(response).join(),
          contains('Android edited import'),
        );
      } finally {
        client.close(force: true);
      }
    } finally {
      await session.stop();
    }

    await tester.pumpWidget(
      _app(
        ExampleDetailPage(
          example: html,
          store: projects,
          auth: auth,
          settings: settings,
        ),
        sequence++,
      ),
    );
    await tester.pumpAndSettle();
    final oldEntry = ProjectConfig.read(existing!.path)?['entryFile'];
    final oldCount = projects.projects.length;
    await _import(
      tester,
      intoProject: true,
      fileName: 'existing_import.html',
      target: existing,
    );
    final opened = await _opened(tester, 'existing_import.html', html.code);
    expect(opened.id, existing.id);
    expect(projects.projects.length, oldCount);
    expect(ProjectConfig.read(existing.path)?['entryFile'], oldEntry);
    expect(tester.takeException(), isNull);
  });
}

MaterialApp _app(Widget home, int sequence) => MaterialApp(
  key: ValueKey(sequence),
  locale: const Locale('en'),
  localizationsDelegates: const [StudioLocalizations.delegate],
  theme: AppTheme.light,
  home: home,
);

Future<void> _import(
  WidgetTester tester, {
  required bool intoProject,
  required String fileName,
  Project? target,
}) async {
  final l10n = StudioLocalizations.of(tester.element(find.byType(CodeSnippet)));
  final command = find.byTooltip(
    intoProject ? l10n.importCodeProject : l10n.importCodeEditor,
  );
  await tester.ensureVisible(command);
  await tester.pumpAndSettle();
  expect(command.hitTestable(), findsOneWidget);
  await tester.tap(command);
  await tester.pumpAndSettle();
  expect(find.byKey(const ValueKey('import-file-name')), findsOneWidget);
  if (target != null) {
    await tester.tap(find.byKey(const ValueKey('import-target-project')));
    await tester.pumpAndSettle();
    await tester.tap(find.text(target.name).last);
    await tester.pumpAndSettle();
  }
  await tester.enterText(
    find.byKey(const ValueKey('import-file-name')),
    fileName,
  );
  FocusManager.instance.primaryFocus?.unfocus();
  await tester.pumpAndSettle();
  final confirm = find.byKey(const ValueKey('import-code-confirm'));
  await tester.ensureVisible(confirm);
  await tester.pumpAndSettle();
  expect(confirm.hitTestable(), findsOneWidget);
  await tester.tap(confirm);
  await tester.pump();
}

Future<Project> _opened(
  WidgetTester tester,
  String fileName,
  String code,
) async {
  await _waitFor(tester, () => find.byType(EditorPage).evaluate().isNotEmpty);
  await tester.pumpAndSettle();
  final editor = tester.widget<EditorPage>(find.byType(EditorPage));
  final path = p.join(editor.project.path, 'src', fileName);
  expect(editor.initialOpenPath, path);
  expect(await File(path).readAsString(), code);
  await _waitFor(tester, () {
    final controllers = tester
        .widgetList<ListenableBuilder>(find.byType(ListenableBuilder))
        .map((widget) => widget.listenable)
        .whereType<EditorController>();
    return controllers.any(
      (controller) =>
          controller.current?.path == path &&
          controller.current?.controller.text.replaceAll('\r\n', '\n') == code,
    );
  });
  expect(find.byType(AlertDialog), findsNothing);
  return editor.project;
}

Future<void> _waitFor(WidgetTester tester, bool Function() condition) async {
  final deadline = DateTime.now().add(const Duration(seconds: 30));
  while (!condition() && DateTime.now().isBefore(deadline)) {
    await tester.pump(const Duration(milliseconds: 100));
  }
  expect(
    condition(),
    isTrue,
    reason: 'Import UI did not reach its expected state',
  );
}
