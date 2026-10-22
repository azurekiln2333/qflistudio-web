import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/editor/editor_analysis_controller.dart';
import 'package:qfli_studio_core/editor/editor_page.dart';
import 'package:qfli_studio_core/editor/editor_problems_bar.dart';
import 'package:qfli_studio_core/editor/open_file.dart';
import 'package:qfli_studio_core/models/project.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/store/auth_store.dart';
import 'package:qfli_studio_core/store/project_store.dart';
import 'package:qfli_studio_core/store/settings_store.dart';
import 'package:qfli_web/main.dart' show webProfile;
import 'package:qfli_web/services/web_code_analyzer.dart';

/// Acceptance tests of the actual EditorPage and native compile-only parser.
/// No analyzer replacement or synthetic diagnostic is used.
void main() {
  for (final size in [const Size(1280, 900), const Size(390, 844)]) {
    testWidgets(
      'real Web analyzer drives unsaved Problems, waves and navigation at $size',
      (tester) async {
        final fixture = _EditorFixture();
        await fixture.mount(tester, size);
        final analysis = tester
            .widget<EditorProblemsBar>(find.byType(EditorProblemsBar))
            .analysis;
        await _waitForAnalysis(tester, analysis);
        expect(find.text('本地检查未发现问题'), findsOneWidget);
        expect(analysis.problems, isEmpty);

        final active = analysis.editor.current!;
        final controller = active.controller;
        const invalid = '// 😀\r\nconst text = "😀"; const broken = ;';
        controller.text = invalid;
        expect(controller.text, invalid);
        expect(active.dirty, isTrue);
        await _waitForAnalysis(tester, analysis);

        final problem = analysis.problems.single;
        final token = invalid.lastIndexOf(';');
        final line = invalid.split('\r\n').last;
        final column = line.lastIndexOf(';');
        expect(problem.filePath, fixture.source.path);
        expect(problem.startOffset, token);
        expect(problem.endOffset, token + 1);
        expect(problem.source, startsWith('QuickJS'));
        expect(problem.code, 'SyntaxError');
        expect(find.text('问题 1'), findsOneWidget);
        expect(fixture.source.readAsStringSync(), _savedSource);

        // This is the same public controller span API used by re_editor's
        // renderer, including the actual core-installed diagnostic decorator.
        final decorated = _lineSpan(tester, active, 1);
        expect(decorated.toPlainText(), line);
        final waves = _wavyLeaves(decorated);
        expect(waves.map((span) => span.text), [';']);
        expect(waves.single.style!.decoration, TextDecoration.underline);
        expect(
          waves.single.style!.decorationColor,
          Theme.of(
            tester.element(find.byType(EditorProblemsBar).first),
          ).colorScheme.error,
        );
        expect(_wavyLeaves(_lineSpan(tester, active, 0)), isEmpty);

        await tester.tap(find.byKey(const ValueKey('editor-problems-status')));
        await tester.pump();
        final panel = find.byType(EditorProblemsPanel);
        expect(panel, findsOneWidget);
        expect(
          find.descendant(of: panel, matching: find.text(problem.message)),
          findsOneWidget,
        );
        expect(
          find.descendant(
            of: panel,
            matching: find.textContaining('main.js:2:${column + 1}'),
          ),
          findsOneWidget,
        );
        final row = find.descendant(of: panel, matching: find.byType(ListTile));
        await tester.ensureVisible(row);
        await tester.tap(row);
        await tester.pump();
        expect(controller.selection.baseIndex, 1);
        expect(controller.selection.baseOffset, column);
        expect(controller.selection.extentIndex, 1);
        expect(controller.selection.extentOffset, column + 1);

        const repaired = '// 😀\r\nconst text = "😀"; const repaired = 42;';
        controller.text = repaired;
        await _waitForAnalysis(tester, analysis);
        expect(analysis.problems, isEmpty);
        expect(find.text('本地检查未发现问题'), findsWidgets);
        expect(find.text(problem.message), findsNothing);
        expect(_wavyLeaves(_lineSpan(tester, active, 1)), isEmpty);
        expect(controller.text, repaired);
        expect(active.dirty, isTrue);
        expect(fixture.source.readAsStringSync(), _savedSource);

        // Selecting another workspace owner must analyze that owner's exact
        // unsaved buffer and must not retain the previous file's diagnostics.
        expect(
          await tester.runAsync(
            () => analysis.editor.openPath(
              fixture.otherSource.path,
              ownerProjectName: 'Other site',
              ownerProjectPath: fixture.otherSource.parent.path,
              ownerProjectType: 'web',
            ),
          ),
          isNull,
        );
        final other = analysis.editor.current!;
        other.controller.text = '// 😀\r\nconst other = ;';
        await _waitForAnalysis(tester, analysis);
        expect(other.projectRootPath, fixture.otherSource.parent.path);
        expect(analysis.problems.single.filePath, fixture.otherSource.path);
        expect(
          analysis.problems.single.startOffset,
          other.controller.text.lastIndexOf(';'),
        );
        expect(fixture.otherSource.readAsStringSync(), _savedSource);

        analysis.editor.select(analysis.editor.files.indexOf(active));
        await _waitForAnalysis(tester, analysis);
        expect(analysis.editor.current, same(active));
        expect(controller.text, repaired);
        expect(analysis.problems, isEmpty);
        expect(find.text('本地检查未发现问题'), findsWidgets);
        expect(_wavyLeaves(_lineSpan(tester, active, 1)), isEmpty);
        expect(fixture.source.readAsStringSync(), _savedSource);
        expect(fixture.otherSource.readAsStringSync(), _savedSource);
        expect(tester.takeException(), isNull);
      },
    );
  }
}

