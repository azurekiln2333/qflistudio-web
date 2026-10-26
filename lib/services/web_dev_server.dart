import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:html/dom.dart' show DocumentType;
import 'package:html/parser.dart' as html_parser;
import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/services/web_preview_file.dart';

import 'web_project_config.dart';
import 'web_runtime_session.dart';

export 'web_runtime_session.dart' show WebRequestEvent;

class WebDevServer implements WebRuntimeSession, WebFilePreviewSession {
  WebDevServer._(this._server, this.config, this._client, this._publicPort);

  final HttpServer _server;
  final WebProjectConfig config;
  final HttpClient _client;
  final int _publicPort;
  final _requests = StreamController<WebRequestEvent>.broadcast();
  final _debug = StreamController<String>.broadcast();
  final _eventClients = <HttpResponse>{};
  final _webSockets = <WebSocket>{};
  final _debugBuffer = <String>[];
  StreamSubscription<FileSystemEvent>? _watcher;
  Timer? _reloadTimer;
  Timer? _heartbeat;
  bool _stopped = false;

  int get port => _server.port;
  @override
  String get engineName => 'WebForge';
  @override
  String get url => 'http://127.0.0.1:$port/';

  /// Maps a project file to the URL this server serves it at. The real
  /// document root is [config.root], so derived and explicit roots both work.
  @override
  String urlForFile(String absolutePath) => webPreviewUrlForFile(
    baseUrl: url,
    documentRoot: config.root,
    filePath: absolutePath,
  );
  @override
  Stream<WebRequestEvent> get requests => _requests.stream;
  @override
  Stream<String> get debugStream => _debug.stream;
  List<String> get debugBuffer => List.unmodifiable(_debugBuffer);

  static Future<WebDevServer> start(
    String projectPath, {
    WebProjectConfig? configuration,
    int? publicPort,
  }) async {
    final config = configuration ?? await WebProjectConfig.load(projectPath);
    config.validateOffline();
    final server = await HttpServer.bind(
      InternetAddress.loopbackIPv4,
      config.port,
    );
    final instance = WebDevServer._(
      server,
      config,
      HttpClient()
        ..connectionTimeout = const Duration(seconds: 10)
        ..autoUncompress = false
        ..findProxy = ((_) => 'DIRECT')
        ..connectionFactory = (uri, proxyHost, proxyPort) {
          // WebSocket.connect follows HTTP redirects. Check every actual socket
          // destination, including redirects, before DNS or a connection starts.
          final address = InternetAddress.tryParse(uri.host);
          if (proxyHost != null || address == null || !address.isLoopback) {
            throw const SocketException('离线预览只允许连接本机回环 IP 地址');
          }
          // A custom HttpClient factory also owns TLS; HttpClient does not
          // wrap this socket for HTTPS (including converted WSS handshakes).
          return uri.scheme == 'https'
              ? SecureSocket.startConnect(address, uri.port)
              : Socket.startConnect(address, uri.port);
        },
      publicPort ?? server.port,
    );
    server.listen((request) => unawaited(instance._handle(request)));
    instance._watchFiles();
    return instance;
  }

  @override
  Future<void> stop() async {
    if (_stopped) return;
    _stopped = true;
    _reloadTimer?.cancel();
    _heartbeat?.cancel();
    await _watcher?.cancel();
    for (final response in _eventClients.toList()) {
      try {
        await response.close();
      } catch (_) {}
    }
    _eventClients.clear();
    for (final socket in _webSockets.toList()) {
      unawaited(socket.close(WebSocketStatus.goingAway));
    }
    _webSockets.clear();
    _client.close(force: true);
    await _server.close(force: true);
    await _requests.close();
    await _debug.close();
  }

  void _watchFiles() {
    try {
      _watcher = Directory(config.root).watch(recursive: true).listen((event) {
        if (p.split(event.path).any((part) => part == '.qfli')) return;
        _queueReload();
      });
    } on FileSystemException {
      // File watching is optional on filesystems that do not support it.
    }
  }

