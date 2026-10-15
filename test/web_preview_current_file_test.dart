import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/editor/editor_page.dart';
import 'package:qfli_studio_core/models/project.dart';
import 'package:qfli_studio_core/services/local_web_server.dart';
import 'package:qfli_studio_core/services/project_config.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/services/web_preview_file.dart';
import 'package:qfli_studio_core/store/auth_store.dart';
import 'package:qfli_studio_core/store/project_store.dart';
import 'package:qfli_studio_core/store/settings_store.dart';
import 'package:qfli_web/services/nginx_session.dart';
import 'package:qfli_web/services/web_dev_server.dart';
import 'package:qfli_web/services/web_runtime.dart';

import 'web_dev_server_test.dart' show request;

/// Current-file preview: long press resolves the active HTML through the
/// session's real document root, a tap keeps the default entry, and every
/// failure is explicit instead of silently substituting the default page.
///
/// The HTTP groups prove real page serving. The widget group only proves URL
/// selection and failure cleanup in the shared editor; it is not a browser
/// end-to-end test.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late Directory project;
  late HttpOverrides? savedOverrides;

  setUp(() {
    savedOverrides = HttpOverrides.current;
    HttpOverrides.global = null;
    project = Directory.systemTemp.createTempSync('webforge-current-');
  });

  tearDown(() {
    HttpOverrides.global = savedOverrides;
    if (project.existsSync()) project.deleteSync(recursive: true);
  });

  void write(String relative, String body) {
    final file = File(p.join(project.path, relative));
    file.parent.createSync(recursive: true);
    file.writeAsStringSync(body);
  }

  String abs(String relative) => p.join(project.path, relative);

  group('WebDevServer current-file preview', () {
    test(
      'index -> main2 -> index over real HTTP without config rewrite',
      () async {
        // Unique markers so the injected debug bridge cannot satisfy a contains.
        write('index.html', '<h1>INDEX-ENTRY-7f3a</h1>');
        write('main2.html', '<h1>MAIN2-ENTRY-91cd</h1>');
        const projectConfig = '{"version":1,"entryFile":"index.html"}';
        const webConfig = '{"spaFallback":false,"port":0}';
        write('.qfli/project.json', projectConfig);
        write('.qfli/web.json', webConfig);

        final server = await WebDevServer.start(project.path);
        addTearDown(server.stop);

        // Tap: the session URL keeps the default entry.
        final index = await request(server.url);
        expect(index.status, HttpStatus.ok);
        expect(index.body, contains('INDEX-ENTRY-7f3a'));
        expect(index.body, isNot(contains('MAIN2-ENTRY-91cd')));

        // Long press: the active file resolves to its own URL.
        final main2Url = server.urlForFile(abs('main2.html'));
        expect(main2Url, '${server.url}main2.html');
        final main2 = await request(main2Url);
        expect(main2.status, HttpStatus.ok);
        expect(main2.body, contains('MAIN2-ENTRY-91cd'));
        expect(main2.body, isNot(contains('INDEX-ENTRY-7f3a')));

        // A later tap still serves the default entry.
        final again = await request(server.url);
        expect(again.status, HttpStatus.ok);
        expect(again.body, contains('INDEX-ENTRY-7f3a'));

        // Neither persisted configuration was touched.
        expect(
          File(abs('.qfli/project.json')).readAsStringSync(),
          projectConfig,
        );
        expect(File(abs('.qfli/web.json')).readAsStringSync(), webConfig);
      },
    );

    test(
      'src-derived root and explicit root resolve the selected file',
      () async {
        write('src/index.html', '<h1>SRC-INDEX-2b41</h1>');
        write('src/main2.html', '<h1>SRC-MAIN2-6e08</h1>');
        final derived = await WebDevServer.start(project.path);
        addTearDown(derived.stop);
        expect(derived.config.root, p.join(project.path, 'src'));
        final derivedUrl = derived.urlForFile(abs('src/main2.html'));
        expect(derivedUrl, '${derived.url}main2.html');
        final derivedPage = await request(derivedUrl);
        expect(derivedPage.status, HttpStatus.ok);
        expect(derivedPage.body, contains('SRC-MAIN2-6e08'));

        // Explicit root elsewhere: the resolver follows the configured root.
        final explicitProject = Directory.systemTemp.createTempSync(
          'webforge-explicit-',
        );
        addTearDown(() => explicitProject.deleteSync(recursive: true));
        final build = Directory(p.join(explicitProject.path, 'build'))
          ..createSync(recursive: true);
        File(
          p.join(build.path, 'index.html'),
        ).writeAsStringSync('BUILD-INDEX-a1');
        File(
          p.join(build.path, 'page.html'),
        ).writeAsStringSync('BUILD-PAGE-b2');
        File(p.join(explicitProject.path, '.qfli', 'web.json'))
          ..createSync(recursive: true)
          ..writeAsStringSync('{"root":"build"}');
        final explicit = await WebDevServer.start(explicitProject.path);
        addTearDown(explicit.stop);
        expect(explicit.config.root, p.join(explicitProject.path, 'build'));
        final explicitUrl = explicit.urlForFile(
          p.join(build.path, 'page.html'),
        );
        expect(explicitUrl, '${explicit.url}page.html');
        final explicitPage = await request(explicitUrl);
        expect(explicitPage.status, HttpStatus.ok);
        expect(explicitPage.body, contains('BUILD-PAGE-b2'));
      },
    );

    test(
      'nested, space, CJK, hash and percent names resolve and serve',
      () async {
        write('index.html', 'index');
        final cases = {
          'deep/nested/x.html': 'NESTED-c31',
          'has space.html': 'SPACE-d47',
          '中文.html': 'CJK-e59',
          'a#b.html': 'HASH-f62',
          'a%b.html': 'PERCENT-07a',
        };
        cases.forEach(write);
        final server = await WebDevServer.start(project.path);
        addTearDown(server.stop);

        for (final entry in cases.entries) {
          final url = server.urlForFile(abs(entry.key));
          final result = await request(url);
          expect(result.status, HttpStatus.ok, reason: url);
          expect(result.body, contains(entry.value), reason: url);
        }
        // Encoding is delegated to Uri: no double encoding of '%' or '#'.
        expect(server.urlForFile(abs('a%b.html')), '${server.url}a%25b.html');
        expect(server.urlForFile(abs('a#b.html')), '${server.url}a%23b.html');
      },
    );

    test('missing, directory, outside-root and hidden targets fail', () async {
      write('index.html', 'index');
      write('.hidden/secret.html', 'secret');
      Directory(abs('adir')).createSync(recursive: true);
      final outside = Directory.systemTemp.createTempSync('webforge-outside-');
      addTearDown(() => outside.deleteSync(recursive: true));
      final outsideFile = File(p.join(outside.path, 'out.html'))
        ..writeAsStringSync('out');

      final server = await WebDevServer.start(project.path);
      addTearDown(server.stop);

      expect(
        () => server.urlForFile(abs('missing.html')),
        throwsA(isA<FileSystemException>()),
      );
      expect(
        () => server.urlForFile(abs('adir')),
        throwsA(isA<FileSystemException>()),
      );
      expect(
        () => server.urlForFile(outsideFile.path),
        throwsA(isA<FileSystemException>()),
      );
      expect(
        () => server.urlForFile(abs('.hidden/secret.html')),
        throwsA(isA<FileSystemException>()),
      );
    });

    test('resolved assets succeed and stop releases the listener', () async {
      write('index.html', 'index');
      write('main2.html', '<link rel="stylesheet" href="style.css">');
      write('style.css', 'body { color: red; }');
      final server = await WebDevServer.start(project.path);
      final pageUrl = server.urlForFile(abs('main2.html'));
      expect((await request(pageUrl)).status, HttpStatus.ok);
      final assetUrl = Uri.parse(pageUrl).resolve('style.css').toString();
      expect((await request(assetUrl)).body, contains('red'));

      final port = Uri.parse(server.url).port;
      await server.stop();
      await expectLater(
        () async => request('http://127.0.0.1:$port/'),
        throwsA(isA<SocketException>()),
      );
    });
  });

  group('Core LocalWebServer current-file preview', () {
    test('resolves and serves a selected file over real HTTP', () async {
      write('index.html', '<h1>LOCAL-INDEX-4c8</h1>');
      write('main2.html', '<h1>LOCAL-MAIN2-9d1</h1>');
      final server = await LocalWebServer.start(project.path);
      addTearDown(server.stop);

      final main2Url = server.urlForFile(abs('main2.html'));
      expect(main2Url, 'http://127.0.0.1:${server.port}/main2.html');
      final page = await request(main2Url);
      expect(page.status, HttpStatus.ok);
      expect(page.body, contains('LOCAL-MAIN2-9d1'));

      expect(
        () => server.urlForFile(abs('missing.html')),
        throwsA(isA<FileSystemException>()),
      );
    });
  });

  group('NginxSession current-file preview', () {
    test(
      'explicit root public URL and engine header serve the selected file',
      () async {
        final executable = await WebRuntime.nginxExecutable();
        if (executable == null) {
          markTestSkipped('native Nginx binary not available');
          return;
        }
        // An explicit root that is not the project root, so a wrong
        // project-relative prefix would fail the assertion below.
        write('public/index.html', '<h1>PUBLIC-INDEX-11e</h1>');
        write('public/main2.html', '<h1>PUBLIC-MAIN2-22f</h1>');
        write('public/style.css', 'body { color: blue; }');
        write('index.html', '<h1>PROJECT-ROOT-WRONG-33a</h1>');
        write('.qfli/web.json', '{"engine":"nginx","root":"public"}');

        final session = await NginxSession.start(
          project.path,
          executable: executable,
        );
        addTearDown(session.stop);

        expect(session.engineName, startsWith('Nginx'));
        final main2Url = session.urlForFile(abs('public/main2.html'));
        expect(main2Url, '${session.url}main2.html');
        final page = await request(main2Url);
        expect(page.status, HttpStatus.ok);
        expect(page.body, contains('PUBLIC-MAIN2-22f'));
        expect(page.body, isNot(contains('PROJECT-ROOT-WRONG-33a')));
        expect(
          page.headers.value('x-webforge-engine'),
          'nginx',
          reason: 'public listener must be nginx',
        );

        // A relative asset resolves and serves through the same public port.
        final asset = await request(
          Uri.parse(main2Url).resolve('style.css').toString(),
        );
        expect(asset.status, HttpStatus.ok);
        expect(asset.body, contains('blue'));
      },
    );
  });

  group('URL-selection and failure-cleanup', () {
    late _PreviewFixture fixture;

    setUp(() {
      fixture = _PreviewFixture();
    });

    tearDown(() async {
      StudioProfile.current = fixture.previousProfile;
      await fixture.dispose();
    });

    testWidgets('tap reads the default URL, long press resolves the file', (
      tester,
    ) async {
      await fixture.mount(tester);
      final run = find.byTooltip(_runTooltip);

      // Tap: only the default URL is read; no per-file resolution happens.
      await tester.tap(run);
      await fixture.waitForStopped(tester, 1);
      final tapped = fixture.sessions[0];
      expect(tapped.defaultRead, isTrue);
      expect(tapped.receivedPath, isNull);
      expect(tapped.stopCount, 1);

      // Long press: the active file is resolved through the session.
      await tester.longPress(run);
      await fixture.waitForStopped(tester, 2);
      final pressed = fixture.sessions[1];
      expect(pressed.receivedPath, p.join(fixture.project.path, 'main2.html'));
      expect(pressed.returnedTarget, isNotNull);
      expect(pressed.stopCount, 1);

      // A later tap again keeps the default entry.
      await tester.tap(run);
      await fixture.waitForStopped(tester, 3);
      expect(fixture.sessions[2].defaultRead, isTrue);
      expect(fixture.sessions[2].receivedPath, isNull);
      expect(fixture.sessions[2].stopCount, 1);

      // The project configuration was never rewritten by a run.
      expect(
        File(ProjectConfig.configPath(fixture.project.path)).readAsStringSync(),
        _projectConfigText,
      );
      expect(tester.takeException(), isNull);
    });

    testWidgets('a session failing to resolve is stopped', (tester) async {
      // The session throws from urlForFile, so the editor must stop it before
      // surfacing the error and must not leave it referenced.
      fixture.failResolution = true;
      await fixture.mount(tester);

      await tester.longPress(find.byTooltip(_runTooltip));
      await fixture.waitForStopped(tester, 1);

      final session = fixture.sessions.single;
      expect(session.receivedPath, p.join(fixture.project.path, 'main2.html'));
      expect(session.stopCount, 1);
      expect(tester.takeException(), isNull);
    });
  });
}

