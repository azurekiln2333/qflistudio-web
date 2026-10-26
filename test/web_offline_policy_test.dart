import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_web/services/nginx_host.dart';
import 'package:qfli_web/services/nginx_session.dart';
import 'package:qfli_web/services/web_dev_server.dart';
import 'package:qfli_web/services/web_project_config.dart';
import 'package:qfli_web/services/web_runtime.dart';
import 'package:qfli_web/services/web_runtime_session.dart';

import 'web_dev_server_test.dart' show request;

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late Directory project;
  late HttpOverrides? savedOverrides;
  setUp(() {
    savedOverrides = HttpOverrides.current;
    HttpOverrides.global = null;
    project = Directory.systemTemp.createTempSync('webforge-offline-');
    File(
      p.join(project.path, 'index.html'),
    ).writeAsStringSync('<p>offline</p>');
  });
  tearDown(() {
    HttpOverrides.global = savedOverrides;
    project.deleteSync(recursive: true);
  });

  for (final target in [
    'https://example.invalid/api',
    'http://192.168.68.207:3000/',
    'http://0.0.0.0:3000/',
    'http://[::]:3000/',
    'http://[2001:db8::1]/',
    'http://localhost:3000/',
    'http://127.0.0.1.example.invalid/',
    'http://[::ffff:127.0.0.1]/',
  ]) {
    test(
      'saved proxy rejects non-loopback literal $target unchanged',
      () async {
        final configFile = File(p.join(project.path, '.qfli', 'web.json'));
        configFile.parent.createSync();
        final bytes = utf8.encode(
          jsonEncode({
            'proxies': [
              {'prefix': '/api', 'target': target},
            ],
          }),
        );
        configFile.writeAsBytesSync(bytes);

        await expectLater(
          WebRuntime.start(project.path),
          throwsFormatException,
        );
        await expectLater(
          WebDevServer.start(project.path),
          throwsFormatException,
        );
        final host = _UncalledHost();
        await expectLater(
          NginxSession.startWithHost(project.path, host: host),
          throwsFormatException,
        );
        expect(host.calls, 0, reason: 'Reject before invoking a native engine');
        expect(configFile.readAsBytesSync(), bytes);
      },
    );
  }

  test('direct configuration cannot bypass validation or bind first', () async {
    final reservation = await ServerSocket.bind(
      InternetAddress.loopbackIPv4,
      0,
    );
    addTearDown(reservation.close);
    final config = WebProjectConfig(
      root: project.path,
      port: reservation.port,
      spaFallback: false,
      proxies: [
        WebProxyRule(
          prefix: '/api',
          target: Uri.parse('https://example.invalid'),
        ),
      ],
    );
    await expectLater(
      WebDevServer.start(project.path, configuration: config),
      throwsFormatException,
    );
    final host = _UncalledHost();
    await expectLater(
      NginxSession.startWithHost(
        project.path,
        host: host,
        configuration: config,
      ),
      throwsFormatException,
    );
    expect(host.calls, 0);
  });

  test('HTTP and HTTPS numeric loopback configurations remain valid', () {
    for (final target in [
      'http://127.0.0.1:3000/api',
      'http://127.12.34.56:3000/',
      'https://127.0.0.1:3000/',
      'http://[::1]:3000/',
      'https://[0:0:0:0:0:0:0:1]:3000/',
    ]) {
      final config = WebProjectConfig.parse(project.path, {
        'proxies': [
          {'prefix': '/api', 'target': target},
        ],
      });
      expect(config.proxies.single.target, Uri.parse(target));
    }
  });

  test('offline preview still forwards to a real loopback service', () async {
    final upstream = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    addTearDown(() => upstream.close(force: true));
    final seen = <String>[];
    upstream.listen((incoming) async {
      seen.add('${incoming.method} ${incoming.uri}');
      incoming.response.write('local:${incoming.uri.queryParameters['q']}');
      await incoming.response.close();
    });
    final config = WebProjectConfig.parse(project.path, {
      'proxies': [
        {'prefix': '/api', 'target': 'http://127.0.0.1:${upstream.port}/v1'},
      ],
    });
    final server = await WebDevServer.start(
      project.path,
      configuration: config,
    );
    addTearDown(server.stop);
    final result = await request('${server.url}api/items?q=7');
    expect(result.status, HttpStatus.ok);
    expect(result.body, 'local:7');
    expect(seen, ['GET /v1/items?q=7']);
    final url = server.url;
    await server.stop();
    await expectLater(request(url), throwsA(isA<SocketException>()));
  });

  test(
    'WebSocket redirect cannot bypass the literal loopback boundary',
    () async {
      final sentinel = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      addTearDown(() => sentinel.close(force: true));
      var escapedHandshakes = 0;
      sentinel.listen((incoming) async {
        escapedHandshakes++;
        incoming.response.statusCode = HttpStatus.forbidden;
        await incoming.response.close();
      });
      final redirector = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      addTearDown(() => redirector.close(force: true));
      var redirects = 0;
      redirector.listen((incoming) async {
        redirects++;
        incoming.response.statusCode = HttpStatus.found;
        // Resolve only to this test's local sentinel if the old implementation
        // follows the redirect. No external network attempt is needed for red.
        incoming.response.headers.set(
          HttpHeaders.locationHeader,
          'http://localhost:${sentinel.port}/escaped',
        );
        await incoming.response.close();
      });
      final server = await WebDevServer.start(
        project.path,
        configuration: WebProjectConfig.parse(project.path, {
          'proxies': [
            {'prefix': '/api', 'target': 'http://127.0.0.1:${redirector.port}'},
          ],
        }),
      );
      addTearDown(server.stop);
      await expectLater(
        WebSocket.connect(
          '${server.url.replaceFirst('http:', 'ws:')}api/socket',
        ).timeout(const Duration(seconds: 5)),
        throwsA(isA<WebSocketException>()),
      );
      expect(redirects, 1);
      expect(
        escapedHandshakes,
        0,
        reason: 'Reject the redirect before DNS/socket',
      );
    },
  );

  for (final websocket in [false, true]) {
    test(
      '${websocket ? 'WSS' : 'HTTPS'} proxy keeps TLS on the actual socket',
      () async {
        final sentinel = await ServerSocket.bind(
          InternetAddress.loopbackIPv4,
          0,
        );
        addTearDown(sentinel.close);
        final firstBytes = Completer<List<int>>();
        final peers = <Socket>{};
        addTearDown(() {
          for (final peer in peers) {
            peer.destroy();
          }
        });
        sentinel.listen((peer) {
          peers.add(peer);
          peer.listen((bytes) {
            if (!firstBytes.isCompleted) firstBytes.complete(bytes);
            // No certificate, key, altered trust store or remote service is
            // needed to distinguish a real TLS ClientHello from plaintext GET.
            peer.destroy();
          }, onError: (Object _) {});
        });
        final server = await WebDevServer.start(
          project.path,
          configuration: WebProjectConfig.parse(project.path, {
            'proxies': [
              {
                'prefix': '/api',
                'target': 'https://127.0.0.1:${sentinel.port}',
              },
            ],
          }),
        );
        addTearDown(server.stop);
        if (websocket) {
          await expectLater(
            WebSocket.connect(
              '${server.url.replaceFirst('http:', 'ws:')}api/socket',
            ).timeout(const Duration(seconds: 5)),
            throwsA(isA<WebSocketException>()),
          );
        } else {
          final response = await request(
            '${server.url}api',
          ).timeout(const Duration(seconds: 5));
          expect(response.status, greaterThanOrEqualTo(400));
        }
        final bytes = await firstBytes.future.timeout(
          const Duration(seconds: 5),
        );
        expect(bytes.length, greaterThanOrEqualTo(3));
        expect(
          bytes[0],
          0x16,
          reason: 'TLS handshake record, never plaintext HTTP',
        );
        expect(bytes[1], 0x03, reason: 'TLS record protocol version');
      },
    );
  }

  for (final native in [false, true]) {
    test(
      '${native ? 'Nginx' : 'WebForge'} forwards a real IPv6 loopback service',
      () async {
        // Failure to bind ::1 is a visible platform limitation, never evidence
        // that a parsed IPv6 configuration successfully forwarded traffic.
        final HttpServer upstream;
        try {
          upstream = await HttpServer.bind(InternetAddress.loopbackIPv6, 0);
        } on SocketException catch (error) {
          markTestSkipped('IPv6 loopback is unavailable: $error');
          return;
        }
        addTearDown(() => upstream.close(force: true));
        final seen = <String>[];
        upstream.listen((incoming) async {
          seen.add('${incoming.method} ${incoming.uri}');
          incoming.response.write('ipv6:${incoming.uri.queryParameters['q']}');
          await incoming.response.close();
        });
        final executable = native ? await WebRuntime.nginxExecutable() : null;
        if (native && executable == null) {
          markTestSkipped('No desktop Nginx build for the real IPv6 check');
          return;
        }
        final config = WebProjectConfig.parse(project.path, {
          'proxies': [
            {'prefix': '/api', 'target': 'http://[::1]:${upstream.port}/v6'},
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
        final response = await request('${server.url}api/items?q=7');
        expect(response.status, HttpStatus.ok);
        expect(response.body, 'ipv6:7');
        expect(seen, ['GET /v6/items?q=7']);
        if (native) {
          expect(response.headers.value('x-webforge-engine'), 'nginx');
        }
      },
    );

    test(
      '${native ? 'Nginx' : 'WebForge'} strips upstream report policies',
      () async {
        final upstream = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
        addTearDown(() => upstream.close(force: true));
        upstream.listen((incoming) async {
          if (incoming.uri.path == '/redirect') {
            incoming.response.statusCode = HttpStatus.found;
            incoming.response.headers.set(
              HttpHeaders.locationHeader,
              '/preserved-local-target?q=7',
            );
          }
          incoming.response.headers.contentType = ContentType.html;
          incoming.response.headers.set('x-local-upstream', 'preserved');
          incoming.response.headers.set(
            'content-security-policy',
            "default-src 'none'",
          );
          incoming.response.headers.set(
            'content-security-policy-report-only',
            "script-src 'none'; report-uri /report",
          );
          incoming.response.headers.set(
            'reporting-endpoints',
            'remote="/report"',
          );
          incoming.response.headers.set(
            'report-to',
            '{"group":"remote","max_age":60,"endpoints":[{"url":"/report"}]}',
          );
          incoming.response.headers.set(
            'nel',
            '{"report_to":"remote","max_age":60}',
          );
          incoming.response.write('<p>local proxied page</p>');
          await incoming.response.close();
        });
        final executable = native ? await WebRuntime.nginxExecutable() : null;
        if (native && executable == null) {
          markTestSkipped('No desktop Nginx build for the real proxy check');
          return;
        }
        final config = WebProjectConfig.parse(project.path, {
          'proxies': [
            {'prefix': '/api', 'target': 'http://127.0.0.1:${upstream.port}'},
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
        for (final redirect in [false, true]) {
          final response = await request(
            '${server.url}api${redirect ? '/redirect' : ''}',
          );
          expect(response.status, redirect ? HttpStatus.found : HttpStatus.ok);
          expect(response.body, '<p>local proxied page</p>');
          expect(response.headers.value('x-local-upstream'), 'preserved');
          expect(
            response.headers.value(HttpHeaders.locationHeader),
            redirect ? '/preserved-local-target?q=7' : isNull,
          );
          expect(
            response.headers.value('content-security-policy'),
            WebProjectConfig.offlineContentSecurityPolicy,
          );
          for (final header in const [
            'content-security-policy-report-only',
            'reporting-endpoints',
            'report-to',
            'nel',
          ]) {
            expect(response.headers.value(header), isNull, reason: header);
          }
          if (native) {
            expect(response.headers.value('x-webforge-engine'), 'nginx');
          }
        }
      },
    );
  }
}

class _UncalledHost implements NginxHost {
  int calls = 0;
  @override
  Future<String> version() async {
    calls++;
    throw StateError('Offline validation must happen before the host is used');
  }

  @override
  Future<void> validate(Directory prefix) async {
    calls++;
    throw StateError('Offline validation must happen before the host is used');
  }

  @override
  Future<NginxInstance> start(Directory prefix) async {
    calls++;
    throw StateError('Offline validation must happen before the host is used');
  }
}
