import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'owned_preview_policy.dart';
import 'web_project_config.dart';

/// One intercepted response. Native handoff must release its lease explicitly.
///
/// A caller must finish copying [bytes] before [release]. Keeping an earlier
/// byte reference after release violates the handoff contract. The broker can
/// revoke leases on disposal; it cannot revoke references copied by a caller.
class OwnedPreviewResource {
  OwnedPreviewResource._({
    required this.statusCode,
    required Map<String, String> headers,
    required Uint8List bytes,
    void Function()? onRelease,
  }) : headers = Map<String, String>.unmodifiable(headers),
       _bytes = bytes.asUnmodifiableView(),
       _onRelease = onRelease;

  final int statusCode;
  final Map<String, String> headers;
  Uint8List _bytes;
  static final _emptyBytes = Uint8List(0).asUnmodifiableView();
  void Function()? _onRelease;
  bool _released = false;

  bool get isReleased => _released;

  Uint8List get bytes {
    if (_released) throw StateError('The preview response lease was released');
    return _bytes;
  }

  void release() {
    if (_released) return;
    _released = true;
    _bytes = _emptyBytes;
    final callback = _onRelease;
    _onRelease = null;
    callback?.call();
  }
}

/// Bounded byte broker for the first owned, static preview mode.
///
/// This service does not mount a Web component or prove ArkWeb isolation. Its
/// future caller must disable the runtime reload bridge, reject proxy settings,
/// and enforce native navigation/permission/network controls before loading.
class OwnedPreviewResourceBroker {
  OwnedPreviewResourceBroker({
    required this.origin,
    this.maxInFlight = kOwnedPreviewMaxInFlight,
    this.maxResponseBytes = kOwnedPreviewMaxResponseBytes,
    this.maxRetainedBytes = kOwnedPreviewMaxRetainedBytes,
    this.maxDebugTextBytes = kOwnedPreviewMaxDebugTextBytes,
    this.requestDeadline = kOwnedPreviewRequestDeadline,
    this.debugTextLimit = true,
  }) {
    if (classifyOwnedResource(url: '$origin/', method: 'GET', origin: origin) !=
        OwnedPreviewDecision.allow) {
      throw ArgumentError.value(origin, 'origin', 'Expected a session origin');
    }
    _bounded('maxInFlight', maxInFlight, kOwnedPreviewMaxInFlight);
    _bounded(
      'maxResponseBytes',
      maxResponseBytes,
      kOwnedPreviewMaxResponseBytes,
    );
    _bounded(
      'maxRetainedBytes',
      maxRetainedBytes,
      kOwnedPreviewMaxRetainedBytes,
    );
    _bounded(
      'maxDebugTextBytes',
      maxDebugTextBytes,
      kOwnedPreviewMaxDebugTextBytes,
    );
    if (maxRetainedBytes < maxResponseBytes) {
      throw ArgumentError('The retained bound must hold one response');
    }
    if (requestDeadline <= Duration.zero ||
        requestDeadline > kOwnedPreviewRequestDeadline) {
      throw ArgumentError.value(requestDeadline, 'requestDeadline');
    }
    _policy = buildOwnedContentSecurityPolicy(
      WebProjectConfig.offlineContentSecurityPolicy,
    );
  }

  final String origin;
  final int maxInFlight;
  final int maxResponseBytes;
  final int maxRetainedBytes;
  final int maxDebugTextBytes;
  final Duration requestDeadline;
  final bool debugTextLimit;
  late final String _policy;
  final Set<_BrokerOperation> _active = {};
  final Set<OwnedPreviewResource> _leases = {};
  int _reservedBytes = 0;
  int _retainedBytes = 0;
  bool _disposed = false;
  Future<void>? _disposeFuture;

  int get activeRequests => _active.length;
  int get retainedBytes => _retainedBytes;
  bool get isDisposed => _disposed;