const _runTooltip = '运行（长按运行当前文件）';
const _projectConfigText = '{"version":1,"entryFile":"index.html"}';

/// A fake preview session that records how the editor selected a URL.
///
/// [debugStream] always throws [StateError] so the run flow ends before any
/// browser launch; this is a URL-selection and cleanup test, not a browser
/// end-to-end test. Real page serving is covered by the HTTP groups above.
class _RecordingPreviewSession implements WebFilePreviewSession {
  _RecordingPreviewSession({required String baseUrl, required this.projectPath})
    : _baseUrl = baseUrl;

  final String projectPath;
  final String _baseUrl;
  bool defaultRead = false;
  String? receivedPath;
  String? returnedTarget;
  int stopCount = 0;
  bool failResolution = false;

  @override
  Stream<String> get debugStream => throw StateError('test debug failure');

  @override
  String get url {
    defaultRead = true;
    return _baseUrl;
  }

  @override
  String urlForFile(String absolutePath) {
    receivedPath = absolutePath;
    if (failResolution) {
      throw const FileSystemException('resolution failed');
    }
    final target = '$_baseUrl${p.basename(absolutePath)}';
    returnedTarget = target;
    return target;
  }

  @override
  Future<void> stop() async {
    stopCount++;
  }
}

class _PreviewFixture {
  _PreviewFixture() {
    final projectDirectory = Directory(p.join(directory.path, 'project'))
      ..createSync();
    project = Project.create(name: 'web test', path: projectDirectory.path);
    File(
      p.join(project.path, 'index.html'),
    ).writeAsStringSync('<h1>index</h1>');
    File(
      p.join(project.path, 'main2.html'),
    ).writeAsStringSync('<h1>main2</h1>');
    final config = File(ProjectConfig.configPath(project.path));
    config.parent.createSync();
    config.writeAsStringSync(_projectConfigText);
  }

