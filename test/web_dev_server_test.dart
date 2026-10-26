import 'dart:async';
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
    'custom imported HTML entry serves the page, assets and SPA routes',
    () async {
      write('src/lesson.html', '<head></head><h1>Imported lesson</h1>');
      write('src/style.css', 'body { color: green; }');
      write('.qfli/project.json', '{"entryFile":"src/lesson.html"}');
      write('.qfli/web.json', '{"spaFallback":true}');
      final server = await WebDevServer.start(project.path);
      addTearDown(server.stop);

      expect(server.config.root, p.join(project.path, 'src'));
      expect(server.config.indexFile, 'lesson.html');
      expect((await request(server.url)).body, contains('Imported lesson'));
      expect((await request('${server.url}style.css')).body, contains('green'));
      expect((await request('${server.url}lesson.html')).status, HttpStatus.ok);
      expect(
        (await request('${server.url}missing.js')).status,
        HttpStatus.notFound,
      );
      expect(
        (await request(
          '${server.url}users/42',
          headers: {'accept': 'text/html'},
        )).body,
        contains('Imported lesson'),
      );
    },
  );

  test(
    'an explicit Web root takes precedence over an imported entry',
    () async {
      write('src/lesson.html', '<h1>Source</h1>');
      write('dist/index.html', '<h1>Build</h1>');
      write('.qfli/project.json', '{"entryFile":"src/lesson.html"}');
      write('.qfli/web.json', '{"root":"dist"}');
      final server = await WebDevServer.start(project.path);
      addTearDown(server.stop);
      expect((await request(server.url)).body, contains('Build'));
    },
  );

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

  test('proxy preserves redirects and WebSocket messages', () async {
    final upstream = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    addTearDown(() => upstream.close(force: true));
    upstream.listen((incoming) async {
      if (incoming.uri.path == '/v1/redirect') {
        incoming.response.statusCode = HttpStatus.found;
        incoming.response.headers.set(
          HttpHeaders.locationHeader,
          '/v1/destination',
        );
        await incoming.response.close();
        return;
      }
      expect(incoming.uri.toString(), '/v1/socket?token=7');
      final socket = await WebSocketTransformer.upgrade(
        incoming,
        protocolSelector: (protocols) =>
            protocols.contains('echo') ? 'echo' : null,
      );
      socket.listen(socket.add);
    });
    write('index.html', 'ok');
    write(
      '.qfli/web.json',
      jsonEncode({
        'proxies': [
          {'prefix': '/api', 'target': 'http://127.0.0.1:${upstream.port}/v1/'},
        ],
      }),
    );
    final server = await WebDevServer.start(project.path);
    addTearDown(server.stop);

    final redirect = await request('${server.url}api/redirect');
    expect(redirect.status, HttpStatus.found);
    expect(
      redirect.headers.value(HttpHeaders.locationHeader),
      '/v1/destination',
    );

    final debug = <String>[];
    final debugSubscription = server.debugStream.listen(debug.add);
    addTearDown(debugSubscription.cancel);
    late final WebSocket socket;
    try {
      socket = await WebSocket.connect(
        '${server.url.replaceFirst('http:', 'ws:')}api/socket?token=7',
        protocols: ['echo'],
      );
    } on WebSocketException catch (error) {
      fail('$error; diagnostics: $debug');
    }
    addTearDown(socket.close);
    expect(socket.protocol, 'echo');
    final messages = StreamIterator<dynamic>(socket);
    addTearDown(messages.cancel);
    socket.add('hello');
    expect(
      await messages.moveNext().timeout(const Duration(seconds: 5)),
      isTrue,
    );
    expect(messages.current, 'hello');
    socket.add([1, 2, 3]);
    expect(
      await messages.moveNext().timeout(const Duration(seconds: 5)),
      isTrue,
    );
    expect(messages.current, [1, 2, 3]);
    final closed = messages.moveNext();
    await server.stop();
    expect(await closed.timeout(const Duration(seconds: 5)), isFalse);
    expect(socket.closeCode, WebSocketStatus.goingAway);
  });

  test('file changes notify the live reload stream', () async {
    write('index.html', '<h1>Before</h1>');
    final server = await WebDevServer.start(project.path);
    addTearDown(server.stop);
    final client = HttpClient();
    addTearDown(() => client.close(force: true));
    final outgoing = await client.getUrl(
      Uri.parse('${server.url}__webforge/events'),
    );
    final incoming = await outgoing.close();
    expect(incoming.statusCode, HttpStatus.ok);
    final chunks = <String>[];
    final reload = Completer<void>();
    final subscription = incoming.transform(utf8.decoder).listen((part) {
      chunks.add(part);
      if (chunks.join().contains('data: reload') && !reload.isCompleted) {
        reload.complete();
      }
    });
    addTearDown(subscription.cancel);
    await Future<void>.delayed(const Duration(milliseconds: 100));
    write('index.html', '<h1>After</h1>');
    try {
      await reload.future.timeout(const Duration(seconds: 6));
    } on TimeoutException {
      fail('No reload event received; SSE chunks: $chunks');
    }
  });

  test('failed requests and malformed debug events are reported', () async {
    write('index.html', 'ok');
    final server = await WebDevServer.start(project.path);
    addTearDown(server.stop);
    final error = server.debugStream.first;
    final missing = await request('${server.url}missing.js');
    expect(missing.status, HttpStatus.notFound);
    expect(await error, contains('GET /missing.js'));

    final invalid = await request(
      '${server.url}__webforge/debug',
      method: 'POST',
      body: '{bad json',
    );
    expect(invalid.status, HttpStatus.badRequest);
  });

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

  for (final native in [false, true]) {
    test('real browser bridge captures early head and body events in '
        '${native ? 'Nginx' : 'WebForge'}', () async {
      final executable = native ? await WebRuntime.nginxExecutable() : null;
      if (native && executable == null) {
        markTestSkipped('No desktop Nginx build for the real browser check');
        return;
      }
      final fixtures = _browserBridgeFixtures();
      for (final fixture in fixtures) {
        write(fixture.path, fixture.source);
      }
      final WebRuntimeSession server = native
          ? await NginxSession.start(project.path, executable: executable!)
          : await WebDevServer.start(project.path);
      addTearDown(server.stop);
      expect(server.engineName, native ? startsWith('Nginx ') : 'WebForge');
      final debug = <String>[];
      final subscription = server.debugStream.listen(debug.add);
      addTearDown(subscription.cancel);
      final process = await Process.start('node', [
        'scripts/test_web_console_bridge.mjs',
      ], workingDirectory: Directory.current.path);
      addTearDown(process.kill);
      final output = process.stdout.transform(utf8.decoder).join();
      final errors = process.stderr.transform(utf8.decoder).join();
      process.stdin.writeln(
        jsonEncode({
          'baseUrl': server.url,
          'cases': [
            for (final fixture in fixtures)
              {
                'path': fixture.path,
                'done': fixture.done,
                'expectedPosts': fixture.lines.length,
              },
          ],
        }),
      );
      await process.stdin.close();
      final exitCode = await process.exitCode.timeout(
        const Duration(seconds: 45),
        onTimeout: () {
          process.kill();
          throw TimeoutException('Production browser bridge check timed out');
        },
      );
      final stdout = await output;
      expect(exitCode, 0, reason: '${await errors}\n$stdout');
      final report = jsonDecode(stdout) as Map<String, dynamic>;
      final observations = report['cases'] as List<dynamic>;
      // Keep the red/green evidence in the normal test log without dumping
      // authored HTML or replacing the production stream with harness data.
      debugPrintSynchronously(
        'browser bridge ${server.engineName}: '
        '${jsonEncode({
          'browserVersion': report['browserVersion'],
          'externalRequests': report['externalRequests'],
          'cases': [
            for (final observation in observations) {'path': observation['path'], 'posts': observation['posts'], 'consoleEvents': observation['consoleEvents'], 'errors': observation['errors'], 'dom': observation['dom']},
          ],
          'debugStream': debug,
        })}',
      );
      expect(report['externalRequests'], isEmpty);
      expect(observations, hasLength(fixtures.length));
      for (var index = 0; index < fixtures.length; index++) {
        final fixture = fixtures[index];
        final observation = observations[index] as Map<String, dynamic>;
        final reason = '${server.engineName} ${fixture.path}';
        expect(observation['bridgeCount'], 1, reason: reason);
        expect(
          observation['sourceWithoutBridge'],
          fixture.source,
          reason: '$reason must retain the authored source exactly',
        );
        expect(observation['dom'], fixture.dom, reason: reason);
        if (native) {
          expect(observation['engineHeader'], 'nginx', reason: reason);
        }
        final posts = observation['posts'] as List<dynamic>;
        expect(posts, hasLength(fixture.lines.length), reason: reason);
        for (final post in posts) {
          expect(post['status'], HttpStatus.noContent, reason: reason);
          expect(post['origin'], Uri.parse(server.url).origin, reason: reason);
        }
        for (final line in fixture.lines) {
          expect(
            debug.where((event) => event == line),
            hasLength(1),
            reason: '$reason: $line must reach the production debugStream once',
          );
        }
      }
    }, timeout: const Timeout(Duration(seconds: 60)));
  }

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

  test('engine settings select WebForge and reject unknown engines', () async {
    write('index.html', 'ok');
    write('.qfli/web.json', '{"engine":"webforge"}');
    final server = await WebRuntime.start(project.path);
    addTearDown(server.stop);
    expect(server.engineName, 'WebForge');
    expect((await request(server.url)).status, HttpStatus.ok);
    write('.qfli/web.json', '{"engine":"unknown"}');
    await expectLater(WebRuntime.start(project.path), throwsFormatException);
  });
}