const _savedSource = '// saved 😀\r\nconst saved = 1;\r\n';

TextSpan _lineSpan(WidgetTester tester, OpenFile file, int index) =>
    file.controller.buildTextSpan(
      context: tester.element(find.byType(EditorProblemsBar).first),
      index: index,
      textSpan: TextSpan(text: file.controller.codeLines[index].text),
      style: const TextStyle(),
    );

List<TextSpan> _wavyLeaves(TextSpan span) => [
  if (span.text != null &&
      span.style?.decorationStyle == TextDecorationStyle.wavy)
    span,
  for (final child in span.children ?? const <InlineSpan>[])
    if (child is TextSpan) ..._wavyLeaves(child),
];

Future<void> _waitForAnalysis(
  WidgetTester tester,
  EditorAnalysisController analysis,
) async {
  for (var attempt = 0; attempt < 300; attempt++) {
    await tester.pump(const Duration(milliseconds: 20));
    if (!analysis.pending) {
      expect(analysis.unavailableReason, isNull);
      expect(analysis.checked, isTrue);
      return;
    }
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 10)),
    );
  }
  fail('The real native editor analysis did not complete.');
}

class _EditorFixture {
  _EditorFixture() {
    final root = Directory(p.join(directory.path, 'site'))..createSync();
    source = File(p.join(root.path, 'main.js'))
      ..writeAsStringSync(_savedSource);
    final other = Directory(p.join(directory.path, 'other-site'))..createSync();
    otherSource = File(p.join(other.path, 'other.js'))
      ..writeAsStringSync(_savedSource);
    project = Project.create(
      name: 'Web analysis site',
      path: root.path,
      type: 'web',
      language: 'Web',
    );
    store = ProjectStore(
      storageFile: File(p.join(directory.path, 'projects.json')),
    );
    settings = SettingsStore(
      storageFile: File(p.join(directory.path, 'settings.json')),
    );
  }

  final directory = Directory.systemTemp.createTempSync('web-editor-analysis-');
  final auth = AuthStore();
  late final ProjectStore store;
  late final SettingsStore settings;
  late final File source;
  late final File otherSource;
  late final Project project;

  Future<void> mount(WidgetTester tester, Size size) async {
    final nativeLibrary = p.join(
      Directory.current.path,
      'build',
      'native',
      'web_syntax',
      Platform.isWindows
          ? 'windows'
          : Platform.isMacOS
          ? 'macos'
          : 'linux',
      Platform.isWindows
          ? 'qfli_web_syntax.dll'
          : Platform.isMacOS
          ? 'libqfli_web_syntax.dylib'
          : 'libqfli_web_syntax.so',
    );
    expect(File(nativeLibrary).existsSync(), isTrue);
    final previous = StudioProfile.current;
    StudioProfile.current = StudioProfile(
      id: webProfile.id,
      appTitle: webProfile.appTitle,
      templates: webProfile.templates,
      isOffline: webProfile.isOffline,
      offlineOnly: webProfile.offlineOnly,
      supportedFileExtensions: webProfile.supportedFileExtensions,
      codeAnalyzer: WebCodeAnalyzer(nativeLibraryPath: nativeLibrary),
    );
    expect(settings.autoSave, isFalse);
    tester.view.physicalSize = size;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(() async {
      await tester.pumpWidget(const SizedBox.shrink());
      StudioProfile.current = previous;
      auth.dispose();
      store.dispose();
      settings.dispose();
      // EditorPage persists tab history asynchronously on disposal. Alternate
      // real I/O and frame microtasks until Windows releases those file handles.
      for (var attempt = 0; attempt < 50; attempt++) {
        try {
          if (directory.existsSync()) directory.deleteSync(recursive: true);
          return;
        } on FileSystemException {
          if (attempt == 49) rethrow;
          await tester.pump(const Duration(milliseconds: 20));
          await tester.runAsync(
            () => Future<void>.delayed(const Duration(milliseconds: 20)),
          );
        }
      }
    });
    await tester.pumpWidget(
      MaterialApp(
        home: EditorPage(
          project: project,
          auth: auth,
          store: store,
          settings: settings,
          initialOpenPath: source.path,
        ),
      ),
    );
    for (var attempt = 0; attempt < 200; attempt++) {
      await tester.pump(const Duration(milliseconds: 20));
      if (find.byType(EditorProblemsBar).evaluate().isNotEmpty) return;
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 10)),
      );
    }
    fail('EditorPage did not open the JavaScript source.');
  }
}