  final directory = Directory.systemTemp.createTempSync('qfli_web_preview_');
  final auth = AuthStore();
  final store = ProjectStore();
  final settings = SettingsStore();
  late final Project project;
  final sessions = <_RecordingPreviewSession>[];
  StudioProfile? previousProfile;
  bool failResolution = false;

  void installProfile() {
    previousProfile = StudioProfile.current;
    StudioProfile.current = StudioProfile(
      id: 'web-test',
      appTitle: 'Web test',
      templates: const [],
      isOffline: true,
      entryFileNames: const ['index.html'],
      supportedFileExtensions: const ['.html'],
      webPreviewFactory: (path) async {
        final session = _RecordingPreviewSession(
          baseUrl: 'http://127.0.0.1:1/',
          projectPath: path,
        )..failResolution = failResolution;
        sessions.add(session);
        return session;
      },
    );
  }

  Future<void> mount(
    WidgetTester tester, {
    String? initialOpenPath = 'main2.html',
  }) async {
    installProfile();
    tester.view.physicalSize = const Size(1100, 850);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(() async {
      await tester.pumpWidget(const SizedBox.shrink());
      if (!_disposed) {
        _disposed = true;
        auth.dispose();
        store.dispose();
        settings.dispose();
      }
      await _disposeFixtureTree(tester, directory);
    });
    await tester.pumpWidget(
      MaterialApp(
        home: EditorPage(
          project: project,
          auth: auth,
          store: store,
          settings: settings,
          initialOpenPath: initialOpenPath,
        ),
      ),
    );
    await _pumpIoUntil(
      tester,
      () =>
          initialOpenPath == null ||
          find
              .descendant(
                of: find.byType(Tab),
                matching: find.text(p.basename(initialOpenPath)),
              )
              .evaluate()
              .isNotEmpty,
    );
    await tester.pump(const Duration(milliseconds: 200));
  }

