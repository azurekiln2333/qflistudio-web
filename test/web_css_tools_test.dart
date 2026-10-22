import 'package:flutter_test/flutter_test.dart';
import 'package:qfli_web/services/web_css_tools.dart';
import 'package:qfli_web/services/web_source_scan.dart';

void main() {
  group('CssColor', () {
    test('parses every CSS hex length', () {
      expect(CssColor.parse('#fff')!.hex, '#FFFFFF');
      expect(CssColor.parse('#0f08')!.alpha, closeTo(0.53, 0.01));
      expect(CssColor.parse('#336699')!.rgb, 'rgb(51, 102, 153)');
      expect(CssColor.parse('#336699CC')!.hex, '#336699CC');
      expect(CssColor.parse('336699'), isNull);
    });

    test('parses rgb/rgba with commas, spaces and slashes', () {
      expect(CssColor.parse('rgb(255, 0, 0)')!.hex, '#FF0000');
      expect(CssColor.parse('rgb(100% 0% 0%)')!.hex, '#FF0000');
      expect(CssColor.parse('rgba(0, 0, 255, 0.5)')!.alpha, 0.5);
      expect(CssColor.parse('rgb(0 128 0 / 50%)')!.hex, '#00800080');
      expect(CssColor.parse('rgb(300, -8, 12)')!.hex, '#FF000C');
    });

    test('parses hsl() using the CSS algorithm', () {
      expect(CssColor.parse('hsl(120, 100%, 25%)')!.hex, '#008000');
      expect(CssColor.parse('hsl(0deg 100% 50%)')!.hex, '#FF0000');
      expect(CssColor.parse('hsl(0.5turn 100% 50%)')!.hex, '#00FFFF');
    });

    test('parses named colours and transparent, rejects unknown values', () {
      expect(cssNamedColorCount, 148);
      expect(CssColor.parse('rebeccapurple')!.hex, '#663399');
      expect(CssColor.parse('DarkSlateGray')!.hex, '#2F4F4F');
      expect(CssColor.parse('transparent')!.alpha, 0);
      expect(CssColor.parse('color-mix(in srgb, red, blue)'), isNull);
      expect(CssColor.parse('notacolour'), isNull);
    });

    test('computes WCAG contrast ratios', () {
      final black = CssColor.parse('#000')!;
      final white = CssColor.parse('#fff')!;
      expect(CssColor.contrastRatio(black, white), closeTo(21, 0.01));
      expect(CssColor.contrastRatio(white, white), closeTo(1, 0.01));
      final gray = CssColor.parse('#777777')!;
      expect(CssColor.contrastRatio(gray, white), closeTo(4.48, 0.02));
      expect(
        CssColor.contrastRatio(CssColor.parse('rgba(0,0,0,0.5)')!, white),
        isNull,
      );
    });

    test(
      'rejects malformed and non-finite colour functions without throwing',
      () {
        for (final value in [
          'rgb(1 2 3) garbage',
          'rgba(1, 2, 3, nope)',
          'rgb(1 2, 3)',
          'rgb(100%, 0, 0)',
          'rgb(NaN 0 0)',
          'hsl(infinity 50% 50%)',
          'rgb(1 2 3 / NaN)',
          'rgb(1,,2,3)',
        ]) {
          expect(CssColor.parse(value), isNull, reason: value);
        }
        expect(CssColor.parse('hsl(200grad 100% 50%)')!.hex, '#00FFFF');
      },
    );
  });

  group('WebCssTools.findColors', () {
    test('finds hex, rgb, hsl and named colours in source order', () {
      final uses = WebCssTools.findColors('''
.a { color: #fff; background: rgb(0, 0, 0); }
.b { border-color: rebeccapurple; outline-color: hsl(120, 100%, 25%); }
''');
      expect(uses.map((use) => use.color.hex), [
        '#FFFFFF',
        '#000000',
        '#663399',
        '#008000',
      ]);
      // The first colour sits on the first source line, after `.a { color: `.
      expect(uses.first.location.line, 1);
      expect(uses.first.location.column, 13);
      expect(uses[2].location.line, 2);
    });

    test('ignores colour-looking text inside strings and comments', () {
      final uses = WebCssTools.findColors(
        '.a::after { content: "#fff"; } /* #000 */ .b { color: red; }',
      );
      expect(uses.map((use) => use.raw), ['red']);
    });

    test(
      'does not mistake selectors, properties or URL fragments for colours',
      () {
        final uses = WebCssTools.findColors(
          '#fff, red, .blue { --red: green; background: url(red.svg#fff); '
          'content: "/* #fff */"; color: red; }',
        );
        expect(uses.map((use) => use.raw), ['green', 'red']);
      },
    );
  });

  group('specificity', () {
    List<String> of(String selector) => [
      for (final entry in WebCssTools.specificities('$selector { color: red }'))
        entry.label,
    ];

    test('counts ids, classes/attributes/pseudo-classes and types', () {
      expect(of('#nav .item a:hover'), ['(1, 2, 1)']);
      expect(of('ul#nav li.item > a:hover::before'), ['(1, 2, 4)']);
      expect(of('*'), ['(0, 0, 0)']);
      expect(of('[type="text"] + input'), ['(0, 1, 1)']);
    });

    test('treats :where() as zero and :not() by its argument', () {
      expect(of(':where(#a, .b) div'), ['(0, 0, 1)']);
      expect(of(':not(.x) p'), ['(0, 1, 1)']);
    });

    test('splits selector lists and reports the rule position', () {
      final entries = WebCssTools.specificities(
        '.a, #b > p {\n  color: red;\n}',
      );
      expect(entries.map((entry) => entry.selector), ['.a', '#b > p']);
      expect(entries.last.location.line, 1);
    });

    test(
      'honours namespaces, legacy pseudo-elements and nth-child of lists',
      () {
        expect(of('svg|a:before'), ['(0, 0, 2)']);
        expect(of('*|a'), ['(0, 0, 1)']);
        expect(of('svg|*'), ['(0, 0, 0)']);
        expect(of(':nth-child(2n of .x, #main) > p'), ['(1, 1, 1)']);
        expect(of('[title="]"]::after'), ['(0, 1, 1)']);
        expect(of('::slotted(.item)'), ['(0, 1, 1)']);
        expect(of(':host(.active)'), ['(0, 2, 0)']);
        expect(of('& .child'), ['依赖嵌套父规则，未计算']);
        final entries = WebCssTools.specificities(
          '${'.x' * 101}, #main { color: red }',
        );
        expect(entries[1].compareTo(entries[0]), greaterThan(0));
      },
    );
  });

  group('duplicate declarations', () {
    test('reports the same property twice in one rule', () {
      final duplicates = WebCssTools.duplicateDeclarations(
        '.a {\n  color: red;\n  margin: 0;\n  color: blue;\n}',
      );
      expect(duplicates, hasLength(1));
      expect(duplicates.single.property, 'color');
      expect(duplicates.single.occurrences, hasLength(2));
      expect(duplicates.single.occurrences.last.location.line, 4);
    });
  });

  group('box model', () {
    CssBoxModel? modelOf(String css, {double? width, double? height}) {
      final sheet = WebCssTools.parse(css);
      return WebCssTools.boxModel(
        sheet.rules.first.declarations,
        contentWidth: width,
        contentHeight: height,
      );
    }

    test('expands the 1-4 value shorthand', () {
      final model = modelOf('.a { padding: 10px 20px 30px; }')!;
      expect(model.padding!.top, '10px');
      expect(model.padding!.right, '20px');
      expect(model.padding!.bottom, '30px');
      expect(model.padding!.left, '20px');
      expect(model.padding!.horizontalPx, 40);
    });

    test('adds content, padding, border and margin in content-box', () {
      final model = modelOf(
        '.a { padding: 10px 20px; border-width: 2px; border-style: solid; margin: 5px; }',
        width: 100,
        height: 50,
      )!;
      expect(model.outerWidth(), 100 + 40 + 4);
      expect(model.outerWidth(includeMargin: true), 154);
      expect(model.outerHeight(includeMargin: true), 50 + 20 + 4 + 10);
    });

    test('honours border-box and refuses to convert non-px units', () {
      final borderBox = modelOf(
        '.a { box-sizing: border-box; padding: 10px; border-width: 2px; }',
        width: 100,
      )!;
      expect(borderBox.isBorderBox, isTrue);
      expect(borderBox.outerWidth(), 100);

      final rem = modelOf('.a { padding: 1rem; }', width: 100)!;
      expect(rem.outerWidth(), isNull);
      expect(rem.toRows().any((row) => row.$2.contains('无法换算')), isTrue);
    });

    test(
      'resolves shorthand/longhand order, important, zero and border style',
      () {
        final model = modelOf(
          '.a { padding: 10px !important; '
          'padding-left: 50px; margin: 0; border: 2px solid red; '
          'border-right-style: none; }',
          width: 100,
        )!;
        expect(model.padding!.left, '10px');
        expect(model.margin!.horizontalPx, 0);
        expect(model.borderWidth!.horizontalPx, 2);
        expect(model.outerWidth(includeMargin: true), 122);
        expect(
          modelOf('.a {border-width: 10px}', width: 100)!.outerWidth(),
          100,
        );
        expect(
          modelOf('.a {padding: calc(1px + 2px) 5px}')!.padding!.top,
          'calc(1px + 2px)',
        );
        final minimum = modelOf(
          '.a {box-sizing:border-box;padding:100px}',
          width: 20,
        )!;
        expect(minimum.outerWidth(), 200);
      },
    );
  });

  group('stylesheet diagnostics', () {
    test('reports unclosed blocks, stray braces and bad declarations', () {
      final codes = WebCssTools.diagnostics(
        '.a {\n  color: red;\n  --x: blue;\n',
      ).map((finding) => finding.code);
      expect(codes, contains('unclosed-block'));

      final badDeclaration = WebCssTools.diagnostics(
        '.a { color blue; }\n}',
      ).map((finding) => finding.code);
      expect(badDeclaration, contains('declaration-without-colon'));
      expect(badDeclaration, contains('unexpected-brace'));
    });

    test('reports unterminated comments and strings', () {
      final findings = WebCssTools.diagnostics('.a { color: red } /* note');
      expect(
        findings.map((finding) => finding.code),
        contains('unterminated-comment'),
      );
      final string = WebCssTools.diagnostics('.a { content: "x; }');
      expect(
        string.map((finding) => finding.code),
        contains('unterminated-string'),
      );
    });

    test('accepts a valid stylesheet without findings', () {
      expect(
        WebCssTools.diagnostics(
          '.a { color: red; }\n@media (min-width: 600px) { .b { color: blue } }',
        ),
        isEmpty,
      );
    });
  });

  test('format re-indents one declaration per line', () {
    expect(
      WebCssTools.format('.a{color:red;margin:0  auto}'),
      '.a {\n  color: red;\n  margin: 0 auto;\n}',
    );
  });

  test(
    'format preserves scopes, at-rules, comments, custom case and strings',
    () {
      const source =
          '@charset "UTF-8";\n@import "local.css";\n'
          '/* keep me */ @media (width > 1px){.a{--Theme: RED;'
          'content:"a  b\\" c";background:url(data:image/svg+xml;utf8,x)}}';
      final formatted = WebCssTools.format(source);
      expect(formatted, contains('@charset "UTF-8";'));
      expect(formatted, contains('@import "local.css";'));
      expect(
        formatted,
        contains('/* keep me */ @media (width > 1px) {\n  .a {'),
      );
      expect(formatted, contains('--Theme: RED;'));
      expect(formatted, contains('content: "a  b\\" c";'));
      expect(formatted, contains('url(data:image/svg+xml;utf8,x)'));
      expect(WebCssTools.format(formatted), formatted);
      const malformed = '.a { content: "unterminated';
      expect(WebCssTools.format(malformed), malformed);
      const customBlock = '.a { --x: { first: one; }; color: red; }';
      expect(WebCssTools.format(customBlock), customBlock);
    },
  );

  group('WebSourceIndex', () {
    test('comment stripping preserves quoted literals and line positions', () {
      const source = '.a { content: "/* real text */"; } /* discarded\nline */';
      final stripped = stripCssComments(source);
      expect(stripped, contains('"/* real text */"'));
      expect(stripped.length, source.length);
      expect(stripped.split('\n'), hasLength(source.split('\n').length));
      expect(stripCssComments('x /* unclosed\nline').split('\n'), hasLength(2));
    });
    test('maps offsets to 1-based line and column', () {
      final index = WebSourceIndex('ab\ncd\n\nef');
      expect(index.locate(0).label, '1:1');
      expect(index.locate(2).label, '1:3');
      expect(index.locate(3).label, '2:1');
      expect(index.locate(7).label, '4:1');
      // Offsets past the end clamp to the last line instead of throwing.
      expect(index.locate(99).label, '4:3');
    });

    test('treats CRLF as one line break', () {
      final index = WebSourceIndex('a\r\nb');
      expect(index.locate(3).label, '2:1');
    });
  });
}
