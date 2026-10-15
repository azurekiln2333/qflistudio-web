import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:qfli_web/services/web_runtime.dart';
import 'package:qfli_web/services/web_runtime_session.dart';

/// Splits text into fixed-size chunks so each line survives device log
/// truncation limits.
Iterable<String> _chunks(String text, int size) sync* {
  for (var i = 0; i < text.length; i += size) {
    yield text.substring(i, (i + size).clamp(0, text.length));
  }
}

/// Dumps any live embedded-Nginx prefix (access/error logs) for a failed run so
/// a device failure can be diagnosed from the console log alone.
Future<void> _dumpPrefix(String reason) async {
  try {
    await for (final entry in Directory.systemTemp.list()) {
      final name = entry.path.split(Platform.pathSeparator).last;
      if (!name.startsWith('webforge-nginx-')) continue;
      debugPrint('[NGINX_SMOKE] prefix($reason)=${entry.path}');
      for (final log in ['access.log', 'error.log', 'nginx.conf']) {
        final file = File('${entry.path}${Platform.pathSeparator}$log');
        final exists = await file.exists();
        final size = exists ? await file.length() : -1;
        if (!exists) {
          debugPrint('[NGINX_SMOKE] $log=<missing>');
          continue;
        }
        final text = await file.readAsString();
        debugPrint('[NGINX_SMOKE] $log=size:$size');
        for (final chunk in _chunks(text, 400)) {
          debugPrint('[NGINX_SMOKE] $log|$chunk');
        }
      }
      debugPrint(
        '[NGINX_SMOKE] prefix listing=${(await Directory(entry.path).list().map((e) => e.path.split(Platform.pathSeparator).last).toList()).join(',')}',
      );
    }
  } catch (error) {
    debugPrint('[NGINX_SMOKE] prefix dump failed: $error');
  }
}

/// Reports whether recursive [Directory.watch] delivers events in this sandbox.
/// The middleware treats watching as optional; this keeps the smoke honest about
/// whether live reload is exercisable without weakening the other checks.
///
/// Watches an independent probe directory rather than [root]. On Android the
/// Dart VM backs each recursive watch with an inotify instance, and adding a
/// second recursive watch over a tree that already has one (the live WebDevServer
/// watches [root]) trips a VM assertion. The middleware's watch is the real one;
/// this probe only needs to answer "does recursive watching work at all here",
/// so it owns a directory nobody else watches.
Future<bool> _supportsRecursiveWatch(String root) async {
  final probe = Directory('$root/.watch-probe');
  StreamSubscription<FileSystemEvent>? subscription;
  try {
    await probe.create();
    final received = Completer<bool>();
    subscription = probe.watch(recursive: true).listen((event) {
      if (!received.isCompleted) received.complete(true);
    });
    await File('${probe.path}/marker').writeAsString('x');
    return await received.future.timeout(
      const Duration(seconds: 2),
      onTimeout: () => false,
    );
  } on FileSystemException {
    return false;
  } finally {
    await subscription?.cancel();
    if (await probe.exists()) await probe.delete(recursive: true);
  }
}

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
    try {
      check(
        (await logged.timeout(const Duration(seconds: 5))).status == 201,
        'Log',
      );
    } catch (error) {
      await _dumpPrefix('access-log-timeout');
      rethrow;
    }
    final socket = await WebSocket.connect(
      '${session.url.replaceFirst('http:', 'ws:')}api/socket',
    );
    socket.add('echo');
    check(
      await socket.first.timeout(const Duration(seconds: 5)) == 'echo',
      'WS',
    );
    await socket.close();
    // Live reload depends on recursive Directory.watch, which the Dart middleware
    // itself treats as optional. Probe it so an unsupported filesystem skips this
    // single check instead of hiding the real stop/auto results behind a timeout.
    final watchingSupported = await _supportsRecursiveWatch(project.path);
    if (watchingSupported) {
      final events = await (await client.getUrl(
        Uri.parse('${session.url}__webforge/events'),
      )).close();
      final reload = events
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .firstWhere((line) => line == 'data: reload');
      await File('${project.path}/style.css').writeAsString('body{color:blue}');
      await reload.timeout(const Duration(seconds: 5));
    } else {
      debugPrint(
        '[NGINX_SMOKE] SKIP live-reload (recursive watch unsupported)',
      );
    }
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
      '[NGINX_SMOKE] PASS HTML CSS 404 proxy WebSocket '
      '${watchingSupported ? 'SSE' : 'SSE-skipped'} diagnostics log '
      'port-conflict stop restart auto',
    );
  } catch (error, stack) {
    debugPrint('[NGINX_SMOKE] FAIL $error\n$stack');
    // Propagate the failure so a run that logs FAIL cannot exit 0 and be read as
    // a pass (the automated device gate and `flutter run -t tool/nginx_smoke.dart`
    // both rely on this). The `finally` below still performs cleanup.
    rethrow;
  } finally {
    client.close(force: true);
    await session?.stop();
    await upstream?.close(force: true);
    await project.delete(recursive: true);
  }
}
