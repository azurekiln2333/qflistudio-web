import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:qfli_web/services/owned_preview_policy.dart';
import 'package:qfli_web/services/owned_preview_resource_broker.dart';
import 'package:qfli_web/services/web_project_config.dart';

void main() {
  late HttpOverrides? previousOverrides;

  setUp(() {
    previousOverrides = HttpOverrides.current;
    HttpOverrides.global = null;
  });
  tearDown(() => HttpOverrides.global = previousOverrides);

  Future<HttpServer> serve(
    FutureOr<void> Function(HttpRequest request) handler,
  ) async {
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    addTearDown(() => server.close(force: true));
    server.listen((request) async {
      try {
        await handler(request);
      } catch (_) {
        // Negative fixtures deliberately observe cancellation by the broker.
        try {
          await request.response.close();
        } catch (_) {}
      }
    });
    return server;
  }

  String originOf(HttpServer server) => 'http://127.0.0.1:${server.port}';

  OwnedPreviewResourceBroker brokerFor(
    HttpServer server, {
    int maxInFlight = 16,
    int maxResponseBytes = 2 << 20,
    int maxRetainedBytes = 16 << 20,
    int maxDebugTextBytes = 128 << 10,
    Duration deadline = const Duration(seconds: 5),
  }) {
    final broker = OwnedPreviewResourceBroker(
      origin: originOf(server),
      maxInFlight: maxInFlight,
      maxResponseBytes: maxResponseBytes,
      maxRetainedBytes: maxRetainedBytes,
      maxDebugTextBytes: maxDebugTextBytes,
      requestDeadline: deadline,
    );
    addTearDown(broker.dispose);
    return broker;
  }

  void expectPolicy(OwnedPreviewResource resource) {
    expect(
      resource.headers['content-security-policy'],
      buildOwnedContentSecurityPolicy(
        WebProjectConfig.offlineContentSecurityPolicy,
      ),
    );
    expect(resource.headers['cache-control'], 'no-store');
    expect(resource.headers['x-content-type-options'], 'nosniff');
  }

  test(
    'fetches exact-origin bytes and retains them until explicit release',
    () async {
      String? encoding;
      final server = await serve((request) async {
        encoding = request.headers.value(HttpHeaders.acceptEncodingHeader);
        request.response.headers.contentType = ContentType.html;
        request.response.write('<h1>Local document</h1>');
        await request.response.close();
      });
      final broker = brokerFor(server);
      final resource = await broker.fetch('${broker.origin}/index.html');
      expect(resource.statusCode, 200);
      expect(utf8.decode(resource.bytes), '<h1>Local document</h1>');
      expect(encoding, 'identity');
      expectPolicy(resource);
      expect(broker.retainedBytes, resource.bytes.length);
      expect(resource.bytes, isA<Uint8List>());
      expect(() => resource.bytes[0] = 0, throwsUnsupportedError);
      expect(utf8.decode(resource.bytes), '<h1>Local document</h1>');
      resource.release();
      resource.release();
      expect(broker.retainedBytes, 0);
      expect(resource.isReleased, isTrue);
      expect(() => resource.bytes, throwsStateError);
    },
  );

  test(
    'refuses another real loopback port before any request reaches it',
    () async {
      final server = await serve((request) => request.response.close());
      var escaped = 0;
      final sentinel = await serve((request) async {
        escaped++;
        await request.response.close();
      });
      final broker = brokerFor(server);
      final result = await broker.fetch('${originOf(sentinel)}/forbidden');
      expect(result.statusCode, 403);
      expectPolicy(result);
      expect(escaped, 0);
      expect(broker.activeRequests, 0);
      expect(broker.retainedBytes, 0);
    },
  );

  test('invalid targets and unsupported methods make no request', () async {
    var hits = 0;
    final server = await serve((request) async {
      hits++;
      await request.response.close();
    });
    final broker = brokerFor(server);
    for (final target in ['file:///secret', '${broker.origin}/page#fragment']) {
      final result = await broker.fetch(target);
      expect(result.statusCode, 400);
      expectPolicy(result);
    }
    for (final method in ['POST', 'get', ' GET ']) {
      final result = await broker.fetch(
        '${broker.origin}/page',
        method: method,
      );
      expect(result.statusCode, 405);
      expectPolicy(result);
    }
    expect(hits, 0);
  });

  test('does not follow a redirect to a second loopback origin', () async {
    var escaped = 0;
    final sentinel = await serve((request) async {
      escaped++;
      await request.response.close();
    });
    final server = await serve((request) async {
      request.response.statusCode = 302;
      request.response.headers.set('location', '${originOf(sentinel)}/escaped');
      await request.response.close();
    });
    final broker = brokerFor(server);
    final result = await broker.fetch('${broker.origin}/redirect');
    expect(result.statusCode, 502);
    expect(result.headers, isNot(contains('location')));
    expectPolicy(result);
    expect(escaped, 0);
  });

  test(
    'rejects same-origin redirects instead of silently changing identity',
    () async {
      var destinationHits = 0;
      final server = await serve((request) async {
        if (request.uri.path == '/target') destinationHits++;
        request.response.statusCode = 302;
        request.response.headers.set('location', '/target');
        await request.response.close();
      });
      final broker = brokerFor(server);
      expect((await broker.fetch('${broker.origin}/redirect')).statusCode, 502);
      expect(destinationHits, 0);
    },
  );

  test(
    'preserves error status but replaces upstream security/reporting headers',
    () async {
      final server = await serve((request) async {
        request.response.statusCode = 404;
        request.response.headers
          ..contentType = ContentType.html
          ..set('content-security-policy', 'default-src *')
          ..set('content-security-policy-report-only', 'report-uri /report')
          ..set('reporting-endpoints', 'default="https://outside.invalid"')
          ..set('report-to', '{"url":"https://outside.invalid"}')
          ..set('nel', '{"report_to":"default"}')
          ..set('set-cookie', 'session=untrusted')
          ..set('refresh', '0; url=https://outside.invalid');
        request.response.write('missing');
        await request.response.close();
      });
      final broker = brokerFor(server);
      final result = await broker.fetch('${broker.origin}/missing');
      expect(result.statusCode, 404);
      expect(utf8.decode(result.bytes), 'missing');
      expectPolicy(result);
      for (final name in [
        'content-security-policy-report-only',
        'reporting-endpoints',
        'report-to',
        'nel',
        'set-cookie',
        'refresh',
      ]) {
        expect(result.headers, isNot(contains(name)));
      }
    },
  );

  test('HEAD forwards its method and returns no retained body', () async {
    String? seenMethod;
    final server = await serve((request) async {
      seenMethod = request.method;
      request.response.headers.contentType = ContentType.text;
      request.response.contentLength = 1000;
      await request.response.close();
    });
    final broker = brokerFor(server, maxResponseBytes: 16);
    final result = await broker.fetch('${broker.origin}/head', method: 'HEAD');
    expect(result.statusCode, 200);
    expect(result.bytes, isEmpty);
    expect(result.headers['content-length'], '0');
    expect(broker.retainedBytes, 0);
    expect(seenMethod, 'HEAD');
  });

  test(
    'rejects a declared overlarge body without retaining its bytes',
    () async {
      final server = await serve((request) async {
        request.response.contentLength = 65;
        request.response.add(List<int>.filled(65, 65));
        await request.response.close();
      });
      final broker = brokerFor(server, maxResponseBytes: 64);
      final result = await broker.fetch('${broker.origin}/large');
      expect(result.statusCode, 413);
      expectPolicy(result);
      await broker.dispose();
      expect(broker.retainedBytes, 0);
      expect(broker.activeRequests, 0);
    },
  );

  test(
    'counts chunked bytes instead of trusting the absent content length',
    () async {
      final server = await serve((request) async {
        request.response.add(List<int>.filled(40, 65));
        await request.response.flush();
        request.response.add(List<int>.filled(40, 66));
        await request.response.close();
      });
      final broker = brokerFor(server, maxResponseBytes: 64);
      expect((await broker.fetch('${broker.origin}/chunks')).statusCode, 413);
      expect(broker.retainedBytes, 0);
    },
  );

  test('applies the smaller debug text bound to HTML', () async {
    final server = await serve((request) async {
      request.response.headers.contentType = ContentType.html;
      request.response.write('123456789');
      await request.response.close();
    });
    final broker = brokerFor(
      server,
      maxResponseBytes: 64,
      maxDebugTextBytes: 8,
    );
    expect((await broker.fetch('${broker.origin}/debug.html')).statusCode, 413);
  });

  test('debug text bound allows larger CSS and plain-text resources', () async {
    final server = await serve((request) async {
      request.response.headers.set(
        'content-type',
        request.uri.path.endsWith('.css') ? 'text/css' : 'text/plain',
      );
      request.response.write('123456789');
      await request.response.close();
    });
    final broker = brokerFor(
      server,
      maxResponseBytes: 64,
      maxDebugTextBytes: 8,
    );
    for (final path in ['/style.css', '/notes.txt']) {
      final result = await broker.fetch('${broker.origin}$path');
      expect(result.statusCode, 200);
      expect(utf8.decode(result.bytes), '123456789');
      result.release();
    }
  });

  test('debug text bound covers JavaScript and MJS response types', () async {
    final server = await serve((request) async {
      request.response.headers.set(
        'content-type',
        request.uri.path.endsWith('.mjs')
            ? 'text/javascript'
            : 'application/javascript',
      );
      request.response.write('123456789');
      await request.response.close();
    });
    final broker = brokerFor(
      server,
      maxResponseBytes: 64,
      maxDebugTextBytes: 8,
    );
    for (final path in ['/main.js', '/module.mjs']) {
      final result = await broker.fetch('${broker.origin}$path');
      expect(result.statusCode, 413);
      expectPolicy(result);
    }
    await broker.dispose();
    expect(broker.activeRequests, 0);
    expect(broker.retainedBytes, 0);
  });

  test(
    'size failure returns its reservation before the next valid request',
    () async {
      final server = await serve((request) async {
        if (request.uri.path == '/large') {
          request.response.add(List<int>.filled(65, 65));
        } else {
          request.response.add([0, 127, 128, 255]);
        }
        await request.response.close();
      });
      final broker = brokerFor(
        server,
        maxInFlight: 1,
        maxResponseBytes: 64,
        maxRetainedBytes: 64,
      );
      expect((await broker.fetch('${broker.origin}/large')).statusCode, 413);
      expect(broker.activeRequests, 0);
      expect(broker.retainedBytes, 0);
      final result = await broker.fetch('${broker.origin}/valid');
      expect(result.statusCode, 200);
      expect(result.bytes, [0, 127, 128, 255]);
      expect(broker.retainedBytes, 4);
      result.release();
      expect(broker.retainedBytes, 0);
      expect(broker.activeRequests, 0);
    },
  );

  test(
    'connection failure does not leave capacity or retained bytes owned',
    () async {
      final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      final origin = originOf(server);
      await server.close(force: true);
      final broker = OwnedPreviewResourceBroker(
        origin: origin,
        maxInFlight: 1,
        maxResponseBytes: 64,
        maxRetainedBytes: 64,
      );
      addTearDown(broker.dispose);
      final result = await broker.fetch('$origin/unreachable');
      expect(result.statusCode, 502);
      expectPolicy(result);
      expect(broker.activeRequests, 0);
      expect(broker.retainedBytes, 0);
      await broker.dispose();
      expect(broker.isDisposed, isTrue);
    },
  );
  test(
    'refuses SSE immediately instead of waiting for its stream to finish',
    () async {
      final server = await serve((request) async {
        request.response.headers.set('content-type', 'text/event-stream');
        request.response.write('data: waiting\n\n');
        await request.response.flush();
      });
      final broker = brokerFor(server);
      final result = await broker
          .fetch('${broker.origin}/events')
          .timeout(const Duration(seconds: 1));
      expect(result.statusCode, 415);
      expectPolicy(result);
    },
  );

  test(
    'rejects compressed upstream bytes despite asking for identity',
    () async {
      final server = await serve((request) async {
        request.response.headers.set('content-encoding', 'gzip');
        request.response.add(gzip.encode(utf8.encode('payload')));
        await request.response.close();
      });
      final broker = brokerFor(server);
      expect((await broker.fetch('${broker.origin}/encoded')).statusCode, 502);
    },
  );

  test('limits concurrent requests until their owned work settles', () async {
    final arrived = Completer<void>();
    final unblock = Completer<void>();
    final server = await serve((request) async {
      if (!arrived.isCompleted) arrived.complete();
      await unblock.future;
      request.response.write('first');
      await request.response.close();
    });
    addTearDown(() {
      if (!unblock.isCompleted) unblock.complete();
    });
    final broker = brokerFor(server, maxInFlight: 1);
    final first = broker.fetch('${broker.origin}/first');
    await arrived.future.timeout(const Duration(seconds: 1));
    final second = await broker.fetch('${broker.origin}/second');
    expect(second.statusCode, 503);
    unblock.complete();
    final result = await first;
    expect(result.statusCode, 200);
    result.release();
  });

  test('retained response leases reserve space until release', () async {
    final server = await serve((request) async {
      request.response.write('12345678');
      await request.response.close();
    });
    final broker = brokerFor(
      server,
      maxResponseBytes: 16,
      maxRetainedBytes: 16,
    );
    final first = await broker.fetch('${broker.origin}/first');
    expect(broker.retainedBytes, 8);
    expect((await broker.fetch('${broker.origin}/blocked')).statusCode, 503);
    first.release();
    expect(
      (await broker.fetch('${broker.origin}/after-release')).statusCode,
      200,
    );
  });

  test(
    'deadline aborts the owned request and releases in-flight accounting',
    () async {
      final server = await serve((request) async {
        if (request.uri.path != '/slow') {
          request.response.write('ready');
          await request.response.close();
          return;
        }
        request.response.write('still waiting');
        await request.response.flush();
      });
      final broker = brokerFor(
        server,
        deadline: const Duration(milliseconds: 200),
      );
      final result = await broker
          .fetch('${broker.origin}/slow')
          .timeout(const Duration(seconds: 1));
      expect(result.statusCode, 504);
      expectPolicy(result);
      expect(broker.activeRequests, 0);
      expect(broker.retainedBytes, 0);
      final recovered = await broker.fetch('${broker.origin}/after-timeout');
      expect(recovered.statusCode, 200);
      expect(utf8.decode(recovered.bytes), 'ready');
      recovered.release();
      await broker.dispose().timeout(const Duration(seconds: 1));
      expect(broker.activeRequests, 0);
      expect(broker.retainedBytes, 0);
    },
  );

  test(
    'dispose revokes leases and cancels pending work without stopping server',
    () async {
      final arrived = Completer<void>();
      var visits = 0;
      final server = await serve((request) async {
        visits++;
        if (request.uri.path == '/slow') {
          if (!arrived.isCompleted) arrived.complete();
          await request.response.flush();
        } else {
          request.response.write('retained');
          await request.response.close();
        }
      });
      final broker = brokerFor(server);
      final lease = await broker.fetch('${broker.origin}/retained');
      final pending = broker.fetch('${broker.origin}/slow');
      await arrived.future.timeout(const Duration(seconds: 1));
      await broker.dispose().timeout(const Duration(seconds: 1));
      expect((await pending).statusCode, 410);
      expect(lease.isReleased, isTrue);
      expect(broker.retainedBytes, 0);
      expect(broker.activeRequests, 0);
      expect(
        (await broker.fetch('${broker.origin}/after-stop')).statusCode,
        410,
      );
      final client = HttpClient();
      addTearDown(() => client.close(force: true));
      final request = await client.getUrl(
        Uri.parse('${originOf(server)}/alive'),
      );
      final response = await request.close();
      expect(await utf8.decoder.bind(response).join(), 'retained');
      expect(visits, 3);
    },
  );

  test(
    'accepts normalized default-port origins without creating a client',
    () async {
      for (final origin in ['http://127.0.0.1', 'https://[::1]']) {
        final broker = OwnedPreviewResourceBroker(origin: origin);
        expect(broker.origin, origin);
        expect(broker.activeRequests, 0);
        await broker.dispose();
      }
    },
  );

  test(
    'rejects invalid origins and limit overrides before creating a client',
    () {
      for (final origin in [
        'http://localhost:3000',
        'http://127.0.0.1:3000/path',
      ]) {
        expect(
          () => OwnedPreviewResourceBroker(origin: origin),
          throwsArgumentError,
        );
      }
      expect(
        () => OwnedPreviewResourceBroker(
          origin: 'http://127.0.0.1:3000',
          maxInFlight: 17,
        ),
        throwsArgumentError,
      );
      expect(
        () => OwnedPreviewResourceBroker(
          origin: 'http://127.0.0.1:3000',
          maxResponseBytes: 32,
          maxRetainedBytes: 16,
        ),
        throwsArgumentError,
      );
      expect(
        () => OwnedPreviewResourceBroker(
          origin: 'http://127.0.0.1:3000',
          requestDeadline: const Duration(seconds: 6),
        ),
        throwsArgumentError,
      );
    },
  );
}
