import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_web/services/web_dev_server.dart';
import 'package:qfli_web/services/web_project_config.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late Directory project;
  late HttpOverrides? savedOverrides;

  setUp(() {
    savedOverrides = HttpOverrides.current;
    HttpOverrides.global = null;
    project = Directory.systemTemp.createTempSync('webforge-server-');
  });

  tearDown(() {
    HttpOverrides.global = savedOverrides;
    if (project.existsSync()) project.deleteSync(recursive: true);
  });

  void write(String path, String body) {
    final file = File(p.join(project.path, path));
    file.parent.createSync(recursive: true);
    file.writeAsStringSync(body);
  }

  test('src template serves HTML and its relative CSS and JS', () async {
    write('src/index.html', '<head></head><link href="style.css">');
    write('src/style.css', 'body { color: red; }');
    write('src/main.js', 'console.log("ready")');
    final server = await WebDevServer.start(project.path);
    addTearDown(server.stop);

    final page = await request('${server.url}index.html');
    expect(page.status, HttpStatus.ok);
    expect(page.body, contains('/__webforge/events'));
    expect((await request('${server.url}style.css')).body, contains('red'));
    expect((await request('${server.url}main.js')).body, contains('ready'));
    final missing = await request('${server.url}missing.js');
    expect(missing.status, HttpStatus.notFound);
    expect(missing.body, isNot(contains('<head>')));
  });

  test('SPA fallback only handles browser navigation', () async {
    write('index.html', '<h1>App</h1>');
    write('.qfli/web.json', '{"spaFallback":true}');
    final server = await WebDevServer.start(project.path);
    addTearDown(server.stop);

    expect(
      (await request(
        '${server.url}users/42',
        headers: {'accept': 'text/html'},
      )).body,
      contains('App'),
    );
    expect(
      (await request(
        '${server.url}users/42',
        headers: {'accept': '*/*'},
      )).status,
      HttpStatus.notFound,
    );
    expect(
      (await request(
        '${server.url}missing.css',
        headers: {'accept': 'text/html'},
      )).status,
      HttpStatus.notFound,
    );
  });

  test(
    'private project files and symlinks outside root are not served',
    () async {
      write('index.html', 'ok');
      write('.qfli/secret.txt', 'private');
    final outside = File('${project.path}.outside.txt');
      outside.writeAsStringSync('outside');
      addTearDown(() {
        if (outside.existsSync()) outside.deleteSync();
      });
      final link = Link(p.join(project.path, 'escape.txt'));
      var hasSymlink = false;
      try {
        link.createSync(outside.path);
        hasSymlink = true;
      } on FileSystemException {
        // Windows may disallow creating symbolic links without developer mode.
      }
      final server = await WebDevServer.start(project.path);
      addTearDown(server.stop);

      expect(
        (await request('${server.url}.qfli/secret.txt')).status,
        HttpStatus.forbidden,
      );
      expect(
        (await request('${server.url}%2e%2e/outside-webforge.txt')).status,
        isNot(HttpStatus.ok),
      );
      if (hasSymlink) {
        expect(
          (await request('${server.url}escape.txt')).status,
          HttpStatus.forbidden,
        );
      }
    },
  );

  test(
    'proxy forwards method, query, body, response status and headers',
    () async {
      final upstream = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      addTearDown(() => upstream.close(force: true));
      upstream.listen((incoming) async {
        expect(incoming.method, 'POST');
        expect(incoming.uri.toString(), '/v1/items?key=7');
        expect(await utf8.decoder.bind(incoming).join(), 'payload');
        incoming.response.statusCode = HttpStatus.created;
        incoming.response.headers.set('x-upstream', 'yes');
        incoming.response.write('saved');
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
      final server = await WebDevServer.start(project.path);
      addTearDown(server.stop);

      final result = await request(
        '${server.url}api/items?key=7',
        method: 'POST',
        body: 'payload',
      );
      expect(result.status, HttpStatus.created);
      expect(result.body, 'saved');
      expect(result.headers.value('x-upstream'), 'yes');
    },
  );

  test('browser errors reach debug stream and are bounded', () async {
    write('index.html', 'ok');
    final server = await WebDevServer.start(project.path);
    addTearDown(server.stop);
    final event = server.debugStream.first;
    final result = await request(
      '${server.url}__webforge/debug',
      method: 'POST',
      headers: {'content-type': 'application/json'},
      body: jsonEncode({'level': 'error', 'message': 'ReferenceError'}),
    );
    expect(result.status, HttpStatus.noContent);
    expect(await event, contains('ReferenceError'));
    expect(server.debugBuffer, hasLength(1));
  });

  test('invalid root and proxy settings fail before binding', () async {
    write('index.html', 'ok');
    write('.qfli/web.json', '{"root":"../outside"}');
    expect(() => WebProjectConfig.load(project.path), throwsFormatException);
    write(
      '.qfli/web.json',
      '{"proxies":[{"prefix":"/api","target":"file:///etc"}]}',
    );
    expect(() => WebProjectConfig.load(project.path), throwsFormatException);
  });
}

Future<({int status, String body, HttpHeaders headers})> request(
  String url, {
  String method = 'GET',
  Map<String, String> headers = const {},
  String? body,
}) async {
  final client = HttpClient();
  try {
    final outgoing = await client.openUrl(method, Uri.parse(url));
    headers.forEach(outgoing.headers.set);
    if (body != null) outgoing.write(body);
    final incoming = await outgoing.close();
    final text = await utf8.decoder.bind(incoming).join();
    return (status: incoming.statusCode, body: text, headers: incoming.headers);
  } finally {
    client.close(force: true);
  }
}
