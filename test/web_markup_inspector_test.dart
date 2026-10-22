import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:html/parser.dart' as html;
import 'package:qfli_web/services/web_markup_inspector.dart';
import 'package:path/path.dart' as p;

void main() {
  List<String> codesOf(Iterable<dynamic> findings) => [
    for (final finding in findings) finding.code as String,
  ];

  group('tag structure', () {
    test('reports a tag closed by the wrong sibling', () {
      final findings = WebMarkupInspector.structureFindings(
        '<div>\n  <span>hi\n</div>',
      );
      expect(codesOf(findings), ['unclosed-tag']);
      expect(findings.single.location.line, 2);
      expect(findings.single.severity.name, 'error');
    });

    test('reports stray end tags and unclosed documents', () {
      expect(codesOf(WebMarkupInspector.structureFindings('</p>')), [
        'stray-end-tag',
      ]);
      expect(codesOf(WebMarkupInspector.structureFindings('<section><div>')), [
        'unclosed-tag',
        'unclosed-tag',
      ]);
    });

    test('tolerates HTML optional end tags and void elements', () {
      final findings = WebMarkupInspector.structureFindings(
        '<ul><li>a<li>b</ul><p>text<p>more<br><img src="a.png">',
      );
      expect(
        findings.where((finding) => finding.severity.name == 'error'),
        isEmpty,
      );
    });

    test('does not parse markup inside script and style raw text', () {
      final findings = WebMarkupInspector.structureFindings(
        '<html><body><script>if (a < b) {}</script></body></html>',
      );
      expect(codesOf(findings), isEmpty);
    });

    test('raw-text end tags require a complete name and a valid boundary', () {
      for (final name in ['script', 'style', 'title', 'textarea']) {
        final source =
            '<$name>text </${name}suffix> still text</${name.toUpperCase()} >';
        expect(
          codesOf(WebMarkupInspector.structureFindings(source)),
          isEmpty,
          reason: name,
        );
        expect(WebMarkupInspector.tags(source).map((tag) => tag.name), [
          name,
          name,
        ]);
        expect(WebMarkupInspector.tags('<$name>text</$name/>'), hasLength(2));
      }
    });

    test('reads attributes with > inside a quoted value', () {
      final tags = WebMarkupInspector.tags(
        '<a href="/x?a=1&amp;b=2" title="a > b">hi</a>',
      );
      expect(tags.first.attribute('title'), 'a > b');
      expect(tags.first.attribute('href'), '/x?a=1&amp;b=2');
    });
  });

  group('accessibility', () {
    test('flags missing lang, title, placeholder alt and labels', () {
      final findings = WebMarkupInspector.accessibilityFindings('''
<html>
<head><meta charset="utf-8"></head>
<body>
<img src="a.png">
<input type="text" id="q">
<label for="name">Name</label><input id="name">
<a href="/x"></a>
</body>
</html>
''');
      final codes = codesOf(findings);
      expect(codes, contains('missing-lang'));
      expect(codes, contains('missing-title'));
      expect(codes, contains('missing-viewport'));
      expect(codes, contains('missing-alt'));
      expect(codes, contains('unlabelled-input'));
      expect(codes, contains('empty-text-target'));
      // The second input has a <label for>, so only one input is unlabelled.
      expect(codes.where((code) => code == 'unlabelled-input'), hasLength(1));
    });

    test('accepts a labelled, described document', () {
      final findings = WebMarkupInspector.accessibilityFindings('''
<html lang="zh-CN">
<head>
  <title>Demo</title>
  <meta name="viewport" content="width=device-width">
</head>
<body>
  <h1>Title</h1>
  <img src="a.png" alt="">
  <a href="/x" aria-label="home"><svg></svg></a>
  <input id="q" aria-label="search">
</body>
</html>
''');
      expect(codesOf(findings), isEmpty);
    });

    test(
      'accepts wrapping labels and rejects empty decorative-image links',
      () {
        final findings = WebMarkupInspector.accessibilityFindings(
          '<label>Name <input></label><a href="x"><img alt=""></a>'
          '<button><span>Save</span></button><a href="x"><img alt="Home"></a>',
        );
        expect(codesOf(findings), ['empty-text-target']);
      },
    );
  });

  group('references', () {
    test(
      'classifies local, site-root, inline, external and escaping paths',
      () {
        final root = p.absolute('/project');
        final inspection = WebMarkupInspector.inspectSource(
          '''
<html lang="en"><head>
  <title>x</title>
  <link rel="stylesheet" href="css/app.css">
  <script src="/js/app.js"></script>
</head>
<body>
  <img src="img/logo.png" alt="logo">
  <img src="img/missing.png" alt="missing">
  <img srcset="img/a.png 1x, img/b.png 2x" alt="set">
  <img src="https://cdn.example.com/x.png" alt="cdn">
  <img src="data:image/gif;base64,R0lGOD" alt="inline">
  <a href="#top">top</a>
  <a href="../../outside.html">outside</a>
</body></html>
''',
          documentPath: p.join(root, 'src', 'index.html'),
          rootPath: root,
          exists: (path) => {
            p.join(root, 'src', 'css', 'app.css'),
            p.join(root, 'js', 'app.js'),
            p.join(root, 'src', 'img', 'logo.png'),
            p.join(root, 'src', 'img', 'a.png'),
            p.join(root, 'src', 'img', 'b.png'),
          }.contains(path),
          readText: (_) => null,
        );

        final byRaw = {
          for (final reference in inspection.references)
            reference.rawValue: reference,
        };
        expect(byRaw['css/app.css']!.kind, WebResourceKind.localFile);
        expect(byRaw['css/app.css']!.resolvedPath, 'src/css/app.css');
        expect(byRaw['css/app.css']!.exists, isTrue);
        expect(byRaw['/js/app.js']!.kind, WebResourceKind.siteRoot);
        expect(byRaw['/js/app.js']!.resolvedPath, 'js/app.js');
        expect(byRaw['img/missing.png']!.kind, WebResourceKind.missing);
        expect(byRaw['img/b.png']!.kind, WebResourceKind.localFile);
        expect(
          byRaw['https://cdn.example.com/x.png']!.kind,
          WebResourceKind.external,
        );
        expect(
          byRaw['data:image/gif;base64,R0lGOD']!.kind,
          WebResourceKind.inline,
        );
        expect(byRaw['../../outside.html']!.kind, WebResourceKind.escaping);
        // Fragment-only anchors are not resources at all.
        expect(byRaw.containsKey('#top'), isFalse);

        expect(inspection.externalCount, 1);
        expect(inspection.missingCount, 1);
        expect(inspection.isOfflineClean, isFalse);
        expect(
          codesOf(inspection.findings),
          containsAll(['external-reference', 'missing-resource']),
        );
      },
    );

    test('follows local stylesheets for url() references', () {
      final root = p.absolute('/project');
      final stylesheet = p.join(root, 'css', 'app.css');
      final inspection = WebMarkupInspector.inspectSource(
        '<html lang="en"><head><title>x</title>'
        '<link rel="stylesheet" href="css/app.css"></head><body></body></html>',
        documentPath: p.join(root, 'index.html'),
        rootPath: root,
        exists: (path) => path == stylesheet,
        readText: (path) => path == stylesheet
            ? '.hero { background: url("../img/hero.png") }'
            : null,
      );
      final cssReference = inspection.references.firstWhere(
        (reference) => reference.element == 'css',
      );
      expect(cssReference.rawValue, '../img/hero.png');
      expect(cssReference.origin, 'css/app.css');
      expect(cssReference.resolvedPath, 'img/hero.png');
      expect(cssReference.kind, WebResourceKind.missing);
      expect(inspection.cssFiles, ['css/app.css']);
    });

    test('reports a missing document instead of throwing', () {
      final inspection = WebMarkupInspector.inspectFile(
        p.join(Directory.systemTemp.path, 'no-such-document.html'),
        rootPath: Directory.systemTemp.path,
      );
      expect(codesOf(inspection.findings), contains('missing-document'));
      expect(inspection.references, isEmpty);
    });

    test('scans a real project file on disk', () {
      final temp = Directory.systemTemp.createTempSync('webforge-markup-');
      addTearDown(() => temp.deleteSync(recursive: true));
      Directory(p.join(temp.path, 'assets')).createSync();
      File(p.join(temp.path, 'assets', 'a.png')).writeAsBytesSync(const [1]);
      File(p.join(temp.path, 'index.html')).writeAsStringSync('''
<html lang="zh-CN">
<head><title>站点</title><meta name="viewport" content="width=device-width"></head>
<body><h1>你好</h1><img src="assets/a.png" alt="图"></body>
</html>
''');
      final inspection = WebMarkupInspector.inspectFile(
        p.join(temp.path, 'index.html'),
        rootPath: temp.path,
      );
      expect(inspection.localCount, 1);
      expect(inspection.missingCount, 0);
      expect(inspection.isOfflineClean, isTrue);
      expect(codesOf(inspection.findings), isEmpty);
    });

    test('missing files and incomplete checks cannot report offline-clean', () {
      final root = p.absolute('/project');
      WebDocumentInspection inspect(String source) =>
          WebMarkupInspector.inspectSource(
            source,
            documentPath: p.join(root, 'index.html'),
            rootPath: root,
            exists: (_) => false,
            readText: (_) => null,
          );
      expect(inspect('<img src="missing.png" alt="">').isOfflineClean, isFalse);
      expect(
        inspect('<base href="/other/"><img src="x.png" alt="">').isOfflineClean,
        isFalse,
      );
      final capped = inspect('<img src="data:image/gif,a" alt="">' * 501);
      expect(capped.references, hasLength(500));
      expect(codesOf(capped.findings), contains('reference-limit'));
      expect(capped.isOfflineClean, isFalse);
      final tooLarge = inspect('x' * (WebMarkupInspector.maxDocumentBytes + 1));
      expect(tooLarge.isOfflineClean, isFalse);
    });

    test(
      'ignores commented CSS URLs, retains data srcset commas and decodes entities',
      () {
        final root = p.absolute('/project');
        final inspection = WebMarkupInspector.inspectSource(
          '<img srcset="data:image/png;base64,AAAA 1x, local.png 2x" alt="">'
          '<img src="local&amp;name.png" alt="">'
          '<style>/* url(https://invalid.test/x) */ .x { content: "url(https://invalid.test/y)"; }</style>',
          documentPath: p.join(root, 'index.html'),
          rootPath: root,
          exists: (path) =>
              path == p.join(root, 'local.png') ||
              path == p.join(root, 'local&name.png'),
          readText: (_) => null,
        );
        expect(inspection.references, hasLength(3));
        expect(inspection.inlineCount, 1);
        expect(inspection.localCount, 2);
        expect(inspection.externalCount, 0);
      },
    );

    test('follows import chains and gives stylesheet source positions', () {
      final root = p.absolute('/project');
      final files = {
        p.join(root, 'first.css'): '@import "second.css";\n.a{color:red}',
        p.join(root, 'second.css'):
            '/* note */\n\n.a {background: url(https://invalid.test/x.png)}',
      };
      final inspection = WebMarkupInspector.inspectSource(
        '<link rel="stylesheet" href="first.css">',
        documentPath: p.join(root, 'index.html'),
        rootPath: root,
        exists: files.containsKey,
        readText: (path) => files[path],
      );
      expect(inspection.cssFiles, ['first.css', 'second.css']);
      expect(inspection.externalCount, 1);
      final external = inspection.references.singleWhere(
        (reference) => reference.isNetwork,
      );
      expect(external.origin, 'second.css');
      expect(external.location.line, 3);
    });

    test(
      'handles invalid UTF-8 and does not read icon links as stylesheets',
      () {
        final temp = Directory.systemTemp.createTempSync(
          'webforge-markup-bytes-',
        );
        addTearDown(() => temp.deleteSync(recursive: true));
        final document = File(p.join(temp.path, 'index.html'));
        File(p.join(temp.path, 'icon.png')).writeAsBytesSync([255, 255]);
        document.writeAsStringSync('<link rel="icon" href="icon.png">');
        expect(
          WebMarkupInspector.inspectFile(
            document.path,
            rootPath: temp.path,
          ).cssFiles,
          isEmpty,
        );
        document.writeAsBytesSync([255, 255]);
        final invalid = WebMarkupInspector.inspectFile(
          document.path,
          rootPath: temp.path,
        );
        expect(codesOf(invalid.findings), contains('unreadable-document'));
        expect(invalid.isOfflineClean, isFalse);
      },
    );

    test('confines document reads and rejects symlinks leaving the root', () {
      final temp = Directory.systemTemp.createTempSync(
        'webforge-markup-confined-',
      );
      addTearDown(() => temp.deleteSync(recursive: true));
      final project = Directory(p.join(temp.path, 'project'))..createSync();
      final outside = Directory(p.join(temp.path, 'outside'))..createSync();
      File(
        p.join(outside.path, 'secret.css'),
      ).writeAsStringSync('.a {color:red}');
      final document = File(p.join(project.path, 'index.html'))
        ..writeAsStringSync('<link rel="stylesheet" href="linked/secret.css">');
      Link(p.join(project.path, 'linked')).createSync(outside.path);
      final inspection = WebMarkupInspector.inspectFile(
        document.path,
        rootPath: project.path,
      );
      expect(inspection.references.single.kind, WebResourceKind.escaping);
      expect(inspection.cssFiles, isEmpty);
      expect(inspection.isOfflineClean, isFalse);
      final wrongRoot = WebMarkupInspector.inspectFile(
        p.join(outside.path, 'secret.css'),
        rootPath: project.path,
      );
      expect(codesOf(wrongRoot.findings), ['escaping-document']);
    });

    test(
      'discovers documents asynchronously without entering excluded directories',
      () async {
        final temp = Directory.systemTemp.createTempSync(
          'webforge-markup-scan-',
        );
        addTearDown(() => temp.deleteSync(recursive: true));
        Directory(
          p.join(temp.path, 'node_modules', 'nested'),
        ).createSync(recursive: true);
        File(
          p.join(temp.path, 'node_modules', 'nested', 'hidden.html'),
        ).writeAsStringSync('hidden');
        File(p.join(temp.path, 'index.html')).writeAsStringSync('visible');
        final scan = await WebMarkupInspector.scanDocuments(temp.path);
        expect(scan.documents, [p.join(temp.path, 'index.html')]);
        expect(scan.truncated, isFalse);
        final inspection = await WebMarkupInspector.inspectFileAsync(
          scan.documents.single,
          rootPath: temp.path,
        );
        expect(inspection.documentPath, scan.documents.single);
      },
    );
  });

  test(
    'document discovery reports its cap instead of claiming a complete scan',
    () async {
      final temp = Directory.systemTemp.createTempSync('webforge-markup-cap-');
      addTearDown(() => temp.deleteSync(recursive: true));
      for (var i = 0; i < 201; i++) {
        File(p.join(temp.path, '$i.html')).writeAsStringSync('document');
      }
      final scan = await WebMarkupInspector.scanDocuments(temp.path);
      expect(scan.documents, hasLength(200));
      expect(scan.truncated, isTrue);
    },
  );

  group('formatHtml', () {
    test(
      'preserves root-level inline fragments and intentional separators',
      () {
        for (final source in [
          '<span>A</span><span>B</span>',
          '<span>A</span> <span>B</span>',
          'first <b>bold</b> tail',
        ]) {
          final formatted = WebMarkupInspector.formatHtml(source);
          expect(formatted, source);
          expect(
            html.parseFragment(formatted).text,
            html.parseFragment(source).text,
          );
        }
      },
    );

    test('re-indents tags block by block', () {
      final formatted = WebMarkupInspector.formatHtml(
        '<html><head><title>x</title></head><body><p>hi</p><br></body></html>',
      );
      expect(
        formatted,
        [
          '<html>',
          '  <head>',
          '    <title>x</title>',
          '  </head>',
          '  <body>',
          '    <p>hi</p>',
          '    <br>',
          '  </body>',
          '</html>',
        ].join('\n'),
      );
    });

    test(
      'preserves inline spacing, raw script strings, textarea and pre text',
      () {
        const source =
            '<html><body><div><span>A</span><span>B</span> '
            '<em>C</em></div><script>const x = `\n  keep  spaces\n`;</script>'
            '<pre>  first\n    second\n</pre><textarea>  text\n next</textarea></body></html>';
        final formatted = WebMarkupInspector.formatHtml(source);
        final before = html.parse(source);
        final after = html.parse(formatted);
        for (final selector in ['div', 'script', 'pre', 'textarea']) {
          expect(
            after.querySelector(selector)!.text,
            before.querySelector(selector)!.text,
            reason: selector,
          );
        }
        expect(formatted, contains('<span>A</span><span>B</span> <em>C</em>'));
        expect(WebMarkupInspector.formatHtml(formatted), formatted);
        const malformed = '<div><span>unfinished';
        expect(WebMarkupInspector.formatHtml(malformed), malformed);
      },
    );
  });
}