  void _queueReload() {
    _reloadTimer?.cancel();
    _reloadTimer = Timer(const Duration(milliseconds: 180), () {
      for (final response in _eventClients.toList()) {
        try {
          response.write('data: reload\n\n');
          unawaited(response.flush());
        } catch (_) {
          _eventClients.remove(response);
        }
      }
    });
  }

  Future<void> _handle(HttpRequest request) async {
    final started = DateTime.now();
    request.response.headers.set(
      'Content-Security-Policy',
      WebProjectConfig.offlineContentSecurityPolicy,
    );
    var status = HttpStatus.internalServerError;
    try {
      if (request.uri.path == '/__webforge/events') {
        status = await _events(request);
      } else if (request.uri.path == '/__webforge/debug') {
        status = await _receiveDebug(request);
      } else {
        final proxy = _matchingProxy(request.uri.path);
        status = proxy == null
            ? await _serveFile(request)
            : request.headers.value('upgrade')?.toLowerCase() == 'websocket'
            ? await _proxyWebSocket(request, proxy)
            : await _proxy(request, proxy);
      }
    } on SocketException {
      status = HttpStatus.badGateway;
      await _sendError(request, status, 'Upstream unavailable');
    } on TimeoutException {
      status = HttpStatus.gatewayTimeout;
      await _sendError(request, status, 'Upstream timed out');
    } on WebSocketException {
      status = HttpStatus.badGateway;
      await _sendError(request, status, 'WebSocket upstream unavailable');
    } catch (error) {
      status = HttpStatus.internalServerError;
      if (!_debug.isClosed) _debug.add('[web.server] $error');
      await _sendError(request, status, 'Internal server error');
    } finally {
      if (!_requests.isClosed && request.uri.path != '/__webforge/events') {
        final event = WebRequestEvent(
          request.method,
          request.uri.toString(),
          status,
          DateTime.now().difference(started),
        );
        _requests.add(event);
        if (status >= 400 && !_debug.isClosed) {
          _debug.add('[web.http] $event');
        }
      }
    }
  }

  WebProxyRule? _matchingProxy(String path) {
    for (final rule in config.proxies) {
      if (rule.matches(path)) return rule;
    }
    return null;
  }

  Future<int> _serveFile(HttpRequest request) async {
    if (request.method != 'GET' && request.method != 'HEAD') {
      await _sendError(
        request,
        HttpStatus.methodNotAllowed,
        'Method not allowed',
      );
      return HttpStatus.methodNotAllowed;
    }
    final segments = request.uri.pathSegments.where((s) => s.isNotEmpty);
    if (segments.any(
      (s) =>
          s == '.' ||
          s == '..' ||
          s.contains('/') ||
          s.contains('\\') ||
          s.contains('\x00') ||
          (s.startsWith('.') && s != '.well-known'),
    )) {
      await _sendError(request, HttpStatus.forbidden, 'Forbidden');
      return HttpStatus.forbidden;
    }
    final parts = segments.toList();
    if (parts.isEmpty) {
      parts.addAll(p.split(config.indexFile));
    } else if (request.uri.path.endsWith('/')) {
      parts.add('index.html');
    }
    var file = File(p.joinAll([config.root, ...parts]));
    if (!await file.exists() &&
        config.spaFallback &&
        p.extension(file.path).isEmpty &&
        request.headers
                .value(HttpHeaders.acceptHeader)
                ?.contains('text/html') ==
            true) {
      file = File(p.join(config.root, config.indexFile));
    }
    if (!await file.exists()) {
      await _sendError(request, HttpStatus.notFound, 'Not found');
      return HttpStatus.notFound;
    }
    final resolved = await file.resolveSymbolicLinks();
    if (!p.isWithin(config.root, resolved)) {
      await _sendError(request, HttpStatus.forbidden, 'Forbidden');
      return HttpStatus.forbidden;
    }
    final response = request.response;
    response.headers.contentType = ContentType.parse(_contentType(file.path));
    response.headers.set(HttpHeaders.cacheControlHeader, 'no-store');
    if (request.method == 'GET') {
      if (p.extension(file.path).toLowerCase() case '.html' || '.htm') {
        final bytes = await file.readAsBytes();
        final rendered = _injectBridge(utf8.decode(bytes));
        // UTF-8 decoding consumes the BOM; retain it in the served source.
        if (bytes.length >= 3 &&
            bytes[0] == 0xef &&
            bytes[1] == 0xbb &&
            bytes[2] == 0xbf) {
          response.add(bytes.sublist(0, 3));
        }
        response.add(utf8.encode(rendered));
      } else {
        await response.addStream(file.openRead());
      }
    }
    await response.close();
    return HttpStatus.ok;
  }

