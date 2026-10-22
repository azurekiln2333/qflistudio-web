import 'dart:async';
import 'dart:convert';
import 'dart:ffi';
import 'dart:io';

import 'package:ffi/ffi.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_web/main.dart' show webProfile;
import 'package:qfli_web/services/nginx_host.dart';
import 'package:qfli_web/services/web_code_analyzer.dart';
import 'package:qfli_web/services/web_runtime_session.dart';

/// Alternate device-only entry. It exercises production adapters against an
/// owned temporary fixture; it never opens a user project or runs its sources.
Future<void> main() async {
  final binding = WidgetsFlutterBinding.ensureInitialized();
  StudioProfile.current = webProfile;
  final state = ValueNotifier<Map<String, Object?>>({
    'status': 'running',
    'cases': <String, bool>{},
  });
  runApp(_AcceptanceApp(state));
  await binding.endOfFrame;
  await _Acceptance(state).run();
}

typedef _VersionNative = Pointer<Utf8> Function();
typedef _VersionDart = Pointer<Utf8> Function();

class _Acceptance {
  _Acceptance(this.state);

  final ValueNotifier<Map<String, Object?>> state;
  final cases = <String, bool>{};
  final identity = <String, Object?>{
    'os': Platform.operatingSystem,
    'profile': webProfile.id,
    'syntaxLibrary': 'libqfli_web_syntax.so',
    'nginxLibrary': 'libqfli_nginx_napi.so',
  };
  Directory? fixture;
  final disk = <String, List<int>>{};

  void require(bool condition, String message) {
    if (!condition) throw StateError(message);
  }

  String publicError(Object error) {
    var text = error.toString().replaceAll(Directory.systemTemp.path, '<temp>');
    if (fixture != null) text = text.replaceAll(fixture!.path, '<fixture>');
    return text.length > 320 ? text.substring(0, 320) : text;
  }

  Future<void> check(
    String id,
    Future<Map<String, Object?>> Function() action,
  ) async {
    Map<String, Object?> details;
    try {
      details = await action();
      cases[id] = true;
    } catch (error) {
      cases[id] = false;
      details = {'error': publicError(error)};
    }
    debugPrintSynchronously(
      'QFLI_WEB_OHOS_ACCEPTANCE_CASE:${jsonEncode({'id': id, 'pass': cases[id], ...details})}',
    );
    state.value = {'status': 'running', 'cases': Map.of(cases), ...identity};
  }

  Future<CodeAnalysisResult> analyze(
    String source, {
    String name = 'app.js',
    String language = 'javascript',
  }) {
    final path = p.join(fixture!.path, name);
    return webProfile.codeAnalyzer!
        .analyze(
          CodeAnalysisRequest(
            projectPath: fixture!.path,
            activeFilePath: path,
            language: language,
            revision: 19,
            documents: [
              CodeDocumentSnapshot(path: path, text: source, revision: 19),
            ],
          ),
        )
        .timeout(const Duration(seconds: 5));
  }

  void clean(CodeAnalysisResult result) {
    require(result.unavailableReason == null, 'parser unavailable');
    require(result.diagnostics.isEmpty, 'valid source received diagnostics');
  }

  Map<String, Object?> exactJavaScript(
    CodeAnalysisResult result,
    int start,
    int end,
    String name,
  ) {
    require(result.unavailableReason == null, 'QuickJS unavailable');
    final errors = result.diagnostics
        .where((item) => item.source.startsWith('QuickJS'))
        .toList();
    require(errors.length == 1, 'expected one real QuickJS diagnostic');
    final error = errors.single;
    require(error.filePath == p.join(fixture!.path, name), 'wrong source path');
    require(error.code == 'SyntaxError', 'wrong diagnostic kind');
    require(
      error.startOffset == start && error.endOffset == end,
      'incorrect original UTF-16 diagnostic range',
    );
    return {
      'backend': error.source,
      'startUtf16': error.startOffset,
      'endUtf16': error.endOffset,
      'expectedStartUtf16': start,
      'expectedEndUtf16': end,
    };
  }

