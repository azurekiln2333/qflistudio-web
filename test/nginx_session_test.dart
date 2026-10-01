import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_web/services/nginx_session.dart';
import 'package:qfli_web/services/web_runtime.dart';

import 'web_dev_server_test.dart' show request;

Future<void> main() async {
  TestWidgetsFlutterBinding.ensureInitialized();
  final executable = await WebRuntime.nginxExecutable();
  if (executable == null) {
    test('native Nginx integration', () {}, skip: 'No desktop Nginx build');
    return;
  }
  late Directory project;
  late HttpOverrides? overrides;

  setUp(() {
    overrides = HttpOverrides.current;
    HttpOverrides.global = null;
    project = Directory.systemTemp.createTempSync('webforge-native-test-');
  });
  tearDown(() {
    HttpOverrides.global = overrides;
    project.deleteSync(recursive: true);
  });
  void write(String path, String content) {
    final file = File(p.join(project.path, path));
    file.parent.createSync(recursive: true);
    file.writeAsStringSync(content);
  }

  test('automatic selection starts the discovered native Nginx', () async {
    write('index.html', '<head></head><h1>Automatic native preview</h1>');
    final server = await WebRuntime.start(project.path);
    addTearDown(server.stop);
    expect(server.engineName, 'Nginx 1.31.6');
    final page = await request(server.url);
    expect(page.headers.value('x-webforge-engine'), 'nginx');
    expect(page.body, contains('Automatic native preview'));
  });

  test(
    'real Nginx serves a custom imported HTML entry and relative assets',
    () async {
      write('src/imported.html', '<head></head><h1>Custom native entry</h1>');
      write('src/style.css', 'body { color: green; }');
      write('.qfli/project.json', '{"entryFile":"src/imported.html"}');
      final server = await NginxSession.start(
        project.path,
        executable: executable,
      );
      addTearDown(server.stop);
      final page = await request(server.url);
      expect(page.status, HttpStatus.ok);
      expect(page.headers.value('x-webforge-engine'), 'nginx');
      expect(page.body, contains('Custom native entry'));
      expect((await request('${server.url}style.css')).body, contains('green'));
    },
  );

  test(
    'real Nginx serves the project, diagnostics and request logs',
    () async {
      write('src/index.html', '<head></head><h1>Native preview</h1>');
      write('src/style.css', 'body { color: red; }');
      write('src/.secret', 'private');
      final server = await NginxSession.start(
        project.path,
        executable: executable,
      );
      addTearDown(server.stop);
      expect(server.engineName, 'Nginx 1.31.6');
      final page = await request(server.url);
      expect(page.status, HttpStatus.ok);
      expect(
        page.headers.value(HttpHeaders.serverHeader),
        startsWith('nginx/'),
      );
      expect(page.headers.value('x-webforge-engine'), 'nginx');
      expect(page.body, contains('Native preview'));
      expect(page.body, contains('/__webforge/debug'));
      expect((await request('${server.url}style.css')).body, contains('red'));
      expect(
        (await request('${server.url}.secret')).status,
        HttpStatus.forbidden,
      );

      final debug = server.debugStream.firstWhere(
        (line) => line.contains('native console'),
      );
      expect(
        (await request(
          '${server.url}__webforge/debug',
          method: 'POST',
          headers: {'origin': server.url.substring(0, server.url.length - 1)},
          body: '{"message":"native console"}',
        )).status,
        HttpStatus.noContent,
      );
      expect(
        await debug.timeout(const Duration(seconds: 3)),
        contains('native console'),
      );

      final event = server.requests.firstWhere(
        (event) => event.path == '/logged.js',
      );
      expect(
        (await request('${server.url}logged.js')).status,
        HttpStatus.notFound,
      );
      expect(
        (await event.timeout(const Duration(seconds: 3))).status,
        HttpStatus.notFound,
      );
      await server.stop();
      await expectLater(request(server.url), throwsA(isA<SocketException>()));
    },
    skip: !Platform.isWindows,
  );

  test(
    'real Nginx proxies HTTP and WebSocket without altering redirects',
    () async {
      final upstream = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      addTearDown(() => upstream.close(force: true));
      upstream.listen((incoming) async {
        if (incoming.uri.path == '/v1/socket') {
          final socket = await WebSocketTransformer.upgrade(
            incoming,
            protocolSelector: (protocols) =>
                protocols.contains('echo') ? 'echo' : null,
          );
          socket.listen(socket.add);
          return;
        }
        if (incoming.uri.path == '/v1/redirect') {
          incoming.response.statusCode = HttpStatus.found;
          incoming.response.headers.set('location', '/v1/target');
        } else {
          expect(incoming.method, 'POST');
          expect(incoming.uri.toString(), '/v1/items?q=7');
          expect(await utf8.decoder.bind(incoming).join(), 'payload');
          incoming.response.statusCode = HttpStatus.created;
          incoming.response.headers.set('x-upstream', 'true');
          incoming.response.write('saved');
        }
        await incoming.response.close();
      });
      write('index.html', 'ok');
      write(
        '.qfli/web.json',
        jsonEncode({
          'proxies': [
            {
              'prefix': '/api',
              'target': 'http://127.0.0.1:${upstream.port}/v1/',
            },
          ],
        }),
      );
      final server = await NginxSession.start(
        project.path,
        executable: executable,
      );
      addTearDown(server.stop);
      final response = await request(
        '${server.url}api/items?q=7',
        method: 'POST',
        body: 'payload',
      );
      expect(response.status, HttpStatus.created);
      expect(response.body, 'saved');
      expect(response.headers.value('x-upstream'), 'true');
      final redirect = await request('${server.url}api/redirect');
      expect(redirect.status, HttpStatus.found);
      expect(redirect.headers.value('location'), '/v1/target');

      final socket = await WebSocket.connect(
        '${server.url.replaceFirst('http:', 'ws:')}api/socket',
        protocols: ['echo'],
      );
      addTearDown(socket.close);
      expect(socket.protocol, 'echo');
      socket.add([7, 8, 9]);
      expect(await socket.first.timeout(const Duration(seconds: 3)), [7, 8, 9]);
    },
    skip: !Platform.isWindows,
  );

  test(
    'nested HTTPS proxy takes priority over its HTTP parent',
    () async {
      write('index.html', 'ok');
      final upstream = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      addTearDown(() => upstream.close(force: true));
      upstream.listen((incoming) async {
        incoming.response.write('HTTP parent');
        await incoming.response.close();
      });
      final closedPort = await ServerSocket.bind(
        InternetAddress.loopbackIPv4,
        0,
      );
      final httpsPort = closedPort.port;
      await closedPort.close();
      write(
        '.qfli/web.json',
        jsonEncode({
          'proxies': [
            {'prefix': '/api', 'target': 'http://127.0.0.1:${upstream.port}'},
            {'prefix': '/api/secure', 'target': 'https://127.0.0.1:$httpsPort'},
          ],
        }),
      );
      final server = await NginxSession.start(
        project.path,
        executable: executable,
      );
      addTearDown(server.stop);
      expect((await request('${server.url}api/items')).body, 'HTTP parent');
      for (final path in ['api/secure', 'api/secure/items']) {
        final result = await request('${server.url}$path');
        expect(result.status, HttpStatus.badGateway);
        expect(result.body, isNot(contains('HTTP parent')));
      }
    },
    skip: !Platform.isWindows,
  );

  test(
    'real Nginx streams live reload and rejects occupied ports',
    () async {
      write('index.html', '<head></head>before');
      final server = await NginxSession.start(
        project.path,
        executable: executable,
      );
      addTearDown(server.stop);
      final client = HttpClient();
      addTearDown(() => client.close(force: true));
      final stream = await (await client.getUrl(
        Uri.parse('${server.url}__webforge/events'),
      )).close();
      final reload = stream
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .firstWhere((line) => line == 'data: reload')
          .timeout(const Duration(seconds: 5));
      write('index.html', '<head></head>after');
      expect(await reload, 'data: reload');
      write('.qfli/web.json', jsonEncode({'port': server.port}));
      await expectLater(
        NginxSession.start(project.path, executable: executable),
        throwsA(isA<SocketException>()),
      );
    },
    skip: !Platform.isWindows,
  );
}