  Future<int> _proxy(HttpRequest request, WebProxyRule rule) async {
    final upstream = _upstreamUri(request, rule);
    final outgoing = await _client
        .openUrl(request.method, upstream)
        .timeout(const Duration(seconds: 10));
    outgoing.followRedirects = false;
    final skipped = _hopHeaders(request.headers);
    request.headers.forEach((name, values) {
      if (!skipped.contains(name.toLowerCase()) &&
          name.toLowerCase() != HttpHeaders.hostHeader) {
        outgoing.headers.set(name, values);
      }
    });
    await outgoing.addStream(request);
    final incoming = await outgoing.close().timeout(
      const Duration(seconds: 30),
    );
    final response = request.response;
    response.statusCode = incoming.statusCode;
    final responseSkipped = _hopHeaders(incoming.headers);
    incoming.headers.forEach((name, values) {
      if (!responseSkipped.contains(name.toLowerCase()) &&
          !WebProjectConfig.offlineProxyPolicyHeaders.contains(
            name.toLowerCase(),
          )) {
        response.headers.set(name, values);
      }
    });
    await response.addStream(incoming);
    await response.close();
    return incoming.statusCode;
  }

  Uri _upstreamUri(HttpRequest request, WebProxyRule rule) {
    final suffix = request.uri.path.substring(rule.prefix.length);
    final basePath = rule.target.path.endsWith('/')
        ? rule.target.path.substring(0, rule.target.path.length - 1)
        : rule.target.path;
    return rule.target.replace(
      path: '$basePath$suffix',
      query: request.uri.hasQuery ? request.uri.query : null,
    );
  }

  Future<int> _proxyWebSocket(HttpRequest request, WebProxyRule rule) async {
    final httpUri = _upstreamUri(request, rule);
    final upstreamUri = httpUri.replace(
      scheme: httpUri.scheme == 'https' ? 'wss' : 'ws',
    );
    final skipped = _hopHeaders(request.headers);
    final headers = <String, String>{};
    request.headers.forEach((name, values) {
      if (!skipped.contains(name.toLowerCase()) &&
          name.toLowerCase() != HttpHeaders.hostHeader &&
          !name.toLowerCase().startsWith('sec-websocket-')) {
        headers[name] = values.join(', ');
      }
    });
    final protocolHeader = request.headers.value('sec-websocket-protocol');
    final protocols = protocolHeader == null
        ? <String>[]
        : protocolHeader
              .split(',')
              .map((protocol) => protocol.trim())
              .where((protocol) => protocol.isNotEmpty)
              .toList();
    final upstream = await WebSocket.connect(
      upstreamUri.toString(),
      headers: headers,
      protocols: protocols,
      customClient: _client,
    ).timeout(const Duration(seconds: 10));
    _webSockets.add(upstream);
    late final WebSocket downstream;
    try {
      if (_stopped) throw const SocketException('Server stopped');
      downstream = await WebSocketTransformer.upgrade(
        request,
        protocolSelector: (_) => upstream.protocol,
      );
    } catch (_) {
      _webSockets.remove(upstream);
      await upstream.close();
      rethrow;
    }
    _webSockets.add(downstream);
    downstream.listen(
      (message) {
        if (upstream.readyState == WebSocket.open) upstream.add(message);
      },
      onDone: () {
        _webSockets.remove(downstream);
        unawaited(_closeSocket(upstream, downstream));
      },
      onError: (_) {
        unawaited(_closeSocket(upstream, downstream));
      },
    );
    upstream.listen(
      (message) {
        if (downstream.readyState == WebSocket.open) downstream.add(message);
      },
      onDone: () {
        _webSockets.remove(upstream);
        unawaited(_closeSocket(downstream, upstream));
      },
      onError: (_) {
        unawaited(_closeSocket(downstream, upstream));
      },
    );
    return HttpStatus.switchingProtocols;
  }