  Future<OwnedPreviewResource> fetch(String url, {String method = 'GET'}) {
    if (_disposed) return Future.value(_error(410, 'Preview session stopped'));
    final decision = classifyOwnedResource(
      url: url,
      method: method,
      origin: origin,
    );
    switch (decision) {
      case OwnedPreviewDecision.invalidTarget:
        return Future.value(_error(400, 'Invalid preview resource target'));
      case OwnedPreviewDecision.forbidden:
        return Future.value(_error(403, 'Resource is outside this preview'));
      case OwnedPreviewDecision.methodNotAllowed:
        return Future.value(_error(405, 'Only GET and HEAD are supported'));
      case OwnedPreviewDecision.allow:
        break;
    }
    if (_active.length >= maxInFlight) {
      return Future.value(_error(503, 'Preview request limit reached'));
    }
    if (_reservedBytes + _retainedBytes + maxResponseBytes > maxRetainedBytes) {
      return Future.value(_error(503, 'Preview retained-byte limit reached'));
    }
    final client = HttpClient()
      ..findProxy = ((_) => 'DIRECT')
      ..autoUncompress = false
      ..connectionTimeout = requestDeadline
      ..connectionFactory = (uri, proxyHost, proxyPort) {
        if (proxyHost != null ||
            classifyOwnedResource(
                  url: uri.toString(),
                  method: 'GET',
                  origin: origin,
                ) !=
                OwnedPreviewDecision.allow) {
          throw const SocketException('Socket is outside the preview origin');
        }
        final address = InternetAddress.tryParse(uri.host);
        if (address == null || !address.isLoopback) {
          throw const SocketException(
            'Preview socket needs a literal loopback',
          );
        }
        return uri.scheme == 'https'
            ? SecureSocket.startConnect(address, uri.port)
            : Socket.startConnect(address, uri.port);
      };
    final operation = _BrokerOperation(client, maxResponseBytes);
    _active.add(operation);
    _reservedBytes += operation.reservedBytes;
    operation.timer = Timer(requestDeadline, () {
      _cancel(operation, 504, 'Preview resource deadline exceeded');
    });
    unawaited(_perform(operation, Uri.parse(url), method));
    return operation.result.future;
  }

  /// Cancels only clients and leases owned by this broker.
  Future<void> dispose() => _disposeFuture ??= _dispose();

  Future<void> _dispose() async {
    _disposed = true;
    final pending = _active.toList();
    for (final operation in pending) {
      _cancel(operation, 410, 'Preview session stopped');
    }
    for (final lease in _leases.toList()) {
      lease.release();
    }
    await Future.wait(pending.map((operation) => operation.settled.future));
  }

