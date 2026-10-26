import 'package:flutter_test/flutter_test.dart';
import 'package:qfli_web/services/owned_preview_policy.dart';
import 'package:qfli_web/services/web_project_config.dart';

/// Runtime origin used by the owned static preview in these cases.
const String ownedOrigin = 'http://127.0.0.1:3000';
const String ownedOriginV6 = 'http://[::1]:3000';

void main() {
  group('bounds', () {
    test('exposes the agreed broker bounds', () {
      expect(kOwnedPreviewMaxInFlight, 16);
      expect(kOwnedPreviewMaxResponseBytes, 2 * 1024 * 1024);
      expect(kOwnedPreviewMaxRetainedBytes, 16 * 1024 * 1024);
      expect(kOwnedPreviewMaxDebugTextBytes, 128 * 1024);
      expect(kOwnedPreviewRequestDeadline, const Duration(seconds: 5));
      expect(
        kOwnedPreviewMaxRetainedBytes,
        greaterThan(kOwnedPreviewMaxResponseBytes),
      );
    });

    test('extra policy denies the four unowned channels only', () {
      expect(kOwnedPreviewExtraPolicy, contains("connect-src 'none'"));
      expect(kOwnedPreviewExtraPolicy, contains("worker-src 'none'"));
      expect(kOwnedPreviewExtraPolicy, contains("frame-src 'none'"));
      expect(kOwnedPreviewExtraPolicy, contains("form-action 'none'"));
      expect(kOwnedPreviewExtraPolicy, isNot(contains('default-src')));
      expect(kOwnedPreviewExtraPolicy, isNot(contains('script-src')));
    });
  });

  group('classifyOwnedResource allows only the exact session origin', () {
    for (final url in [
      'http://127.0.0.1:3000/',
      'http://127.0.0.1:3000',
      'http://127.0.0.1:3000/index.html',
      'http://127.0.0.1:3000/css/app.css?ver=2',
      'http://127.0.0.1:3000/a/b/c.js',
    ]) {
      test('GET $url', () {
        expect(
          classifyOwnedResource(url: url, method: 'GET', origin: ownedOrigin),
          OwnedPreviewDecision.allow,
        );
      });
    }

    test('HEAD is allowed with an exact method token', () {
      for (final method in ['GET', 'HEAD']) {
        expect(
          classifyOwnedResource(
            url: 'http://127.0.0.1:3000/app.js',
            method: method,
            origin: ownedOrigin,
          ),
          OwnedPreviewDecision.allow,
          reason: method,
        );
      }
    });

    test('a normalized method token is refused', () {
      for (final method in ['get', 'head', 'Head', ' get ', 'GET ']) {
        expect(
          classifyOwnedResource(
            url: 'http://127.0.0.1:3000/app.js',
            method: method,
            origin: ownedOrigin,
          ),
          OwnedPreviewDecision.methodNotAllowed,
          reason: method,
        );
      }
    });

    test('accepts UTF-8 paths and an encoded space', () {
      for (final url in [
        'http://127.0.0.1:3000/%E4%B8%AD%E6%96%87.html',
        'http://127.0.0.1:3000/中文.html',
        'http://127.0.0.1:3000/%E4%B8%AD%E6%96%87%20%E6%96%87%E4%BB%B6.html',
        'http://127.0.0.1:3000/static/%E4%B8%AD%E6%96%87/app.css',
      ]) {
        expect(
          classifyOwnedResource(url: url, method: 'GET', origin: ownedOrigin),
          OwnedPreviewDecision.allow,
          reason: url,
        );
      }
    });

    test('IPv6 loopback origin matches its own resources', () {
      expect(
        classifyOwnedResource(
          url: 'http://[::1]:3000/app.js',
          method: 'GET',
          origin: ownedOriginV6,
        ),
        OwnedPreviewDecision.allow,
      );
    });
  });

  group('classifyOwnedResource refuses foreign origins', () {
    for (final url in [
      'http://127.0.0.1:3001/app.js',
      'http://127.0.0.2:3000/app.js',
      'https://127.0.0.1:3000/app.js',
      'http://127.0.0.1/app.js',
      'http://localhost:3000/app.js',
      'http://127.12.34.56:3000/app.js',
      'http://127.0.0.1.example:3000/app.js',
      'http://127.0.0.1.evil.invalid:3000/app.js',
      'http://[0:0:0:0:0:0:0:1]:3000/app.js',
      'http://[::ffff:127.0.0.1]:3000/app.js',
      'https://example.invalid/app.js',
      'http://192.168.1.10:3000/app.js',
    ]) {
      test('forbids $url', () {
        expect(
          classifyOwnedResource(url: url, method: 'GET', origin: ownedOrigin),
          OwnedPreviewDecision.forbidden,
        );
      });
    }
  });

  group('classifyOwnedResource refuses other methods', () {
    for (final method in [
      'POST',
      'PUT',
      'DELETE',
      'PATCH',
      'OPTIONS',
      'TRACE',
      'CONNECT',
      'post',
      '',
    ]) {
      test('method ${method.isEmpty ? '<empty>' : method}', () {
        expect(
          classifyOwnedResource(
            url: 'http://127.0.0.1:3000/api',
            method: method,
            origin: ownedOrigin,
          ),
          OwnedPreviewDecision.methodNotAllowed,
        );
      });
    }
  });

  group('classifyOwnedResource refuses invalid targets', () {
    for (final url in [
      '',
      '/index.html',
      'index.html',
      '//127.0.0.1:3000/app.js',
      'data:text/html,<p>x</p>',
      'blob:http://127.0.0.1:3000/0b8c',
      'about:blank',
      'file:///sdcard/app.js',
      'resource://rawfile/app.js',
      'javascript:void(0)',
      'ws://127.0.0.1:3000/socket',
      'http://user@127.0.0.1:3000/app.js',
      'http://user:pass@127.0.0.1:3000/app.js',
      'http://127.0.0.1:3000/app.js#frag',
      'http://127.0.0.1:3000/app.js#',
      'http://127.0.0.1:3000\\app.js',
      'http://127.0.0.1:3000/a b.js',
      'http://127.0.0.1:3000/a\tb.js',
      'http://127.0.0.1:3000/a\u0001b.js',
      'http://127.0.0.1:3000/a\u007Fb.js',
      'http://127.0.0.1:3000/a\u0085b.js',
      'http://127.0.0.1:3000/a%00b.js',
      'http://127.0.0.1:3000/a%zzb.js',
      'http://127.0.0.1:3000/a%2',
      'http://127.0.0.1:3000/./app.js',
      'http://127.0.0.1:3000/a/../app.js',
      'http://127.0.0.1:3000/a/..',
      'http://127.0.0.1:3000/a/%2E%2E/b.js',
      'http://127.0.0.1:3000/%2E%2E/b.js',
      'http://127.0.0.1:3000/a%5Cb.js',
      'http://127.0.0.1:3000/.qfli/web.json',
      'http://127.0.0.1:3000/.hidden/chunk.js',
      'http://127.0.0.1:3000/page.html?q=a%00b',
      'http://127.0.0.1:3000/page.html?q=%E4%B8%AD%08',
    ]) {
      test('rejects ${url.isEmpty ? '<empty>' : url}', () {
        expect(
          classifyOwnedResource(url: url, method: 'GET', origin: ownedOrigin),
          OwnedPreviewDecision.invalidTarget,
        );
      });
    }
  });

  group('separator checks stay inside the path', () {
    test('allows encoded separators and dots in a query', () {
      for (final url in [
        'http://127.0.0.1:3000/a%2Eb.js',
        'http://127.0.0.1:3000/page.html?next=%2Fhome',
        'http://127.0.0.1:3000/page.html?p=%2E%2E',
        'http://127.0.0.1:3000/page.html?x=%5C',
        'http://127.0.0.1:3000/page.html?q=a%20b',
        'http://127.0.0.1:3000/page.html?name=%E4%B8%AD%E6%96%87',
      ]) {
        expect(
          classifyOwnedResource(url: url, method: 'GET', origin: ownedOrigin),
          OwnedPreviewDecision.allow,
          reason: url,
        );
      }
    });

    test('refuses an encoded slash in the path only', () {
      for (final url in [
        'http://127.0.0.1:3000/a%2Fb.js',
        'http://127.0.0.1:3000/a%2fb.js',
        'http://127.0.0.1:3000/%2Fetc%2Fpasswd',
        'http://127.0.0.1:3000/a%2F..%2Fb.js',
      ]) {
        expect(
          classifyOwnedResource(url: url, method: 'GET', origin: ownedOrigin),
          OwnedPreviewDecision.invalidTarget,
          reason: url,
        );
      }
    });

    test('allows the .well-known exception', () {
      expect(
        classifyOwnedResource(
          url: 'http://127.0.0.1:3000/.well-known/assetlinks.json',
          method: 'GET',
          origin: ownedOrigin,
        ),
        OwnedPreviewDecision.allow,
      );
    });
  });

  group('classifyOwnedResource refuses invalid origins', () {
    for (final origin in [
      '',
      'localhost:3000',
      'http://localhost:3000',
      'http://127.0.0.1:0',
      'http://127.0.0.1:65536',
      'ws://127.0.0.1:3000',
      'http://127.0.0.1:3000/preview',
      'http://127.0.0.1:3000?q=1',
      'http://127.0.0.1:3000#frag',
      'http://user@127.0.0.1:3000',
      'http://127.0.0.2:3000',
      'http://[0:0:0:0:0:0:0:1]:3000',
    ]) {
      test('origin ${origin.isEmpty ? '<empty>' : origin}', () {
        expect(
          classifyOwnedResource(
            url: 'http://127.0.0.1:3000/app.js',
            method: 'GET',
            origin: origin,
          ),
          OwnedPreviewDecision.invalidTarget,
        );
      });
    }
  });

  group('default ports make an explicit and an omitted port equal', () {
    test('accepts http on the default port either way', () {
      for (final pair in [
        ['http://127.0.0.1', 'http://127.0.0.1/app.js'],
        ['http://127.0.0.1', 'http://127.0.0.1:80/app.js'],
        ['http://127.0.0.1:80', 'http://127.0.0.1/app.js'],
        ['http://127.0.0.1:80', 'http://127.0.0.1:80/app.js'],
      ]) {
        expect(
          classifyOwnedResource(url: pair[1], method: 'GET', origin: pair[0]),
          OwnedPreviewDecision.allow,
          reason: '${pair[0]} vs ${pair[1]}',
        );
      }
    });

    test('accepts https on the default port either way', () {
      for (final pair in [
        ['https://127.0.0.1', 'https://127.0.0.1/app.js'],
        ['https://127.0.0.1', 'https://127.0.0.1:443/app.js'],
        ['https://127.0.0.1:443', 'https://127.0.0.1/app.js'],
      ]) {
        expect(
          classifyOwnedResource(url: pair[1], method: 'GET', origin: pair[0]),
          OwnedPreviewDecision.allow,
          reason: '${pair[0]} vs ${pair[1]}',
        );
      }
    });

    test('still refuses a different effective port or scheme', () {
      for (final pair in [
        ['http://127.0.0.1', 'http://127.0.0.1:3000/app.js'],
        ['http://127.0.0.1:3000', 'http://127.0.0.1/app.js'],
        ['http://127.0.0.1', 'https://127.0.0.1/app.js'],
        ['https://127.0.0.1', 'http://127.0.0.1/app.js'],
        ['https://127.0.0.1', 'https://127.0.0.1:80/app.js'],
        ['http://127.0.0.1:443', 'https://127.0.0.1/app.js'],
      ]) {
        expect(
          classifyOwnedResource(url: pair[1], method: 'GET', origin: pair[0]),
          OwnedPreviewDecision.forbidden,
          reason: '${pair[0]} vs ${pair[1]}',
        );
      }
    });

    test('navigates inside an omitted-port origin', () {
      expect(
        isOwnedNavigationAllowed(
          url: 'http://127.0.0.1/page.html#top',
          origin: 'http://127.0.0.1',
        ),
        isTrue,
      );
      expect(
        isOwnedNavigationAllowed(
          url: 'http://127.0.0.1:8080/page.html',
          origin: 'http://127.0.0.1',
        ),
        isFalse,
      );
    });
  });

  group('classifyOwnedResource decision order', () {
    test('a foreign target reports forbidden before the method', () {
      expect(
        classifyOwnedResource(
          url: 'https://example.invalid/api',
          method: 'POST',
          origin: ownedOrigin,
        ),
        OwnedPreviewDecision.forbidden,
      );
    });

    test('an unparsable target reports invalidTarget before the method', () {
      expect(
        classifyOwnedResource(
          url: 'data:text/plain,hi',
          method: 'POST',
          origin: ownedOrigin,
        ),
        OwnedPreviewDecision.invalidTarget,
      );
    });

    test('an owned target reports methodNotAllowed before allow', () {
      expect(
        classifyOwnedResource(
          url: 'http://127.0.0.1:3000/api',
          method: 'POST',
          origin: ownedOrigin,
        ),
        OwnedPreviewDecision.methodNotAllowed,
      );
    });
  });

  group('isOwnedNavigationAllowed keeps anchors inside the page', () {
    test('allows owned documents', () {
      for (final url in [
        'http://127.0.0.1:3000/',
        'http://127.0.0.1:3000/page.html',
        'http://127.0.0.1:3000/page.html?x=1',
      ]) {
        expect(
          isOwnedNavigationAllowed(url: url, origin: ownedOrigin),
          isTrue,
          reason: url,
        );
      }
    });

    test('allows a same-page anchor', () {
      for (final url in [
        'http://127.0.0.1:3000/page.html#section-2',
        'http://127.0.0.1:3000/#top',
        'http://127.0.0.1:3000/page.html#',
      ]) {
        expect(
          isOwnedNavigationAllowed(url: url, origin: ownedOrigin),
          isTrue,
          reason: url,
        );
      }
    });

    test('refuses a foreign origin even with an anchor', () {
      for (final url in [
        'https://example.invalid/page.html#section-2',
        'http://127.0.0.1:3001/page.html#section-2',
        'http://localhost:3000/page.html#section-2',
      ]) {
        expect(
          isOwnedNavigationAllowed(url: url, origin: ownedOrigin),
          isFalse,
          reason: url,
        );
      }
    });

    test('refuses non-HTTP and malformed destinations', () {
      for (final url in [
        'data:text/html,<p>x</p>',
        'blob:http://127.0.0.1:3000/0b8c',
        'about:blank',
        'file:///data/index.html',
        'resource://rawfile/index.html',
        'javascript:void(0)',
        'http://user@127.0.0.1:3000/page.html',
        'http://127.0.0.1:3000\\page.html',
        'http://127.0.0.1:3000/a/../page.html',
        'http://127.0.0.1:3000/%2E%2E/page.html',
        'http://127.0.0.1:3000/a/%2E%2E/page.html',
        'http://127.0.0.1:3000/a%2F..%2Fpage.html',
        '/page.html',
        '',
      ]) {
        expect(
          isOwnedNavigationAllowed(url: url, origin: ownedOrigin),
          isFalse,
          reason: url,
        );
      }
    });

    test('allows a filename that merely contains dots', () {
      // `a%2E%2E` decodes to the name `a..`, which is not a `..` path segment.
      // Refusing it would reject legitimate authored files such as `a..b.html`.
      for (final url in [
        'http://127.0.0.1:3000/a%2E%2E/page.html',
        'http://127.0.0.1:3000/a..b.html',
        'http://127.0.0.1:3000/v1.2..3/page.html',
        'http://127.0.0.1:3000/中文.html',
        'http://127.0.0.1:3000/%E4%B8%AD%E6%96%87.html',
      ]) {
        expect(
          isOwnedNavigationAllowed(url: url, origin: ownedOrigin),
          isTrue,
          reason: url,
        );
      }
    });

    test('refuses an invalid origin', () {
      expect(
        isOwnedNavigationAllowed(
          url: 'http://127.0.0.1:3000/page.html',
          origin: 'http://localhost:3000',
        ),
        isFalse,
      );
    });
  });

  group('buildOwnedContentSecurityPolicy sends two policy values', () {
    final baseline = WebProjectConfig.offlineContentSecurityPolicy;

    test('keeps the baseline bytes and appends the extra policy', () {
      final policy = buildOwnedContentSecurityPolicy(baseline);
      final parts = policy.split(', ');
      expect(parts, hasLength(2));
      expect(parts.first, baseline);
      expect(parts.last, kOwnedPreviewExtraPolicy);
    });

    test('produces the exact expected header value', () {
      expect(
        buildOwnedContentSecurityPolicy(baseline),
        "default-src 'self' data: blob:; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' blob:; "
        "style-src 'self' 'unsafe-inline' data: blob:; "
        "connect-src 'self' blob:; form-action 'self'; base-uri 'self'; "
        "object-src 'self' data: blob:, "
        "connect-src 'none'; worker-src 'none'; frame-src 'none'; "
        "form-action 'none'",
      );
    });

    test('does not rewrite any baseline directive', () {
      final parts = buildOwnedContentSecurityPolicy(baseline).split(', ');
      // The baseline keeps its own connect-src and form-action values.
      expect(parts.first, contains("connect-src 'self' blob:"));
      expect(parts.first, contains("form-action 'self'"));
      expect(parts.first, contains("script-src 'self' 'unsafe-inline'"));
      // Only the extra value carries the denials.
      expect(parts.last, contains("connect-src 'none'"));
      expect(parts.last, contains("form-action 'none'"));
      expect(parts.last, isNot(contains("connect-src 'self'")));
      expect(parts.last, isNot(contains('data:')));
      expect(parts.last, isNot(contains('blob:')));
      expect(parts.last, isNot(contains('script-src')));
    });

    test('never adds data: to script-src', () {
      final policy = buildOwnedContentSecurityPolicy(baseline);
      final scriptDirective = policy
          .split('; ')
          .firstWhere((directive) => directive.startsWith('script-src'));
      expect(scriptDirective, isNot(contains('data:')));
      expect(
        policy.split(',').length,
        2,
        reason: 'exactly two serialized policies',
      );
    });

    test('refuses an empty base instead of dropping default-src', () {
      expect(() => buildOwnedContentSecurityPolicy(''), throwsArgumentError);
      expect(() => buildOwnedContentSecurityPolicy('   '), throwsArgumentError);
    });

    test('trims a padded base without changing its directives', () {
      final padded = '  $baseline  ';
      final first = buildOwnedContentSecurityPolicy(padded).split(', ').first;
      expect(first, baseline);
    });

    test('refuses a base that smuggles another policy', () {
      for (final base in [
        "$baseline, script-src *",
        '$baseline\n',
        '$baseline\r',
        '$baseline\u0000',
      ]) {
        expect(
          () => buildOwnedContentSecurityPolicy(base),
          throwsArgumentError,
          reason: base.replaceAll('\n', r'\n').replaceAll('\r', r'\r'),
        );
      }
    });
  });
}