  Future<void> _closeSocket(WebSocket target, WebSocket source) async {
    final code = source.closeCode;
    final validCode =
        code == WebSocketStatus.noStatusReceived ||
            code == WebSocketStatus.abnormalClosure ||
            code == WebSocketStatus.reserved1015
        ? null
        : code;
    try {
      await target.close(
        validCode,
        validCode == null ? null : source.closeReason,
      );
    } on WebSocketException {
      // The peer may already have closed while the other side is finishing.
    }
  }

  Future<int> _receiveDebug(HttpRequest request) async {
    if (request.method != 'POST') {
      await _sendError(
        request,
        HttpStatus.methodNotAllowed,
        'Method not allowed',
      );
      return HttpStatus.methodNotAllowed;
    }
    final origin = request.headers.value('origin');
    if (origin != null &&
        origin != 'http://127.0.0.1:$_publicPort' &&
        origin != 'http://localhost:$_publicPort') {
      await _sendError(request, HttpStatus.forbidden, 'Forbidden');
      return HttpStatus.forbidden;
    }
    final bytes = <int>[];
    await for (final chunk in request) {
      bytes.addAll(chunk);
      if (bytes.length > 16384) {
        await _sendError(
          request,
          HttpStatus.requestEntityTooLarge,
          'Too large',
        );
        return HttpStatus.requestEntityTooLarge;
      }
    }
    final Object? value;
    try {
      value = jsonDecode(utf8.decode(bytes));
    } on FormatException {
      await _sendError(request, HttpStatus.badRequest, 'Invalid debug event');
      return HttpStatus.badRequest;
    }
    if (value is! Map || value['message'] is! String) {
      await _sendError(request, HttpStatus.badRequest, 'Invalid debug event');
      return HttpStatus.badRequest;
    }
    final level = value['level'] is String ? value['level'] as String : 'log';
    final message = (value['message'] as String);
    final line =
        '[web.${level.substring(0, level.length.clamp(0, 16))}] '
        '${message.substring(0, message.length.clamp(0, 4000))}';
    _debugBuffer.add(line);
    if (_debugBuffer.length > 500) _debugBuffer.removeRange(0, 100);
    if (!_debug.isClosed) _debug.add(line);
    request.response.statusCode = HttpStatus.noContent;
    await request.response.close();
    return HttpStatus.noContent;
  }

  Future<int> _events(HttpRequest request) async {
    if (request.method != 'GET') {
      await _sendError(
        request,
        HttpStatus.methodNotAllowed,
        'Method not allowed',
      );
      return HttpStatus.methodNotAllowed;
    }
    final response = request.response;
    response.bufferOutput = false;
    response.headers.contentType = ContentType.parse('text/event-stream');
    response.headers.set(HttpHeaders.cacheControlHeader, 'no-store');
    response.write(': connected\n\n');
    await response.flush();
    _eventClients.add(response);
    unawaited(
      response.done.then<void>(
        (_) => _eventClients.remove(response),
        onError: (Object _) => _eventClients.remove(response),
      ),
    );
    _heartbeat ??= Timer.periodic(const Duration(seconds: 15), (_) {
      for (final client in _eventClients.toList()) {
        try {
          client.write(': keepalive\n\n');
          unawaited(client.flush());
        } catch (_) {
          _eventClients.remove(client);
        }
      }
    });
    return HttpStatus.ok;
  }

