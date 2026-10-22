import 'dart:convert';
import 'dart:io';

import 'package:qfli_web/services/web_css_tools.dart';
import 'package:qfli_web/services/web_markup_inspector.dart';

void main(List<String> arguments) {
  const css =
      '@import "data:text/css,.probe%7Bheight%3A45px%7D";'
      '/* retain scope */ @media (min-width:1px){.probe{--Theme:red;'
      'color:var(--Theme);width:123px;padding:5px;border:2px solid blue;'
      'box-sizing:border-box}.probe::after{content:"a  b"}}'
      '@supports(display:grid){.probe{display:grid}}'
      '@layer defaults{.probe{margin:7px}}';
  const html =
      '<!doctype html><html><head><title>fixture</title></head>'
      '<body><div class="probe"><span>A</span><span>B</span> <em>C</em></div>'
      '<script>window.preserved = `\n  two  spaces\n</scripture>`;</script>'
      '<pre>  first\n    second\n</pre><textarea>  keep\n next</textarea>'
      '</body></html>';
  File(arguments.single).writeAsStringSync(
    jsonEncode({
      'css': css,
      'formattedCss': WebCssTools.format(css),
      'html': html,
      'formattedHtml': WebMarkupInspector.formatHtml(html),
      'rawTextFindings': WebMarkupInspector.structureFindings(
        html,
      ).map((finding) => finding.code).toList(),
      'fragments': [
        for (final source in [
          '<span>A</span><span>B</span>',
          '<span>A</span> <span>B</span>',
          'first <b>bold</b> tail',
        ])
          {
            'source': source,
            'formatted': WebMarkupInspector.formatHtml(source),
          },
      ],
    }),
  );
}
