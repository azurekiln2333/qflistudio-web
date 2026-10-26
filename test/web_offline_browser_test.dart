import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart' show debugPrintSynchronously;
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_web/services/nginx_session.dart';
import 'package:qfli_web/services/web_dev_server.dart';
import 'package:qfli_web/services/web_project_config.dart';
import 'package:qfli_web/services/web_runtime.dart';
import 'package:qfli_web/services/web_runtime_session.dart';

import 'web_dev_server_test.dart' show request;

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  for (final native in [false, true]) {
    test('production ${native ? 'Nginx' : 'WebForge'} keeps shipped offline '
        'resources and blocks external resources and forms', () async {
      final previousOverrides = HttpOverrides.current;
      HttpOverrides.global = null;
      addTearDown(() => HttpOverrides.global = previousOverrides);
      final project = Directory.systemTemp.createTempSync('webforge-csp-');
      addTearDown(() => project.deleteSync(recursive: true));
      // A real second loopback origin observes any escaped WebSocket handshake.
      // Unlike mocking window.WebSocket, this preserves the browser's own CSP.
      final socketSentinel = await HttpServer.bind(
        InternetAddress.loopbackIPv4,
        0,
      );
      addTearDown(() => socketSentinel.close(force: true));
      var escapedWebSockets = 0;
      var escapedReports = 0;
      var escapedObjects = 0;
      socketSentinel.listen((incoming) async {
        if (incoming.uri.path == '/report') {
          escapedReports++;
        } else if (incoming.uri.path == '/object' ||
            incoming.uri.path == '/embed') {
          escapedObjects++;
        } else {
          escapedWebSockets++;
        }
        incoming.response.statusCode = HttpStatus.forbidden;
        await incoming.response.close();
      });
      final externalSocketUrl = 'ws://127.0.0.1:${socketSentinel.port}/socket';
      final externalObjectUrl =
          'http://127.0.0.1:${socketSentinel.port}/object';
      final externalEmbedUrl = 'http://127.0.0.1:${socketSentinel.port}/embed';
      final reportUpstream = await HttpServer.bind(
        InternetAddress.loopbackIPv4,
        0,
      );
      addTearDown(() => reportUpstream.close(force: true));
      reportUpstream.listen((incoming) async {
        incoming.response.headers.contentType = ContentType.html;
        incoming.response.headers.set(
          'content-security-policy-report-only',
          "script-src 'none'; report-uri http://127.0.0.1:${socketSentinel.port}/report",
        );
        incoming.response.write('''<!doctype html><script>
window.__reportViolations = [];
document.addEventListener('securitypolicyviolation', event => {
  window.__reportViolations.push(event.effectiveDirective);
});
window.__reportMarker = 42;
</script>''');
        await incoming.response.close();
      });
      File(p.join(project.path, 'index.html')).writeAsStringSync(
        _fixture
            .replaceAll('__OFFLINE_SOCKET_URL__', externalSocketUrl)
            .replaceAll('__OFFLINE_OBJECT_URL__', externalObjectUrl)
            .replaceAll('__OFFLINE_EMBED_URL__', externalEmbedUrl),
      );
      File(p.join(project.path, 'local.js')).writeAsStringSync(
        "window.__offlineLocalScript = 'loaded-from-project';",
      );
      File(
        p.join(project.path, 'local.css'),
      ).writeAsStringSync('#local { color: rgb(0, 128, 0); }');
      File(p.join(project.path, 'local-object.html')).writeAsStringSync(
        '<!doctype html><p id="local-object-content">Local object document</p>',
      );
      // Use the shipped documents unchanged: synthetic local.css alone misses
      // data:/blob: stylesheets, embedded documents and an authored Blob fetch.
      final catalogFile = File('assets/content/examples.json');
      final catalog =
          jsonDecode(catalogFile.readAsStringSync()) as Map<String, dynamic>;
      final entries = (catalog['entries'] as List).cast<Map<String, dynamic>>();
      final catalogFiles = <String, String>{};
      for (final id in _catalogIds) {
        final entry = entries.singleWhere((entry) => entry['id'] == id);
        final name = '$id.html';
        final source = entry['code'] as String;
        File(p.join(project.path, name)).writeAsStringSync(source);
        catalogFiles[id] = name;
      }
      final executable = native ? await WebRuntime.nginxExecutable() : null;
      if (native && executable == null) {
        markTestSkipped('No desktop Nginx build for the real browser check');
        return;
      }
      final config = WebProjectConfig.parse(project.path, {
        'proxies': [
          {
            'prefix': '/policy',
            'target': 'http://127.0.0.1:${reportUpstream.port}',
          },
        ],
      });
      final WebRuntimeSession server = native
          ? await NginxSession.start(
              project.path,
              executable: executable!,
              configuration: config,
            )
          : await WebDevServer.start(project.path, configuration: config);
      addTearDown(server.stop);
      for (final path in ['', 'missing.js']) {
        final response = await request('${server.url}$path');
        expect(
          response.headers.value('content-security-policy'),
          WebProjectConfig.offlineContentSecurityPolicy,
        );
      }
      final process = await Process.start('node', [
        'scripts/test_web_offline_browser.mjs',
      ], workingDirectory: Directory.current.path);
      addTearDown(() => process.kill());
      final output = process.stdout.transform(utf8.decoder).join();
      final errors = process.stderr.transform(utf8.decoder).join();
      process.stdin.writeln(
        jsonEncode({
          'baseUrl': server.url,
          'externalSocketUrl': externalSocketUrl,
          'externalObjectUrls': [externalObjectUrl, externalEmbedUrl],
          'reportPageUrl': '${server.url}policy',
          'catalogPages': {
            for (final entry in catalogFiles.entries)
              entry.key: '${server.url}${entry.value}',
          },
        }),
      );
      await process.stdin.close();
      final exit = await process.exitCode.timeout(
        const Duration(seconds: 30),
        onTimeout: () {
          process.kill();
          throw StateError('Production offline browser check timed out');
        },
      );
      final reportText = await output;
      expect(exit, 0, reason: '${await errors}\n$reportText');
      final report = jsonDecode(reportText) as Map<String, dynamic>;
      debugPrintSynchronously(
        'production offline ${server.engineName}: $reportText',
      );
      expect(report['escapedRequests'], isEmpty);
      expect(escapedWebSockets, 0);
      expect(escapedReports, 0);
      expect(escapedObjects, 0);
      expect(report['policy'], WebProjectConfig.offlineContentSecurityPolicy);
      expect(
        (report['catalogChecks'] as List).map((item) => (item as Map)['id']),
        orderedEquals(_catalogIds),
      );
      if (native) {
        final response = await request(server.url);
        expect(response.headers.value('x-webforge-engine'), 'nginx');
      }
    }, timeout: const Timeout(Duration(seconds: 45)));
  }
}