  Future<void> _sendError(HttpRequest request, int code, String text) async {
    try {
      request.response.statusCode = code;
      request.response.headers.contentType = ContentType.text;
      request.response.write(text);
      await request.response.close();
    } catch (_) {}
  }

  static Set<String> _hopHeaders(HttpHeaders headers) {
    final result = <String>{
      'connection',
      'keep-alive',
      'proxy-authenticate',
      'proxy-authorization',
      'te',
      'trailer',
      'transfer-encoding',
      'upgrade',
    };
    for (final value in headers[HttpHeaders.connectionHeader] ?? const []) {
      for (final item in value.split(',')) {
        result.add(item.trim().toLowerCase());
      }
    }
    return result;
  }

  static String _contentType(String path) =>
      switch (p.extension(path).toLowerCase()) {
        '.html' || '.htm' => 'text/html; charset=utf-8',
        '.css' => 'text/css; charset=utf-8',
        '.js' || '.mjs' => 'text/javascript; charset=utf-8',
        '.json' || '.map' => 'application/json; charset=utf-8',
        '.svg' => 'image/svg+xml',
        '.png' => 'image/png',
        '.jpg' || '.jpeg' => 'image/jpeg',
        '.gif' => 'image/gif',
        '.webp' => 'image/webp',
        '.ico' => 'image/x-icon',
        '.woff' => 'font/woff',
        '.woff2' => 'font/woff2',
        '.wasm' => 'application/wasm',
        '.txt' => 'text/plain; charset=utf-8',
        '.xml' => 'application/xml; charset=utf-8',
        '.pdf' => 'application/pdf',
        _ => 'application/octet-stream',
      };
}

String _injectBridge(String html) {
  final document = html_parser.HtmlParser(
    html,
    generateSpans: true,
    parseMeta: false,
  ).parse();
  final doctype = document.nodes.whereType<DocumentType>().firstOrNull;
  // Install before authored head scripts. HTML5 spans distinguish actual tags
  // from comments, quoted attributes and raw text without serializing the DOM.
  // With an implicit head, stay after the doctype to retain document mode and
  // before any possibly unclosed comment that could swallow the bridge.
  final boundary =
      document.head?.sourceSpan?.end.offset ??
      doctype?.sourceSpan?.end.offset ??
      0;
  // The parser normalizes CRLF to LF. Map this one UTF-16 boundary back to the
  // authored source instead of normalizing or rewriting any of that source.
  var offset = 0;
  for (var index = 0; index < boundary; index++) {
    if (html.codeUnitAt(offset) == 13 &&
        offset + 1 < html.length &&
        html.codeUnitAt(offset + 1) == 10) {
      offset++;
    }
    offset++;
  }
  return html.replaceRange(offset, offset, _bridge);
}

const _bridge = r'''<script>
(() => {
  const send = (level, values) => {
    let message;
    try { message = values.map(value => typeof value === 'string' ? value : JSON.stringify(value)).join(' '); }
    catch (_) { message = String(values); }
    fetch('/__webforge/debug', {method: 'POST', headers: {'content-type': 'application/json'},
      body: JSON.stringify({level, message})}).catch(() => {});
  };
  for (const level of ['log', 'info', 'warn', 'error']) {
    const original = console[level].bind(console);
    console[level] = (...values) => { send(level, values); original(...values); };
  }
  window.addEventListener('error', event => send('error', [event.message]));
  window.addEventListener('unhandledrejection', event => send('error', [String(event.reason)]));
  new EventSource('/__webforge/events').onmessage = event => {
    if (event.data === 'reload') location.reload();
  };
})();
</script>
''';
