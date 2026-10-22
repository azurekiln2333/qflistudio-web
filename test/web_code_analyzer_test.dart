import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/services/code_analysis.dart';
import 'package:qfli_web/services/web_code_analyzer.dart';

void main() {
  late Directory project;
  late String nativeLibrary;

  setUp(() {
    project = Directory.systemTemp.createTempSync('web-code-analyzer-');
    nativeLibrary = _nativeLibraryPath();
    addTearDown(() => project.deleteSync(recursive: true));
  });

  CodeAnalysisRequest request(
    String text, {
    String name = 'index.html',
    String language = 'html',
    int revision = 7,
    List<CodeDocumentSnapshot>? documents,
  }) {
    final active = p.join(project.path, name);
    return CodeAnalysisRequest(
      projectPath: project.path,
      activeFilePath: active,
      language: language,
      revision: revision,
      documents:
          documents ??
          [CodeDocumentSnapshot(path: active, text: text, revision: revision)],
    );
  }

  Future<CodeAnalysisResult> analyze(
    String text, {
    String name = 'index.html',
    String language = 'html',
  }) => WebCodeAnalyzer(
    nativeLibraryPath: nativeLibrary,
  ).analyze(request(text, name: name, language: language));

  test(
    'HTML5 parser checks actual markup and reports a duplicate attribute',
    () async {
      const source =
          '<!doctype html><html><head><title>示例</title></head><body><div id="a" id="b">内容</div></body></html>';
      final result = await analyze(source);
      expect(result.unavailableReason, isNull);
      final diagnostic = result.diagnostics.singleWhere(
        (d) => d.code == 'duplicate-attribute',
      );
      expect(diagnostic.source, 'html5lib');
      expect(diagnostic.filePath, p.join(project.path, 'index.html'));
      expect(diagnostic.startOffset, inInclusiveRange(0, source.length));
      expect(
        diagnostic.endOffset,
        inInclusiveRange(diagnostic.startOffset, source.length),
      );
    },
  );

  test('valid HTML and CSS are actually parsed with no errors', () async {
    final html = await analyze(
      '<!doctype html><html><head><title>ok</title><style>a { color: red; }</style></head><body><a>ok</a></body></html>',
    );
    expect(html.unavailableReason, isNull);
    expect(html.diagnostics, isEmpty);
    final css = await analyze(
      'a:hover { color: rgb(255, 0, 0); margin: 1rem; }',
      name: 'style.css',
      language: 'css',
    );
    expect(css.unavailableReason, isNull);
    expect(css.diagnostics, isEmpty);
  });

  test('CSS parser reports a genuine declaration syntax error', () async {
    const source = '/* 😀 */\r\na { color red; }';
    final result = await analyze(source, name: 'style.css', language: 'css');
    expect(result.unavailableReason, isNull);
    expect(result.diagnostics, isNotEmpty);
    expect(result.diagnostics.every((d) => d.source == 'csslib'), isTrue);
    expect(
      result.diagnostics.first.startOffset,
      greaterThanOrEqualTo(source.indexOf('color')),
    );
  });

  test(
    'real CSS parser accepts supported modern syntax without false marks',
    () async {
      for (final source in [
        '@layer theme { .card { & > .title { color: var(--accent); } } }',
        '.card { color: red; .title { color: blue; } }',
        ':root { --accent: red; --gap: 10px; } a { color: var(--accent); margin: var(--gap); }',
        ':root { --my-data: { a: b }; }',
        '.a { color: oklch(70% 0.2 30); background: color(display-p3 1 0 0 / .7); }',
        '.a { color: color-mix(in oklab, red 30%, blue); }',
        '.a { color: rgb(from var(--accent) r g b / 50%); }',
        '.a { color: rgb(100 120 130 / .5); }',
        '@supports (display: grid) { a { display: grid; } }',
        '@property --angle { syntax: "<angle>"; inherits: false; initial-value: 0deg; }',
      ]) {
        final result = await analyze(
          source,
          name: 'modern.css',
          language: 'css',
        );
        expect(result.unavailableReason, isNull, reason: source);
        expect(result.diagnostics, isEmpty, reason: source);
      }
    },
  );

  test(
    'unsupported valid modern CSS is explicitly incomplete, never a syntax error',
    () async {
      for (final source in [
        '@container sidebar (min-width: 20rem) { .card { display: grid; } }',
        '@scope (.card) { a { color: red; } }',
        '@layer reset, theme;',
        '.a:has(> img) { color: red; }',
        '.a:is(.b,.c) { color: red; }',
        '.a:where(.b > .c) { color: red; }',
        '.a:not(.b,.c) { color: red; }',
        '.a:nth-child(2n of .x) { color: red; }',
        '@media (width >= 40rem) { a { color: red; } }',
        '@media (400px < width < 900px) { a { color: red; } }',
      ]) {
        final result = await analyze(
          source,
          name: 'modern.css',
          language: 'css',
        );
        expect(
          result.unavailableReason,
          contains('csslib 尚不支持'),
          reason: source,
        );
        expect(result.diagnostics, isEmpty, reason: source);
      }
    },
  );

  test(
    'CSS capability detection ignores marker text inside comments and strings',
    () async {
      const source =
          '/* @container x (width > 1px) {} @scope (.x) {} @layer a, b; */ a { content: "@container :has(> img) @media (width > 1px)"; color red; }';
      final result = await analyze(source, name: 'style.css', language: 'css');
      expect(result.unavailableReason, isNull);
      expect(result.diagnostics, isNotEmpty);
      expect(result.diagnostics.every((d) => d.source == 'csslib'), isTrue);
    },
  );

  test(
    'incomplete embedded CSS preserves independently parsed HTML errors',
    () async {
      final result = await analyze(
        '<!doctype html><html><head><title>x</title><style>@scope (.card) { a { color: red; } }</style></head><body><div id=x id=y></div></body></html>',
      );
      expect(result.unavailableReason, contains('@scope'));
      expect(
        result.diagnostics.any((d) => d.code == 'duplicate-attribute'),
        isTrue,
      );
      expect(result.diagnostics.any((d) => d.source == 'csslib'), isFalse);
    },
  );

  test(
    'HTML parser CRLF spans map to the exact original UTF-16 buffer',
    () async {
      const lf =
          '<!doctype html>\n<html><head><title>😀</title></head>\n<body><div id="a" id="b"></div></body></html>';
      final crlf = lf.replaceAll('\n', '\r\n');
      final first = await analyze(lf);
      final second = await analyze(crlf);
      final a = first.diagnostics.singleWhere(
        (d) => d.code == 'duplicate-attribute',
      );
      final b = second.diagnostics.singleWhere(
        (d) => d.code == 'duplicate-attribute',
      );
      expect(b.startOffset, a.startOffset + 2);
      expect(b.endOffset, a.endOffset + 2);
    },
  );

  test('embedded CSS spans retain original CRLF and emoji offsets', () async {
    const prefix =
        '<!doctype html>\r\n<html><head><title>😀</title>\r\n<style>';
    const css = '/* 😀 */\r\na { color red; }';
    final standalone = await analyze(css, name: 'style.css', language: 'css');
    final embedded = await analyze(
      '$prefix$css</style></head><body></body></html>',
    );
    final a = standalone.diagnostics.first;
    final b = embedded.diagnostics.firstWhere((d) => d.source == 'csslib');
    expect(b.startOffset, prefix.length + a.startOffset);
    expect(b.endOffset, prefix.length + a.endOffset);
  });

  test(
    'unsaved buffer wins and diagnostics never write the project file',
    () async {
      final file = File(p.join(project.path, 'style.css'))
        ..writeAsStringSync('a { color: red; }');
      final result = await analyze(
        'a { color red; }',
        name: 'style.css',
        language: 'css',
      );
      expect(result.diagnostics, isNotEmpty);
      expect(file.readAsStringSync(), 'a { color: red; }');
      expect(project.listSync().map((f) => p.basename(f.path)), ['style.css']);
    },
  );

  test(
    'unavailable native backend is explicit and HTML errors are retained',
    () async {
      final result =
          await WebCodeAnalyzer(
            nativeLibraryPath: p.join(project.path, 'missing-library'),
          ).analyze(
            request(
              '<!doctype html><html><head><title>x</title></head><body><div id=x id=y></div><script>const = ;</script></body></html>',
            ),
          );
      expect(result.unavailableReason, contains('QuickJS'));
      expect(
        result.diagnostics.any((d) => d.code == 'duplicate-attribute'),
        isTrue,
      );
    },
  );

  test(
    'JSON script data and external references are never loaded or evaluated',
    () async {
      final result = await analyze(
        '<!doctype html><html><head><title>x</title><link rel="stylesheet" href="https://example.invalid/x.css"></head><body><script type="application/ld+json">{"not":"JavaScript"}</script><script src="https://example.invalid/x.js">const = ;</script></body></html>',
      );
      expect(result.unavailableReason, isNull);
      expect(result.diagnostics, isEmpty);
      expect(project.listSync(), isEmpty);
    },
  );

  test(
    'project confinement, duplicate snapshots and stale revisions fail honestly',
    () async {
      const analyzer = WebCodeAnalyzer();
      final active = p.join(project.path, 'index.html');
      final foreign = p.join(p.dirname(project.path), 'foreign.html');
      for (final docs in [
        [CodeDocumentSnapshot(path: active, text: '', revision: 6)],
        [CodeDocumentSnapshot(path: foreign, text: '', revision: 7)],
        [
          CodeDocumentSnapshot(path: active, text: '', revision: 7),
          CodeDocumentSnapshot(path: active, text: '', revision: 7),
        ],
      ]) {
        final result = await analyzer.analyze(request('', documents: docs));
        expect(result.unavailableReason, isNotNull);
        expect(result.diagnostics, isEmpty);
      }
    },
  );

  test('unsupported language and bounded source return unavailable', () async {
    final unsupported = await analyze(
      '{}',
      name: 'data.json',
      language: 'json',
    );
    expect(unsupported.unavailableReason, isNotNull);
    final large = await analyze(
      '😀' * (256 * 1024),
      name: 'app.js',
      language: 'javascript',
    );
    expect(large.unavailableReason, contains('大小限制'));
  });

  group(
    'real native QuickJS parser',
    () {
      test('valid modern classic and module/import syntax', () async {
        for (final (name, source) in [
          (
            'app.js',
            'class Item { #x = 1; get() { return this.#x; } } const value = new Item()?.get() ?? 0;',
          ),
          (
            'app.mjs',
            'import value from "./missing.js"; export default await value;',
          ),
          (
            'module.js',
            'import "https://example.invalid/never-load.js"; export const value = 1;',
          ),
        ]) {
          final result = await analyze(
            source,
            name: name,
            language: 'javascript',
          );
          expect(result.unavailableReason, isNull, reason: source);
          expect(result.diagnostics, isEmpty, reason: source);
        }
      });

      test(
        'exact JavaScript CRLF/emoji token and EOF insertion ranges',
        () async {
          const source = '// 😀\r\nconst text="😀"; const broken = ;';
          final result = await analyze(
            source,
            name: 'app.js',
            language: 'javascript',
          );
          expect(result.unavailableReason, isNull);
          final error = result.diagnostics.single;
          expect(error.startOffset, source.lastIndexOf(';'));
          expect(error.endOffset, error.startOffset + 1);
          expect(error.code, 'SyntaxError');
          const eof = 'const x = (';
          final insertion = (await analyze(
            eof,
            name: 'app.js',
            language: 'javascript',
          )).diagnostics.single;
          expect(insertion.startOffset, eof.length);
          expect(insertion.endOffset, eof.length);
        },
      );

      test(
        'embedded scripts use exact original offsets and their declared grammar',
        () async {
          const prefix =
              '<!doctype html>\r\n<html><head><title>😀</title></head><body>\r\n<script>';
          const source = '// 😀\r\nconst broken = ;';
          final result = await analyze('$prefix$source</script></body></html>');
          expect(result.unavailableReason, isNull);
          final error = result.diagnostics.singleWhere(
            (d) => d.source.startsWith('QuickJS'),
          );
          expect(error.startOffset, prefix.length + source.lastIndexOf(';'));
          final module = await analyze(
            '<!doctype html><html><head><title>x</title></head><body><script type="module">import "./not-read.js"; export default 1;</script></body></html>',
          );
          expect(module.unavailableReason, isNull);
          expect(module.diagnostics, isEmpty);
        },
      );

      test(
        'throw, infinite loop, fetch and filesystem statements are only compiled',
        () async {
          final result = await analyze(
            'throw Error("never execute"); while(true) {} fetch("https://example.invalid"); require("fs").writeFileSync("must-not-exist", "bad");',
            name: 'app.js',
            language: 'javascript',
          );
          expect(result.unavailableReason, isNull);
          expect(result.diagnostics, isEmpty);
          expect(project.listSync(), isEmpty);
        },
      );

      test(
        'native stack resource failure is unavailable, not a clean parse',
        () async {
          final result = await analyze(
            '(' * 10000,
            name: 'app.js',
            language: 'javascript',
          );
          expect(result.unavailableReason, contains('stack overflow'));
          expect(result.diagnostics, isEmpty);
        },
      );
    },
    skip: !File(_nativeLibraryPath()).existsSync()
        ? 'Build the real desktop parser with scripts/build_web_syntax.py; mobile delivery has a separate runtime gate.'
        : false,
  );
}

String _nativeLibraryPath() =>
    Platform.environment['QFLI_WEB_SYNTAX_LIBRARY'] ??
    p.join(
      Directory.current.path,
      'build',
      'native',
      'web_syntax',
      Platform.isWindows
          ? 'windows'
          : Platform.isMacOS
          ? 'macos'
          : 'linux',
      Platform.isWindows
          ? 'qfli_web_syntax.dll'
          : Platform.isMacOS
          ? 'libqfli_web_syntax.dylib'
          : 'libqfli_web_syntax.so',
    );