  var _disposed = false;

  Future<void> waitForStopped(WidgetTester tester, int count) async {
    await _pumpIoUntil(
      tester,
      () => sessions.length >= count && sessions[count - 1].stopCount >= 1,
    );
    await tester.pump();
  }

  Future<void> dispose() async {
    if (_disposed) return;
    _disposed = true;
    auth.dispose();
    store.dispose();
    settings.dispose();
  }
}

Future<void> _disposeFixtureTree(
  WidgetTester tester,
  Directory directory,
) async {
  // EditorPage.dispose() schedules an unawaited history.json write inside the
  // FakeAsync zone; alternate zones until deletion succeeds, as the core
  // editor_run_test fixture does.
  const maxRounds = 50;
  FileSystemException? lastError;
  for (var round = 0; round < maxRounds; round++) {
    try {
      if (directory.existsSync()) await directory.delete(recursive: true);
      return;
    } on FileSystemException catch (error) {
      lastError = error;
      await tester.pump(const Duration(milliseconds: 20));
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 20)),
      );
    }
  }
  throw lastError!;
}

Future<void> _pumpIoUntil(
  WidgetTester tester,
  bool Function() condition,
) async {
  for (var attempt = 0; attempt < 200; attempt++) {
    await tester.pump(const Duration(milliseconds: 20));
    if (condition()) return;
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 10)),
    );
  }
  expect(condition(), isTrue, reason: 'The editor operation did not finish.');
}