typedef _BrowserBridgeFixture = ({
  String path,
  String source,
  String? done,
  List<String> lines,
  Map<String, Object?> dom,
});

List<_BrowserBridgeFixture> _browserBridgeFixtures() {
  _BrowserBridgeFixture page(
    String id,
    String prefix, {
    String suffix = '',
    String mode = 'CSS1Compat',
    String? headNote,
    bool rawText = false,
    bool crlf = false,
  }) {
    final head =
        '''<script>
console.log('$id-head-log'); console.info('$id-head-info');
Promise.reject(new Error('$id-head-rejection'));
</script><script>throw new Error('$id-head-error');</script>''';
    final body =
        '''<body data-fixture="$id"><p>Authored $id</p><script>
console.warn('$id-body-warn'); console.error('$id-body-error-log');
Promise.reject(new Error('$id-body-rejection'));
</script><script>throw new Error('$id-body-error');</script><script>
setTimeout(() => { console.log('$id-done'); window.__bridgeFixtureDone = '$id'; }, 0);
</script></body>''';
    final source = '$prefix$head$suffix$body';
    return (
      path: '$id.html',
      source: crlf ? source.replaceAll('\n', '\r\n') : source,
      done: id,
      lines: [
        '[web.log] $id-head-log',
        '[web.info] $id-head-info',
        '[web.error] Uncaught Error: $id-head-error',
        '[web.error] Error: $id-head-rejection',
        '[web.warn] $id-body-warn',
        '[web.error] $id-body-error-log',
        '[web.error] Uncaught Error: $id-body-error',
        '[web.error] Error: $id-body-rejection',
        '[web.log] $id-done',
      ],
      dom: {
        'compatMode': mode,
        'fixture': id,
        'headNote': headNote,
        'rawStyle': rawText ? 'body::before{content:"</head>"}' : null,
        'rawScript': rawText ? '{"tag":"</head>"}' : null,
        'bridgeScripts': 1,
      },
    );
  }

  return [
    page('early', '<!doctype html><html><head>', suffix: '</head>'),
    page(
      'comment',
      '<!doctype html><!-- fake <head></head> -->'
          '<html><head data-note="> </head>">',
      suffix: '</head>',
      headNote: '> </head>',
    ),
    page(
      'rawtext',
      '<!doctype html><html><head>'
          '<style id="raw-style">body::before{content:"</head>"}</style>'
          '<title>Literal </head></title>'
          '<script id="raw-script" type="application/json">{"tag":"</head>"}</script>',
      suffix: '</head>',
      rawText: true,
    ),
    page('implicit', '<!doctype html><html lang="zh-CN">'),
    page('fragment', '<!-- fake <head></head> -->', mode: 'BackCompat'),
    page(
      'crlf',
      '\ufeff<!doctype html>\n<!-- 🙂 -->\n<HTML>\n<HEAD\n data-note="🙂 >">\n',
      suffix: '\n</HEAD>\n',
      headNote: '🙂 >',
      crlf: true,
    ),
    for (final source in [
      '<!doctype html>\n<!-- only a comment -->',
      '<!doctype html>\n<!-- unclosed comment',
      '<!-- no doctype, unclosed comment',
    ])
      (
        path: 'empty-${source.length}.htm',
        source: source,
        done: null,
        lines: const <String>[],
        dom: {
          'compatMode': source.startsWith('<!doctype')
              ? 'CSS1Compat'
              : 'BackCompat',
          'fixture': null,
          'headNote': null,
          'rawStyle': null,
          'rawScript': null,
          'bridgeScripts': 1,
        },
      ),
  ];
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
    outgoing.followRedirects = false;
    headers.forEach(outgoing.headers.set);
    if (body != null) outgoing.write(body);
    final incoming = await outgoing.close();
    final text = await utf8.decoder.bind(incoming).join();
    return (status: incoming.statusCode, body: text, headers: incoming.headers);
  } finally {
    client.close(force: true);
  }
}