  Future<void> unchanged() async {
    final found = <String>{};
    await for (final item in fixture!.list(
      recursive: true,
      followLinks: false,
    )) {
      if (item is! File) continue;
      final relative = p.relative(item.path, from: fixture!.path);
      found.add(relative);
      require(disk.containsKey(relative), 'unexpected fixture file created');
      require(
        listEquals(await item.readAsBytes(), disk[relative]),
        'saved fixture source changed',
      );
    }
    require(setEquals(found, disk.keys.toSet()), 'saved fixture file removed');
  }

  Future<void> run() async {
    try {
      await check('ohos-profile', () async {
        require(Platform.operatingSystem == 'ohos', 'OHOS execution required');
        require(
          webProfile.isOffline && webProfile.offlineOnly,
          'offline profile',
        );
        require(
          webProfile.codeAnalyzer is WebCodeAnalyzer,
          'production analyzer',
        );
        require(
          webProfile.webPreviewFactory != null,
          'production preview factory',
        );
        return {'analyzer': 'WebCodeAnalyzer', 'offline': true};
      });
      fixture = await Directory.systemTemp.createTemp(
        'qfli-web-ohos-acceptance-',
      );
      final sources = {
        'app.js': 'const saved = ;\r\n',
        'index.html':
            '<!doctype html><html><head><title>OHOS acceptance</title>'
            '<link rel="stylesheet" href="style.css"></head>'
            '<body>qfli-owned-offline-preview</body></html>',
        'style.css': 'body { color: rgb(12, 34, 56); }',
        p.join('.qfli', 'web.json'): jsonEncode({'engine': 'nginx', 'port': 0}),
      };
      for (final entry in sources.entries) {
        final file = File(p.join(fixture!.path, entry.key));
        await file.parent.create(recursive: true);
        final bytes = utf8.encode(entry.value);
        await file.writeAsBytes(bytes, flush: true);
        disk[entry.key] = bytes;
      }

      await check('quickjs-library', () async {
        final library = DynamicLibrary.open('libqfli_web_syntax.so');
        final version = library
            .lookupFunction<_VersionNative, _VersionDart>(
              'qfli_web_syntax_version',
            )()
            .toDartString();
        require(
          version == 'QuickJS 2026-06-04 (compile-only, no module resolution)',
          'unexpected native backend identity',
        );
        identity['quickjs'] = version;
        return {'version': version};
      });
      await check('js-unsaved-clean', () async {
        clean(
          await analyze(
            'class Item { #x = 1; get() { return this.#x; } } '
            'const value = new Item()?.get() ?? 0;',
          ),
        );
        return {'differentSavedSource': true, 'diagnostics': 0};
      });
      await check('js-crlf-emoji', () async {
        const source = '// 😀\r\nconst text="😀"; const broken = ;';
        final start = source.lastIndexOf(';');
        return exactJavaScript(
          await analyze(source),
          start,
          start + 1,
          'app.js',
        );
      });
      await check('js-eof', () async {
        const source = 'const x = (';
        return exactJavaScript(
          await analyze(source),
          source.length,
          source.length,
          'app.js',
        );
      });
      await check('html-embedded-js', () async {
        const prefix =
            '<!doctype html>\r\n<html><head><title>😀</title></head>'
            '<body>\r\n<script>';
        const script = '// 😀\r\nconst broken = ;';
        final start = prefix.length + script.lastIndexOf(';');
        return exactJavaScript(
          await analyze(
            '$prefix$script</script></body></html>',
            name: 'embedded.html',
            language: 'html',
          ),
          start,
          start + 1,
          'embedded.html',
        );
      });
      await check('css-supported', () async {
        clean(
          await analyze(
            'a:hover { color: rgb(255, 0, 0); margin: 1rem; }',
            name: 'style.css',
            language: 'css',
          ),
        );
        return {'backend': 'csslib', 'diagnostics': 0};
      });
      await check('css-real-error', () async {
        const source = '/* 😀 */\r\na { color red; }';
        final result = await analyze(
          source,
          name: 'style.css',
          language: 'css',
        );
        require(
          result.unavailableReason == null,
          'CSS unexpectedly unavailable',
        );
        require(result.diagnostics.isNotEmpty, 'CSS error not detected');
        require(
          result.diagnostics.every((d) => d.source == 'csslib'),
          'CSS backend',
        );
        require(
          result.diagnostics.first.startOffset >= source.indexOf('color'),
          'CSS range excludes declaration',
        );
        return {'backend': 'csslib', 'diagnostics': result.diagnostics.length};
      });
      await check('css-unavailable', () async {
        final result = await analyze(
          '@scope (.card) { a { color: red; } }',
          name: 'style.css',
          language: 'css',
        );
        require(
          result.unavailableReason?.contains('csslib 尚不支持') == true,
          'unsupported valid CSS reported clean',
        );
        require(
          result.diagnostics.isEmpty,
          'unsupported CSS received false errors',
        );
        return {'backend': 'csslib', 'available': false, 'falseDiagnostics': 0};
      });
      await check('js-no-execution', () async {
        final sentinel = File(p.join(fixture!.path, 'must-not-exist'));
        clean(
          await analyze(
            'require("fs").writeFileSync('
            '${jsonEncode(sentinel.path)}, "bad"); '
            'throw Error("must not execute"); while (true) {} '
            'fetch("http://127.0.0.1:1/must-not-request");',
          ),
        );
        require(!await sentinel.exists(), 'analyzed code wrote a file');
        return {'compiledOnly': true, 'sentinelExists': false};
      });
      await check('js-no-import-read', () async {
        clean(
          await analyze(
            'import value from "./must-not-exist.mjs"; '
            'export default await value;',
            name: 'module.mjs',
          ),
        );
        return {'missingDependencyResolved': false, 'diagnostics': 0};
      });
      await check('sources-unchanged', () async {
        await unchanged();
        return {'unchangedFiles': disk.length};
      });
      await check('native-preview', preview);
      await check('sources-after-preview', () async {
        await unchanged();
        return {'unchangedFiles': disk.length};
      });
    } catch (error) {
      cases['harness'] = false;
      debugPrintSynchronously(
        'QFLI_WEB_OHOS_ACCEPTANCE_CASE:'
        '${jsonEncode({'id': 'harness', 'pass': false, 'error': publicError(error)})}',
      );
    } finally {
      await check('fixture-cleanup', () async {
        if (fixture != null && await fixture!.exists()) {
          await fixture!
              .delete(recursive: true)
              .timeout(const Duration(seconds: 5));
        }
        require(fixture == null || !await fixture!.exists(), 'fixture remains');
        return {'ownedFixtureRemoved': true};
      });
      final passed = cases.values.where((value) => value).length;
      final result = <String, Object?>{
        'schemaVersion': 1,
        'status': passed == cases.length ? 'passed' : 'failed',
        ...identity,
        'passed': passed,
        'failed': cases.length - passed,
        'cases': Map.of(cases),
      };
      state.value = result;
      debugPrintSynchronously(
        'QFLI_WEB_OHOS_ACCEPTANCE_RESULT:${jsonEncode(result)}',
      );
    }
  }