const _catalogIds = [
  'html-example-027',
  'html-example-097',
  'html-example-137',
  'html-example-138',
  'js-example-017',
];

const _fixture = '''<!doctype html><html><head><meta charset="utf-8">
<script>
window.__offlineViolations = [];
document.addEventListener('securitypolicyviolation', event => {
  window.__offlineViolations.push({directive:event.effectiveDirective, uri:event.blockedURI});
});
window.__offlineEval = eval('40 + 2');
window.__offlineFetchBlocked = false;
fetch('https://qfli-offline.invalid/api').catch(() => {
  window.__offlineFetchBlocked = true;
}).finally(() => { window.__offlineFetchDone = true; });
window.__offlineWebsocketError = false;
try {
  const socket = new WebSocket('__OFFLINE_SOCKET_URL__');
  socket.onerror = () => { window.__offlineWebsocketError = true; };
} catch (error) { window.__offlineWebsocketError = true; }
</script>
<script src="local.js"></script><link rel="stylesheet" href="local.css">
<script src="https://qfli-offline.invalid/remote.js"></script>
<link rel="stylesheet" href="https://qfli-offline.invalid/remote.css">
</head><body><p id="local">Local project</p>
<object id="local-object" type="text/html" data="local-object.html"></object>
<img src="https://qfli-offline.invalid/remote.png" alt="blocked">
<iframe src="https://qfli-offline.invalid/frame"></iframe>
<object type="text/html" data="https://object.qfli-offline.invalid/remote.html"></object>
<embed type="image/svg+xml" src="https://embed.qfli-offline.invalid/remote.svg">
<object type="text/html" data="__OFFLINE_OBJECT_URL__"></object>
<embed type="image/svg+xml" src="__OFFLINE_EMBED_URL__">
<form id="external-form" action="https://qfli-offline.invalid/submit"><button>Submit</button></form>
</body></html>''';