  Future<void> _perform(
    _BrokerOperation operation,
    Uri uri,
    String method,
  ) async {
    try {
      final request = await operation.client.openUrl(method, uri);
      operation.request = request;
      if (operation.cancelled) {
        request.abort(const _BrokerCancelled());
        return;
      }
      request
        ..followRedirects = false
        ..persistentConnection = false;
      request.headers.set(HttpHeaders.acceptEncodingHeader, 'identity');
      final incoming = await request.close();
      if (operation.cancelled) return;
      if (incoming.statusCode >= 300 && incoming.statusCode < 400) {
        _cancel(operation, 502, 'Preview redirects are unsupported');
        return;
      }
      if (incoming.statusCode < 200 || incoming.statusCode > 599) {
        _cancel(operation, 502, 'Unsupported preview response status');
        return;
      }
      final encoding = incoming.headers.value(
        HttpHeaders.contentEncodingHeader,
      );
      if (encoding != null && encoding.trim().toLowerCase() != 'identity') {
        _cancel(operation, 502, 'Encoded preview responses are unsupported');
        return;
      }
      final contentType = incoming.headers.contentType;
      final mime =
          contentType?.mimeType.toLowerCase() ?? 'application/octet-stream';
      if (mime == 'text/event-stream') {
        _cancel(operation, 415, 'Streaming preview resources are unsupported');
        return;
      }
      final debugSource =
          mime == 'text/html' ||
          mime == 'application/xhtml+xml' ||
          mime == 'text/javascript' ||
          mime == 'application/javascript' ||
          mime == 'text/ecmascript' ||
          mime == 'application/ecmascript';
      final limit = debugTextLimit && debugSource
          ? (maxDebugTextBytes < maxResponseBytes
                ? maxDebugTextBytes
                : maxResponseBytes)
          : maxResponseBytes;
      if (method != 'HEAD' && incoming.contentLength > limit) {
        _cancel(operation, 413, 'Preview resource exceeds its byte limit');
        return;
      }
      final builder = BytesBuilder();
      if (method != 'HEAD') {
        await for (final chunk in incoming) {
          if (operation.cancelled) return;
          if (builder.length + chunk.length > limit) {
            _cancel(operation, 413, 'Preview resource exceeds its byte limit');
            return;
          }
          builder.add(chunk);
        }
      }
      if (operation.cancelled || _disposed) return;
      _reservedBytes -= operation.reservedBytes;
      operation.reservedBytes = 0;
      final bytes = builder.takeBytes();
      final retainedLength = bytes.length;
      _retainedBytes += retainedLength;
      late final OwnedPreviewResource resource;
      resource = OwnedPreviewResource._(
        statusCode: incoming.statusCode,
        headers: _headers(contentType?.toString() ?? mime, bytes.length),
        bytes: bytes,
        onRelease: () {
          if (_leases.remove(resource)) _retainedBytes -= retainedLength;
        },
      );
      _leases.add(resource);
      operation.response = resource;
    } catch (_) {
      operation.response ??= _error(502, 'Preview resource read failed');
    } finally {
      operation.timer?.cancel();
      operation.client.close(force: true);
      _reservedBytes -= operation.reservedBytes;
      operation.reservedBytes = 0;
      _active.remove(operation);
      operation.response ??= _error(410, 'Preview session stopped');
      operation.settled.complete();
      // Returning a result also promises that its in-flight reservation is gone.
      operation.result.complete(operation.response!);
    }
  }

  void _cancel(_BrokerOperation operation, int status, String message) {
    if (operation.response != null || operation.cancelled) return;
    operation.cancelled = true;
    // abort/close may re-enter the read error path. Claim the outcome first.
    operation.response = _error(status, message);
    operation.request?.abort(const _BrokerCancelled());
    operation.client.close(force: true);
  }

  OwnedPreviewResource _error(int status, String message) {
    final messageBytes = utf8.encode(message);
    final body = messageBytes.length > maxResponseBytes
        ? messageBytes.sublist(0, maxResponseBytes)
        : messageBytes;
    return OwnedPreviewResource._(
      statusCode: status,
      headers: _headers('text/plain; charset=utf-8', body.length),
      bytes: body,
    );
  }

  Map<String, String> _headers(String type, int length) => {
    HttpHeaders.contentTypeHeader: type,
    HttpHeaders.contentLengthHeader: '$length',
    'content-security-policy': _policy,
    HttpHeaders.cacheControlHeader: 'no-store',
    'x-content-type-options': 'nosniff',
  };

  static void _bounded(String name, int value, int maximum) {
    if (value < 1 || value > maximum) {
      throw ArgumentError.value(value, name, 'Expected 1..$maximum');
    }
  }
}

class _BrokerOperation {
  _BrokerOperation(this.client, this.reservedBytes);

  final HttpClient client;
  final result = Completer<OwnedPreviewResource>();
  final settled = Completer<void>();
  OwnedPreviewResource? response;
  HttpClientRequest? request;
  Timer? timer;
  int reservedBytes;
  bool cancelled = false;
}

class _BrokerCancelled implements Exception {
  const _BrokerCancelled();
}
