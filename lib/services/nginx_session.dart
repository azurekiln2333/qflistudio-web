import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/services/web_preview_file.dart';

import 'nginx_host.dart';
import 'web_dev_server.dart';
import 'web_project_config.dart';
import 'web_runtime_session.dart';

class NginxSession implements WebRuntimeSession, WebFilePreviewSession {
  NginxSession._(
    this._instance,
    this._bridge,
    this._prefix,
    this.port,
    this.version,
  );

  final NginxInstance _instance;
  final WebDevServer _bridge;
  final Directory _prefix;
  final int port;
  final String version;
  final _debug = StreamController<String>.broadcast();
  final _requests = StreamController<WebRequestEvent>.broadcast();
  final _subscriptions = <StreamSubscription<dynamic>>[];
  Timer? _logTimer;
  int _logOffset = 0;
  int _errorOffset = 0;
  Future<void>? _logRead;
  bool _exited = false;
  Future<void>? _stopFuture;

  @override
  String get engineName => 'Nginx $version';
  @override
  String get url => 'http://127.0.0.1:$port/';

  /// Maps a project file to its public URL. The public listener is [url]; the
  /// real document root belongs to the middleware bridge, so an explicit or
  /// derived root resolves exactly as the bridge would serve it.
  @override
  String urlForFile(String absolutePath) => webPreviewUrlForFile(
    baseUrl: url,
    documentRoot: _bridge.config.root,
    filePath: absolutePath,
  );
  @override
  Stream<String> get debugStream => _debug.stream;
  @override
  Stream<WebRequestEvent> get requests => _requests.stream;

  static Future<NginxSession> start(
    String projectPath, {
    required String executable,
    WebProjectConfig? configuration,
  }) => startWithHost(
    projectPath,
    host: ProcessNginxHost(executable),
    configuration: configuration,
  );

  static Future<NginxSession> startWithHost(
    String projectPath, {
    required NginxHost host,
    WebProjectConfig? configuration,
  }) async {
    final config = configuration ?? await WebProjectConfig.load(projectPath);
    final version = await host.version();
    final prefix = await Directory.systemTemp.createTemp('webforge-nginx-');
    WebDevServer? bridge;
    NginxSession? session;
    try {
      final reservation = await ServerSocket.bind(
        InternetAddress.loopbackIPv4,
        config.port,
      );
      final port = reservation.port;
      await reservation.close();
      // The bridge retains project-path protection and browser diagnostics.
      // Plain HTTP proxy routes are handled directly by the native Nginx process.
      bridge = await WebDevServer.start(
        projectPath,
        publicPort: port,
        configuration: WebProjectConfig(
          root: config.root,
          indexFile: config.indexFile,
          port: 0,
          spaFallback: config.spaFallback,
          proxies: config.proxies
              .where((rule) => rule.target.scheme == 'https')
              .toList(),
        ),
      );
      final token = p.basename(prefix.path);
      await Directory(
        p.join(prefix.path, 'temp', 'client'),
      ).create(recursive: true);
      await Directory(
        p.join(prefix.path, 'temp', 'proxy'),
      ).create(recursive: true);
      await File(
        p.join(prefix.path, 'nginx.conf'),
      ).writeAsString(_configuration(config, bridge.port, port, token));
      await host.validate(prefix);
      final instance = await host.start(prefix);
      session = NginxSession._(instance, bridge, prefix, port, version);
      session._listen();
      await session._waitUntilReady(token);
      return session;
    } catch (_) {
      if (session != null) {
        await session.stop();
      } else {
        await bridge?.stop();
        if (await prefix.exists()) await prefix.delete(recursive: true);
      }
      rethrow;
    }
  }

  void _listen() {
    _subscriptions.add(_bridge.debugStream.listen(_emit));
    for (final stream in _instance.output) {
      _subscriptions.add(
        stream
            .transform(const Utf8Decoder(allowMalformed: true))
            .transform(const LineSplitter())
            .listen((line) => _emit('[nginx] $line')),
      );
    }
    _logTimer = Timer.periodic(
      const Duration(milliseconds: 200),
      (_) => unawaited(_readAccessLog()),
    );
    unawaited(
      _instance.exitCode.then(
        (code) {
          _exited = true;
          if (_stopFuture == null) {
            _emit('Nginx 已停止（退出码 $code）');
            unawaited(stop());
          }
        },
        onError: (Object error, StackTrace stack) {
          _emit('Nginx 状态检查失败：$error');
          unawaited(
            stop().catchError((Object error) => _emit('Nginx 停止失败：$error')),
          );
        },
      ),
    );
  }

  void _emit(String line) {
    if (!_debug.isClosed) _debug.add(line);
  }

  Future<void> _waitUntilReady(String token) async {
    final client = HttpClient()
      ..connectionTimeout = const Duration(milliseconds: 300);
    try {
      for (var attempt = 0; attempt < 30; attempt++) {
        if (_exited || _stopFuture != null) throw StateError('Nginx 启动后退出');
        try {
          final outgoing = await client
              .getUrl(Uri.parse('${url}__webforge/health'))
              .timeout(const Duration(milliseconds: 300));
          final incoming = await outgoing.close().timeout(
            const Duration(milliseconds: 300),
          );
          final sessionToken = incoming.headers.value('x-webforge-session');
          await incoming.drain<void>();
          if (sessionToken == token) return;
        } on IOException {
          // Nginx may still be starting its listener.
        } on TimeoutException {
          // Retry within the bounded startup window.
        }
        await Future<void>.delayed(const Duration(milliseconds: 100));
      }
      throw StateError('Nginx 未能启动本地监听');
    } finally {
      client.close(force: true);
    }
  }

