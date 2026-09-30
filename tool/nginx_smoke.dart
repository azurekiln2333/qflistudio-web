import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:qfli_web/services/web_runtime.dart';
import 'package:qfli_web/services/web_runtime_session.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MaterialApp(home: Scaffold(body: Text('Nginx runtime check'))));
  final project = await Directory.systemTemp.createTemp('nginx-smoke-');
  HttpServer? upstream;
  WebRuntimeSession? session;
  final client = HttpClient();
  try {
    await File(
      '${project.path}/index.html',
    ).writeAsString('<head></head>native');
    await File('${project.path}/style.css').writeAsString('body{color:red}');
    upstream = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    upstream.listen((request) async {
      if (request.uri.path == '/socket') {
        final socket = await WebSocketTransformer.upgrade(request);
        socket.listen(socket.add);
        return;
      }
      request.response.statusCode = HttpStatus.created;
      request.response.write(await utf8.decoder.bind(request).join());
      await request.response.close();
    });
    await Directory('${project.path}/.qfli').create();
    await File('${project.path}/.qfli/web.json').writeAsString(
      jsonEncode({
        'engine': 'nginx',
        'proxies': [
          {'prefix': '/api', 'target': 'http://127.0.0.1:${upstream.port}'},
        ],
      }),
    );
    final path = await WebRuntime.nginxExecutable();
    debugPrint('[NGINX_SMOKE] executable=$path');
    if (Platform.operatingSystem == 'ohos' && path != null) {
      debugPrint(
        '[NGINX_SMOKE] mode=${(await File(path).stat()).mode.toRadixString(8)}',
      );
    }
    session = await WebRuntime.start(project.path);
    void check(bool value, String message) {
      if (!value) throw StateError(message);
    }

    check(session.engineName.startsWith('Nginx '), 'Native engine missing');
    final response = await (await client.getUrl(
      Uri.parse(session.url),
    )).close();
    check(response.statusCode == 200, 'HTML status');
    check(
      response.headers.value('server')!.startsWith('nginx/'),
      'Nginx header',
    );
    check(
      (await utf8.decoder.bind(response).join()).contains('native'),
      'HTML',
    );
    final css = await (await client.getUrl(
      Uri.parse('${session.url}style.css'),
    )).close();
    check((await utf8.decoder.bind(css).join()).contains('color:red'), 'CSS');
    final missing = await (await client.getUrl(
      Uri.parse('${session.url}missing.js'),
    )).close();
    check(missing.statusCode == HttpStatus.notFound, 'Missing asset status');
    await missing.drain<void>();
    final diagnostics = session.debugStream.firstWhere(
      (line) => line.contains('native-diagnostic'),
    );
    final debugRequest = await client.postUrl(
      Uri.parse('${session.url}__webforge/debug'),
    );
    debugRequest.headers.set(
      'origin',
      session.url.replaceFirst(RegExp(r'/$'), ''),
    );
    debugRequest.write('{"message":"native-diagnostic"}');
    await (await debugRequest.close()).drain<void>();
    await diagnostics.timeout(const Duration(seconds: 5));
    final logged = session.requests.firstWhere(
      (event) => event.path == '/api/save',
    );
    final proxy = await client.postUrl(Uri.parse('${session.url}api/save'));
    proxy.write('saved');
    final saved = await proxy.close();
    check(saved.statusCode == 201, 'Proxy status');
    check(await utf8.decoder.bind(saved).join() == 'saved', 'Proxy body');
    check(
      (await logged.timeout(const Duration(seconds: 5))).status == 201,
      'Log',
    );
    final socket = await WebSocket.connect(
      '${session.url.replaceFirst('http:', 'ws:')}api/socket',
    );
    socket.add('echo');
    check(
      await socket.first.timeout(const Duration(seconds: 5)) == 'echo',
      'WS',
    );
    await socket.close();
    final events = await (await client.getUrl(
      Uri.parse('${session.url}__webforge/events'),
    )).close();
    final reload = events
        .transform(utf8.decoder)
        .transform(const LineSplitter())
        .firstWhere((line) => line == 'data: reload');
    await File('${project.path}/style.css').writeAsString('body{color:blue}');
    await reload.timeout(const Duration(seconds: 5));
    await File('${project.path}/.qfli/web.json').writeAsString(
      jsonEncode({'engine': 'nginx', 'port': Uri.parse(session.url).port}),
    );
    var conflict = false;
    try {
      final unexpected = await WebRuntime.start(project.path);
      await unexpected.stop();
    } on SocketException {
      conflict = true;
    }
    check(conflict, 'Occupied port was accepted');
    final url = session.url;
    await session.stop();
    var stopped = false;
    try {
      await (await client.getUrl(Uri.parse(url))).close();
    } on SocketException {
      stopped = true;
    }
    check(stopped, 'Listener remains after stop');
    // Default selection must use the same packaged native runtime.
    await File('${project.path}/.qfli/web.json').writeAsString('{}');
    session = await WebRuntime.start(project.path);
    check(
      session.engineName.startsWith('Nginx '),
      'Automatic native selection',
    );
    await session.stop();
    debugPrint(
      '[NGINX_SMOKE] PASS HTML CSS 404 proxy WebSocket SSE diagnostics log port-conflict stop restart auto',
    );
  } catch (error, stack) {
    debugPrint('[NGINX_SMOKE] FAIL $error\n$stack');
  } finally {
    client.close(force: true);
    await session?.stop();
    await upstream?.close(force: true);
    await project.delete(recursive: true);
  }
}