  Future<({int status, String body, String? server})> get(
    HttpClient client,
    Uri uri,
  ) async {
    require(
      uri.scheme == 'http' && uri.host == '127.0.0.1',
      'loopback required',
    );
    final request = await client
        .getUrl(uri)
        .timeout(const Duration(seconds: 3));
    final response = await request.close().timeout(const Duration(seconds: 3));
    final bytes = <int>[];
    await for (final chunk in response.timeout(const Duration(seconds: 3))) {
      bytes.addAll(chunk);
      require(bytes.length <= 65536, 'unexpectedly large fixture response');
    }
    return (
      status: response.statusCode,
      body: utf8.decode(bytes),
      server: response.headers.value('server'),
    );
  }

  Future<Map<String, Object?>> preview() async {
    final version = await const EmbeddedNginxHost().version().timeout(
      const Duration(seconds: 5),
    );
    identity['nginx'] = version;
    WebPreviewSession? session;
    StreamSubscription<WebRequestEvent>? subscription;
    final requests = <WebRequestEvent>[];
    final client = HttpClient()
      ..connectionTimeout = const Duration(seconds: 2)
      ..idleTimeout = Duration.zero
      ..findProxy = (_) => 'DIRECT';
    try {
      final starting = webProfile.webPreviewFactory!(fixture!.path);
      try {
        session = await starting.timeout(const Duration(seconds: 15));
      } on TimeoutException {
        // A timeout does not cancel a Future. Retain ownership of any session
        // that completes later rather than abandoning its native listener.
        unawaited(
          starting.then<void>((lateSession) async {
            try {
              await lateSession.stop().timeout(const Duration(seconds: 5));
            } catch (error) {
              debugPrintSynchronously(
                'QFLI_WEB_OHOS_ACCEPTANCE_LATE_CLEANUP:'
                '${jsonEncode({'pass': false, 'error': publicError(error)})}',
              );
            }
          }, onError: (Object _, StackTrace _) {}),
        );
        rethrow;
      }
      require(
        session is WebRuntimeSession,
        'production runtime session required',
      );
      final runtime = session as WebRuntimeSession;
      require(
        runtime.engineName == 'Nginx $version',
        'native engine substituted',
      );
      subscription = runtime.requests.listen((event) {
        if (requests.length < 32) requests.add(event);
      });
      final uri = Uri.parse(runtime.url).resolve('index.html');
      final html = await get(client, uri);
      require(html.status == 200, 'HTML HTTP status');
      require(html.server?.startsWith('nginx/') == true, 'native HTTP server');
      require(html.body.contains('qfli-owned-offline-preview'), 'HTML body');
      final css = await get(client, uri.resolve('style.css'));
      require(
        css.status == 200 && css.body.contains('rgb(12, 34, 56)'),
        'CSS body',
      );
      final missing = await get(client, uri.resolve('missing-acceptance.js'));
      require(missing.status == 404, 'missing asset must be 404');
      final deadline = DateTime.now().add(const Duration(seconds: 3));
      while (!requests.any(
        (event) =>
            event.method == 'GET' &&
            event.path == '/index.html' &&
            event.status == 200,
      )) {
        require(
          DateTime.now().isBefore(deadline),
          'native request log missing',
        );
        await Future<void>.delayed(const Duration(milliseconds: 50));
      }
      await subscription.cancel();
      subscription = null;
      await session.stop().timeout(const Duration(seconds: 5));
      session = null;
      var refused = false;
      try {
        await get(client, uri);
      } on SocketException {
        refused = true;
      }
      require(refused, 'preview listener remains after stop');
      return {
        'engine': runtime.engineName,
        'htmlStatus': html.status,
        'cssStatus': css.status,
        'missingStatus': missing.status,
        'requestLog': true,
        'postStopConnectionRefused': refused,
      };
    } finally {
      client.close(force: true);
      await subscription?.cancel();
      await session?.stop().timeout(const Duration(seconds: 5));
    }
  }
}

class _AcceptanceApp extends StatelessWidget {
  const _AcceptanceApp(this.state);
  final ValueListenable<Map<String, Object?>> state;

  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'WebForge OHOS acceptance',
    home: Scaffold(
      appBar: AppBar(title: const Text('WebForge OHOS acceptance')),
      body: SafeArea(
        child: ValueListenableBuilder<Map<String, Object?>>(
          valueListenable: state,
          builder: (context, value, child) {
            final checks = (value['cases'] as Map<String, bool>?) ?? {};
            return ListView(
              padding: const EdgeInsets.all(20),
              children: [
                Text(
                  '${value['status']}'.toUpperCase(),
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
                Text('QuickJS: ${value['quickjs'] ?? 'checking'}'),
                Text('Nginx: ${value['nginx'] ?? 'checking'}'),
                const Text('Production source analysis and loopback preview'),
                const Text('Editor UI and native debugging are not evaluated.'),
                const SizedBox(height: 16),
                for (final check in checks.entries)
                  Text('${check.value ? 'PASS' : 'FAIL'}  ${check.key}'),
              ],
            );
          },
        ),
      ),
    ),
  );
}