  Future<void> _readAccessLog() =>
      _logRead ??= _readLog().whenComplete(() => _logRead = null);

  Future<void> _readErrorLog() async {
    RandomAccessFile? handle;
    try {
      final file = File(p.join(_prefix.path, 'error.log'));
      if (!await file.exists()) return;
      handle = await file.open();
      final length = await handle.length();
      if (length < _errorOffset) _errorOffset = 0;
      await handle.setPosition(_errorOffset);
      final bytes = await handle.read((length - _errorOffset).clamp(0, 65536));
      final newline = bytes.lastIndexOf(10);
      if (newline < 0) return;
      _errorOffset += newline + 1;
      for (final line in const LineSplitter().convert(
        utf8.decode(bytes.sublist(0, newline + 1), allowMalformed: true),
      )) {
        _emit('[nginx] $line');
      }
    } on IOException {
      // The native worker may still be opening its diagnostic file.
    } finally {
      await handle?.close();
    }
  }

  Future<void> _readLog() async {
    await _readErrorLog();
    RandomAccessFile? handle;
    try {
      final file = File(p.join(_prefix.path, 'access.log'));
      if (!await file.exists()) return;
      handle = await file.open();
      final length = await handle.length();
      if (length < _logOffset) _logOffset = 0;
      await handle.setPosition(_logOffset);
      final bytes = await handle.read((length - _logOffset).clamp(0, 65536));
      final lastNewline = bytes.lastIndexOf(10);
      if (lastNewline < 0) return;
      _logOffset += lastNewline + 1;
      for (final line in const LineSplitter().convert(
        utf8.decode(bytes.sublist(0, lastNewline + 1), allowMalformed: true),
      )) {
        try {
          final record = jsonDecode(line) as Map<String, dynamic>;
          final event = WebRequestEvent(
            record['method'] as String,
            record['uri'] as String,
            record['status'] as int,
            Duration(microseconds: ((record['time'] as num) * 1000000).round()),
          );
          if (event.path == '/__webforge/events') continue;
          if (!_requests.isClosed) _requests.add(event);
          if (event.status >= 400) _emit('[nginx.http] $event');
        } on FormatException {
          _emit('[nginx.log] $line');
        }
      }
    } on FileSystemException {
      // The log can disappear during session cleanup.
    } finally {
      await handle?.close();
    }
  }

  @override
  Future<void> stop() => _stopFuture ??= _stop();

  Future<void> _stop() async {
    _logTimer?.cancel();
    await _instance.stop();
    try {
      await _bridge.stop();
    } finally {
      await _readAccessLog();
      for (final subscription in _subscriptions) {
        await subscription.cancel();
      }
      await _debug.close();
      await _requests.close();
      if (await _prefix.exists()) await _prefix.delete(recursive: true);
    }
  }

  static String _quote(String value) =>
      '"${value.replaceAll(r'\', r'\\').replaceAll('"', r'\"').replaceAll(r'$', r'\$').replaceAll('\n', r'\n').replaceAll('\r', r'\r')}"';

  static String _configuration(
    WebProjectConfig config,
    int bridgePort,
    int port,
    String token,
  ) {
    final locations = StringBuffer();
    for (final rule in config.proxies) {
      if (rule.target.scheme == 'https') {
        for (final location in [
          '= ${_quote(rule.prefix)}',
          '^~ ${_quote('${rule.prefix}/')}',
        ]) {
          locations.writeln(
            'location $location { proxy_pass http://127.0.0.1:$bridgePort; }',
          );
        }
        continue;
      }
      final basePath = rule.target.path.endsWith('/')
          ? rule.target.path.substring(0, rule.target.path.length - 1)
          : rule.target.path;
      final exactTarget = rule.target.replace(
        path: basePath.isEmpty ? '/' : basePath,
      );
      final nestedTarget = rule.target.replace(path: '$basePath/');
      locations.writeln(
        'location = ${_quote(rule.prefix)} { proxy_pass ${_quote(exactTarget.toString())}; }',
      );
      locations.writeln(
        'location ^~ ${_quote('${rule.prefix}/')} { proxy_pass ${_quote(nestedTarget.toString())}; }',
      );
    }
    return '''
daemon off;
master_process off;
pid nginx.pid;
error_log stderr warn;
events { worker_connections 256; }
http {
  log_format webforge escape=json '{"method":"\$request_method","uri":"\$request_uri","status":\$status,"time":\$request_time}';
  access_log access.log webforge;
  client_body_temp_path temp/client;
  proxy_temp_path temp/proxy;
  client_max_body_size 64m;
  map \$http_upgrade \$connection_upgrade { default upgrade; '' close; }
  proxy_http_version 1.1;
  proxy_set_header Host \$proxy_host;
  proxy_set_header Upgrade \$http_upgrade;
  proxy_set_header Connection \$connection_upgrade;
  proxy_buffering off;
  proxy_redirect off;
  proxy_connect_timeout 10s;
  proxy_read_timeout 30s;
  server {
    listen 127.0.0.1:$port;
    add_header X-WebForge-Engine nginx always;
    add_header X-WebForge-Session ${_quote(token)} always;
    location = /__webforge/health { empty_gif; access_log off; }
    location = /__webforge/events { proxy_pass http://127.0.0.1:$bridgePort; proxy_read_timeout 1h; }
    location = /__webforge/debug { proxy_pass http://127.0.0.1:$bridgePort; }
    $locations
    location / { proxy_pass http://127.0.0.1:$bridgePort; }
  }
}
''';
  }
}
