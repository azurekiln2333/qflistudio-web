/// Offline CSS inspection used directly by the WebForge tools page.
///
/// Covers the three things an offline Web IDE can honestly compute without a
/// browser engine:
///
/// * colour literals — hex / `rgb()` / `hsl()` / CSS named colours, converted
///   with WCAG contrast ratios (MDN "CSS color values", WCAG 2.1 §1.4.3);
/// * selector specificity — the `(a, b, c)` triple from the selectors spec
///   (ID, class/attribute/pseudo-class, type/pseudo-element);
/// * the box model — `padding` / `margin` / `border-width` shorthand expansion
///   and `content-box` vs `border-box` outer sizes.
///
/// It is a bounded scanner over the literal stylesheet, so results are reported
/// as inspections. It never claims to be a CSS parser for the cascade.
library;

import 'dart:math' as math;

import 'package:qfli_studio_core/tools/offline_tools.dart';

import 'web_source_scan.dart';

/// Every CSS named colour (MDN "CSS color values", 148 names) plus
/// `transparent`. Stored as one compact table instead of 149 map entries.
const String _namedColorTable =
    'aliceblue=f0f8ff,antiquewhite=faebd7,aqua=00ffff,aquamarine=7fffd4,'
    'azure=f0ffff,beige=f5f5dc,bisque=ffe4c4,black=000000,'
    'blanchedalmond=ffebcd,blue=0000ff,blueviolet=8a2be2,brown=a52a2a,'
    'burlywood=deb887,cadetblue=5f9ea0,chartreuse=7fff00,chocolate=d2691e,'
    'coral=ff7f50,cornflowerblue=6495ed,cornsilk=fff8dc,crimson=dc143c,'
    'cyan=00ffff,darkblue=00008b,darkcyan=008b8b,darkgoldenrod=b8860b,'
    'darkgray=a9a9a9,darkgreen=006400,darkgrey=a9a9a9,darkkhaki=bdb76b,'
    'darkmagenta=8b008b,darkolivegreen=556b2f,darkorange=ff8c00,'
    'darkorchid=9932cc,darkred=8b0000,darksalmon=e9967a,darkseagreen=8fbc8f,'
    'darkslateblue=483d8b,darkslategray=2f4f4f,darkslategrey=2f4f4f,'
    'darkturquoise=00ced1,darkviolet=9400d3,deeppink=ff1493,'
    'deepskyblue=00bfff,dimgray=696969,dimgrey=696969,dodgerblue=1e90ff,'
    'firebrick=b22222,floralwhite=fffaf0,forestgreen=228b22,fuchsia=ff00ff,'
    'gainsboro=dcdcdc,ghostwhite=f8f8ff,gold=ffd700,goldenrod=daa520,'
    'gray=808080,green=008000,greenyellow=adff2f,grey=808080,honeydew=f0fff0,'
    'hotpink=ff69b4,indianred=cd5c5c,indigo=4b0082,ivory=fffff0,khaki=f0e68c,'
    'lavender=e6e6fa,lavenderblush=fff0f5,lawngreen=7cfc00,'
    'lemonchiffon=fffacd,lightblue=add8e6,lightcoral=f08080,'
    'lightcyan=e0ffff,lightgoldenrodyellow=fafad2,lightgray=d3d3d3,'
    'lightgreen=90ee90,lightgrey=d3d3d3,lightpink=ffb6c1,lightsalmon=ffa07a,'
    'lightseagreen=20b2aa,lightskyblue=87cefa,lightslategray=778899,'
    'lightslategrey=778899,lightsteelblue=b0c4de,lightyellow=ffffe0,'
    'lime=00ff00,limegreen=32cd32,linen=faf0e6,magenta=ff00ff,maroon=800000,'
    'mediumaquamarine=66cdaa,mediumblue=0000cd,mediumorchid=ba55d3,'
    'mediumpurple=9370db,mediumseagreen=3cb371,mediumslateblue=7b68ee,'
    'mediumspringgreen=00fa9a,mediumturquoise=48d1cc,'
    'mediumvioletred=c71585,midnightblue=191970,mintcream=f5fffa,'
    'mistyrose=ffe4e1,moccasin=ffe4b5,navajowhite=ffdead,navy=000080,'
    'oldlace=fdf5e6,olive=808000,olivedrab=6b8e23,orange=ffa500,'
    'orangered=ff4500,orchid=da70d6,palegoldenrod=eee8aa,palegreen=98fb98,'
    'paleturquoise=afeeee,palevioletred=db7093,papayawhip=ffefd5,'
    'peachpuff=ffdab9,peru=cd853f,pink=ffc0cb,plum=dda0dd,'
    'powderblue=b0e0e6,purple=800080,rebeccapurple=663399,red=ff0000,'
    'rosybrown=bc8f8f,royalblue=4169e1,saddlebrown=8b4513,salmon=fa8072,'
    'sandybrown=f4a460,seagreen=2e8b57,seashell=fff5ee,sienna=a0522d,'
    'silver=c0c0c0,skyblue=87ceeb,slateblue=6a5acd,slategray=708090,'
    'slategrey=708090,snow=fffafa,springgreen=00ff7f,steelblue=4682b4,'
    'tan=d2b48c,teal=008080,thistle=d8bfd8,tomato=ff6347,'
    'turquoise=40e0d0,violet=ee82ee,wheat=f5deb3,white=ffffff,'
    'whitesmoke=f5f5f5,yellow=ffff00,yellowgreen=9acd32';

final Map<String, int> _namedColors = () {
  final table = <String, int>{};
  for (final entry in _namedColorTable.split(',')) {
    final separator = entry.indexOf('=');
    table[entry.substring(0, separator)] = int.parse(
      entry.substring(separator + 1),
      radix: 16,
    );
  }
  return Map<String, int>.unmodifiable(table);
}();

/// Number of CSS named colours supported by [CssColor.parse].
int get cssNamedColorCount => _namedColors.length;

/// A parsed CSS colour with 0-255 channels and a 0-1 alpha.
class CssColor {
  const CssColor(this.red, this.green, this.blue, {this.alpha = 1});

  final int red;
  final int green;
  final int blue;
  final double alpha;

  /// Parses `#RGB`, `#RGBA`, `#RRGGBB`, `#RRGGBBAA`, `rgb()`, `rgba()`,
  /// `hsl()`, `hsla()` (comma or space syntax) and the CSS named colours.
  ///
  /// Returns `null` for anything else, including other CSS functions such as
  /// `color-mix()`, instead of guessing a value.
  static CssColor? parse(String text) {
    final value = text.trim();
    if (value.isEmpty) return null;
    final lower = value.toLowerCase();
    final named = _namedColors[lower];
    if (named != null) {
      return CssColor((named >> 16) & 0xFF, (named >> 8) & 0xFF, named & 0xFF);
    }
    if (lower == 'transparent') return const CssColor(0, 0, 0, alpha: 0);
    if (lower.startsWith('#')) return _parseHex(lower.substring(1));
    if (lower.startsWith('rgb')) return _parseRgb(lower);
    if (lower.startsWith('hsl')) return _parseHsl(lower);
    return null;
  }

  static CssColor? _parseHex(String hex) {
    if (!RegExp('^[0-9a-f]+\$').hasMatch(hex)) return null;
    final expanded = switch (hex.length) {
      3 || 4 => hex.split('').map((digit) => '$digit$digit').join(),
      6 || 8 => hex,
      _ => null,
    };
    if (expanded == null) return null;
    int channel(int index) =>
        int.parse(expanded.substring(index * 2, index * 2 + 2), radix: 16);
    final hasAlpha = expanded.length == 8;
    return CssColor(
      channel(0),
      channel(1),
      channel(2),
      alpha: hasAlpha ? channel(3) / 255 : 1,
    );
  }

  static List<String>? _arguments(String lower, String name) {
    final open = lower.indexOf('(');
    if (open < 0 || !lower.startsWith('$name(')) return null;
    final close = lower.lastIndexOf(')');
    if (close <= open || close != lower.length - 1) return null;
    final inner = lower.substring(open + 1, close).trim();
    // Modern syntax separates the alpha with `/`; commas are the legacy form.
    final parts = inner.split('/');
    if (parts.length > 2) return null;
    final legacy = parts.first.contains(',');
    if (legacy && parts.length == 2) return null;
    if (legacy &&
        parts.first
            .split(',')
            .any((part) => part.trim().split(RegExp(r'\s+')).length != 1)) {
      return null;
    }
    final channels = parts.first
        .split(',')
        .expand(
          (part) => part
              .trim()
              .split(RegExp(r'\s+'))
              .where((part) => part.isNotEmpty),
        )
        .toList();
    if (legacy && parts.first.split(',').any((part) => part.trim().isEmpty)) {
      return null;
    }
    final slashAlpha = parts.length == 2 ? _alpha(parts[1].trim()) : null;
    if (parts.length == 2 && slashAlpha == null) return null;
    // rgba(r, g, b, a) keeps the alpha as a fourth comma-separated argument.
    double? alpha = slashAlpha;
    if (channels.length == 4) {
      if (!legacy) return null;
      alpha = _alpha(channels.removeLast());
      if (alpha == null) return null;
    }
    if (channels.length != 3) return null;
    if (legacy &&
        name.startsWith('rgb') &&
        channels.any((part) => part.endsWith('%')) &&
        !channels.every((part) => part.endsWith('%'))) {
      return null;
    }
    return [...channels, if (alpha != null) 'alpha:$alpha'];
  }

  static double? _alpha(String text) {
    if (text.endsWith('%')) {
      final percent = double.tryParse(text.substring(0, text.length - 1));
      return percent == null || !percent.isFinite
          ? null
          : (percent / 100).clamp(0, 1).toDouble();
    }
    final value = double.tryParse(text);
    return value == null || !value.isFinite
        ? null
        : value.clamp(0, 1).toDouble();
  }

  static CssColor? _parseRgb(String lower) {
    final args = _arguments(lower, lower.startsWith('rgba') ? 'rgba' : 'rgb');
    if (args == null) return null;
    final channels = <int>[];
    for (final arg in args.take(3)) {
      final value = _channel(arg);
      if (value == null) return null;
      channels.add(value);
    }
    final alpha = args.length == 4
        ? double.parse(args.last.substring('alpha:'.length))
        : 1.0;
    return CssColor(channels[0], channels[1], channels[2], alpha: alpha);
  }

  static int? _channel(String text) {
    if (text.endsWith('%')) {
      final percent = double.tryParse(text.substring(0, text.length - 1));
      if (percent == null || !percent.isFinite) return null;
      return (percent * 255 / 100).round().clamp(0, 255).toInt();
    }
    final value = double.tryParse(text);
    if (value == null || !value.isFinite) return null;
    return value.round().clamp(0, 255).toInt();
  }

  static CssColor? _parseHsl(String lower) {
    final args = _arguments(lower, lower.startsWith('hsla') ? 'hsla' : 'hsl');
    if (args == null) return null;
    final hueText = args[0];
    double? hue;
    if (hueText.endsWith('deg')) {
      hue = double.tryParse(hueText.substring(0, hueText.length - 3));
    } else if (hueText.endsWith('grad')) {
      final gradians = double.tryParse(
        hueText.substring(0, hueText.length - 4),
      );
      hue = gradians == null ? null : gradians * 0.9;
    } else if (hueText.endsWith('turn')) {
      final turns = double.tryParse(hueText.substring(0, hueText.length - 4));
      hue = turns == null ? null : turns * 360;
    } else if (hueText.endsWith('rad')) {
      final radians = double.tryParse(hueText.substring(0, hueText.length - 3));
      hue = radians == null ? null : radians * 180 / math.pi;
    } else {
      hue = double.tryParse(hueText);
    }
    final saturation = _percent(args[1]);
    final lightness = _percent(args[2]);
    if (hue == null ||
        !hue.isFinite ||
        saturation == null ||
        lightness == null) {
      return null;
    }
    final alpha = args.length == 4
        ? double.parse(args.last.substring('alpha:'.length))
        : 1.0;
    final normalizedHue = ((hue % 360) + 360) % 360;
    return _fromHsl(normalizedHue, saturation, lightness, alpha);
  }

  static double? _percent(String text) {
    if (!text.endsWith('%')) return null;
    final value = double.tryParse(text.substring(0, text.length - 1));
    return value == null || !value.isFinite
        ? null
        : (value / 100).clamp(0, 1).toDouble();
  }

  /// HSL → sRGB with the standard CSS algorithm (MDN `hsl()`).
  static CssColor _fromHsl(
    double hue,
    double saturation,
    double lightness,
    double alpha,
  ) {
    final chroma = (1 - (2 * lightness - 1).abs()) * saturation;
    final sector = hue / 60;
    final secondary = chroma * (1 - ((sector % 2) - 1).abs());
    final (r, g, b) = switch (sector.floor() % 6) {
      0 => (chroma, secondary, 0.0),
      1 => (secondary, chroma, 0.0),
      2 => (0.0, chroma, secondary),
      3 => (0.0, secondary, chroma),
      4 => (secondary, 0.0, chroma),
      _ => (chroma, 0.0, secondary),
    };
    final match = lightness - chroma / 2;
    int channel(double value) =>
        ((value + match) * 255).round().clamp(0, 255).toInt();
    return CssColor(channel(r), channel(g), channel(b), alpha: alpha);
  }

  bool get isOpaque => alpha >= 0.999;

  OfflineColorInfo get _info => OfflineColorInfo.fromArgb(
    (alpha * 255).round().clamp(0, 255),
    red,
    green,
    blue,
  );

  /// `#RRGGBB`, or `#RRGGBBAA` when the alpha is not opaque.
  String get hex => isOpaque ? _info.hexRgb : '${_info.hexRgb}${_alphaHex()}';

  String _alphaHex() => ((alpha * 255).round().clamp(
    0,
    255,
  )).toRadixString(16).padLeft(2, '0').toUpperCase();

  String get rgb => _info.cssRgb;

  String get hsl => _info.cssHsl;

  /// WCAG 2.1 relative luminance, see `contrastRatio`.
  double get relativeLuminance {
    double linear(int channel) {
      final value = channel / 255;
      return value <= 0.03928
          ? value / 12.92
          : math.pow((value + 0.055) / 1.055, 2.4).toDouble();
    }

    return 0.2126 * linear(red) +
        0.7152 * linear(green) +
        0.0722 * linear(blue);
  }

  /// WCAG 2.1 contrast ratio between two opaque colours, 1.0 - 21.0.
  ///
  /// Translucent colours are composited over the other colour's channel value
  /// is not attempted; callers should pass opaque colours for a valid ratio.
  static double? contrastRatio(CssColor first, CssColor second) {
    if (!first.isOpaque || !second.isOpaque) return null;
    final bright = math.max(first.relativeLuminance, second.relativeLuminance);
    final dark = math.min(first.relativeLuminance, second.relativeLuminance);
    return (bright + 0.05) / (dark + 0.05);
  }

  @override
  String toString() => hex;
}

/// One colour literal found in a stylesheet.
class CssColorUse {
  const CssColorUse({
    required this.raw,
    required this.color,
    required this.location,
  });

  final String raw;
  final CssColor color;
  final WebSourceLocation location;
}

/// One parsed CSS declaration with the position of its property name.
class CssDeclaration {
  const CssDeclaration({
    required this.property,
    required this.value,
    required this.location,
    this.valueOffset = 0,
  });

  final String property;
  final String value;
  final WebSourceLocation location;
  final int valueOffset;
}

/// One selector block and its declarations.
class CssRule {
  const CssRule({
    required this.selector,
    required this.declarations,
    required this.location,
  });

  final String selector;
  final List<CssDeclaration> declarations;
  final WebSourceLocation location;
}

/// The `(a, b, c)` specificity triple of one selector.
class CssSpecificity {
  const CssSpecificity({
    required this.selector,
    required this.ids,
    required this.classes,
    required this.types,
    required this.location,
    this.dependsOnParent = false,
  });

  final String selector;
  final int ids;
  final int classes;
  final int types;
  final WebSourceLocation location;
  final bool dependsOnParent;

  /// Specificity is compared lexicographically, never as decimal digits.
  int compareTo(CssSpecificity other) => _compareCounts(
    (ids, classes, types),
    (other.ids, other.classes, other.types),
  );

  String get label =>
      dependsOnParent ? '依赖嵌套父规则，未计算' : '($ids, $classes, $types)';
}

/// One property declared more than once inside the same rule.
class CssDuplicateProperty {
  const CssDuplicateProperty({
    required this.selector,
    required this.property,
    required this.occurrences,
  });

  final String selector;
  final String property;
  final List<CssDeclaration> occurrences;
}

/// A fully parsed stylesheet: rules plus structural findings.
class CssStylesheet {
  const CssStylesheet({required this.rules, required this.findings});

  final List<CssRule> rules;
  final List<WebFinding> findings;
}

/// Bounded scanner for CSS colour values, selectors and the box model.
abstract final class WebCssTools {
  /// The most declarations/colours reported, so a paste bomb cannot hang the UI.
  static const int maxFindings = 200;
  static const int maxSourceCharacters = 128 * 1024;

  /// Parses a stylesheet into rule blocks and structural findings.
  static CssStylesheet parse(String source) {
    if (source.length > maxSourceCharacters) {
      return const CssStylesheet(
        rules: [],
        findings: [
          WebFinding(
            code: 'source-too-large',
            message: '文本超过 128 K 字符，请缩小后检查',
            location: WebSourceLocation(line: 1, column: 1, offset: 0),
          ),
        ],
      );
    }
    source = stripCssComments(source);
    final index = WebSourceIndex(source);
    final findings = <WebFinding>[];
    final rules = <CssRule>[];
    final stack = <_OpenBlock>[];
    var position = 0;
    var segmentStart = 0;

    void flushDeclaration(_OpenBlock block, int end) {
      final text = source.substring(segmentStart, end);
      if (text.trim().isEmpty) return;
      final colon = _indexOfTopLevelColon(text);
      if (colon < 0) {
        if (!block.header.startsWith('@')) {
          findings.add(
            WebFinding(
              code: 'declaration-without-colon',
              message: '声明缺少冒号：${text.trim()}',
              location: index.locate(
                segmentStart + text.indexOf(RegExp(r'\S')),
              ),
            ),
          );
        }
        return;
      }
      final property = text.substring(0, colon).trim();
      final value = text.substring(colon + 1).trim();
      if (property.isEmpty) return;
      final nameOffset = segmentStart + text.indexOf(RegExp(r'\S'));
      block.declarations.add(
        CssDeclaration(
          property: property.startsWith('--')
              ? property
              : property.toLowerCase(),
          value: value,
          location: index.locate(nameOffset),
          valueOffset:
              segmentStart +
              colon +
              1 +
              text.substring(colon + 1).indexOf(RegExp(r'\S')),
        ),
      );
    }

    var parentheses = 0;
    var brackets = 0;
    while (position < source.length) {
      final unit = source.codeUnitAt(position);
      if (unit == 0x22 || unit == 0x27) {
        final close = _skipString(source, position);
        if (close < 0) {
          findings.add(
            WebFinding(
              code: 'unterminated-string',
              message: '字符串没有闭合',
              location: index.locate(position),
              severity: WebFindingSeverity.error,
            ),
          );
          break;
        }
        position = close + 1;
        continue;
      }
      if (unit == 0x28) parentheses++;
      if (unit == 0x29 && parentheses > 0) parentheses--;
      if (unit == 0x5B) brackets++;
      if (unit == 0x5D && brackets > 0) brackets--;
      if (parentheses > 0 || brackets > 0) {
        position++;
        continue;
      }
      switch (unit) {
        case 0x7B: // {
          final header = source.substring(segmentStart, position).trim();
          final headerOffset =
              segmentStart +
              source.substring(segmentStart, position).indexOf(RegExp(r'\S'));
          stack.add(
            _OpenBlock(
              header: header,
              location: index.locate(
                headerOffset < 0 ? segmentStart : headerOffset,
              ),
            ),
          );
          segmentStart = position + 1;
        case 0x3B: // ;
          if (stack.isNotEmpty) flushDeclaration(stack.last, position);
          segmentStart = position + 1;
        case 0x7D: // }
          if (stack.isEmpty) {
            findings.add(
              WebFinding(
                code: 'unexpected-brace',
                message: '多余的 }',
                location: index.locate(position),
                severity: WebFindingSeverity.error,
              ),
            );
          } else {
            final block = stack.removeLast();
            flushDeclaration(block, position);
            if (block.declarations.isNotEmpty ||
                !block.header.startsWith('@')) {
              rules.add(
                CssRule(
                  selector: block.header,
                  declarations: List.unmodifiable(block.declarations),
                  location: block.location,
                ),
              );
            }
          }
          segmentStart = position + 1;
      }
      position++;
    }
    for (final block in stack) {
      findings.add(
        WebFinding(
          code: 'unclosed-block',
          message: '规则块没有闭合：${block.header.isEmpty ? '{' : block.header}',
          location: block.location,
          severity: WebFindingSeverity.error,
        ),
      );
    }
    return CssStylesheet(
      rules: List.unmodifiable(rules),
      findings: List.unmodifiable(findings.take(maxFindings)),
    );
  }

  /// Structural findings only, including an unterminated comment.
  static List<WebFinding> diagnostics(String source) {
    final findings = <WebFinding>[];
    stripCssComments(
      source,
      unterminated: (location) => findings.add(
        WebFinding(
          code: 'unterminated-comment',
          message: '注释没有闭合',
          location: location,
          severity: WebFindingSeverity.error,
        ),
      ),
    );
    final stripped = stripCssComments(source);
    findings.addAll(parse(stripped).findings);
    return findings;
  }

  /// Every colour literal in [source], in source order.
  static List<CssColorUse> findColors(String source) {
    if (source.length > maxSourceCharacters) return const [];
    final stripped = stripCssComments(source);
    final index = WebSourceIndex(source);
    final uses = <CssColorUse>[];

    void add(int offset, int length, CssColor? color) {
      if (color == null || uses.length >= maxFindings) return;
      if (isInsideQuotedRun(stripped, offset)) return;
      uses.add(
        CssColorUse(
          raw: source.substring(offset, offset + length),
          color: color,
          location: index.locate(offset),
        ),
      );
    }

    // Inspect declaration values only: selectors such as `#fff`, `.red` and
    // custom-property names such as `--red` are not colour literals.
    final values = List<String>.filled(source.length, ' ');
    for (final rule in parse(stripped).rules) {
      for (final declaration in rule.declarations) {
        final start = declaration.valueOffset;
        for (var i = 0; i < declaration.value.length; i++) {
          if (start + i >= 0 && start + i < values.length) {
            values[start + i] = stripped[start + i];
          }
        }
      }
    }
    var searchable = values.join();
    // A URL may contain a colour name or a fragment without being a colour.
    searchable = searchable.replaceAllMapped(
      RegExp(
        r'''url\(\s*(?:"(?:\\.|[^"])*"|'(?:\\.|[^'])*'|[^)]*)\)''',
        caseSensitive: false,
      ),
      (match) => ' ' * match.group(0)!.length,
    );
    final hex = RegExp(r'#([0-9a-fA-F]{3,8})\b');
    for (final match in hex.allMatches(searchable)) {
      final digits = match.group(1)!;
      if (!{3, 4, 6, 8}.contains(digits.length)) continue;
      add(
        match.start,
        match.end - match.start,
        CssColor.parse(match.group(0)!),
      );
    }
    final functions = RegExp(
      r'\b(rgba?|hsla?)\(([^()]*)\)',
      caseSensitive: false,
    );
    for (final match in functions.allMatches(searchable)) {
      add(
        match.start,
        match.end - match.start,
        CssColor.parse(match.group(0)!),
      );
    }
    final words = RegExp('[A-Za-z][A-Za-z0-9]*');
    for (final match in words.allMatches(searchable)) {
      final word = match.group(0)!.toLowerCase();
      if (word != 'transparent' && !_namedColors.containsKey(word)) continue;
      final before = match.start == 0 ? '' : searchable[match.start - 1];
      final after = match.end >= searchable.length ? '' : searchable[match.end];
      if (RegExp('[-#.a-zA-Z0-9_]').hasMatch(before)) continue;
      if (RegExp('[-a-zA-Z0-9_]').hasMatch(after)) continue;
      add(match.start, match.end - match.start, CssColor.parse(word));
    }
    uses.sort((a, b) => a.location.offset.compareTo(b.location.offset));
    return uses;
  }

  /// Selector specificity for every rule, in source order.
  static List<CssSpecificity> specificities(String source) {
    final sheet = parse(stripCssComments(source));
    final result = <CssSpecificity>[];
    for (final rule in sheet.rules) {
      if (rule.selector.startsWith('@')) continue;
      for (final part in _splitTopLevel(rule.selector, ',')) {
        final trimmed = part.trim();
        if (trimmed.isEmpty) continue;
        final counts = _selectorCounts(trimmed);
        result.add(
          CssSpecificity(
            selector: trimmed,
            ids: counts.$1,
            classes: counts.$2,
            types: counts.$3,
            location: rule.location,
            dependsOnParent: trimmed.contains('&'),
          ),
        );
      }
    }
    return result;
  }

  /// Properties repeated in one rule; validity and !important govern the winner.
  static List<CssDuplicateProperty> duplicateDeclarations(String source) {
    final sheet = parse(stripCssComments(source));
    final duplicates = <CssDuplicateProperty>[];
    for (final rule in sheet.rules) {
      final byName = <String, List<CssDeclaration>>{};
      for (final declaration in rule.declarations) {
        byName.putIfAbsent(declaration.property, () => []).add(declaration);
      }
      for (final entry in byName.entries) {
        if (entry.value.length < 2) continue;
        duplicates.add(
          CssDuplicateProperty(
            selector: rule.selector,
            property: entry.key,
            occurrences: List.unmodifiable(entry.value),
          ),
        );
      }
    }
    return duplicates;
  }

  /// Expands the `padding` / `margin` / `border-width` shorthand of one rule.
  ///
  /// Only `px` lengths are summed; every other unit is reported verbatim so the
  /// tool never invents a pixel value for `rem`, `em` or `%`.
  static CssBoxModel? boxModel(
    List<CssDeclaration> declarations, {
    double? contentWidth,
    double? contentHeight,
  }) {
    const sides = ['top', 'right', 'bottom', 'left'];
    final values = <String, (String, bool)>{};
    var relevant = false;
    void put(String key, String value, bool important) {
      if (values[key]?.$2 == true && !important) return;
      values[key] = (value, important);
    }

    void putEdges(String key, String value, bool important) {
      final edges = _expandEdges(value);
      if (edges == null) return;
      for (var i = 0; i < sides.length; i++) {
        put('$key-${sides[i]}', edges.values[i], important);
      }
    }

    const borderStyles = {
      'none',
      'hidden',
      'solid',
      'dashed',
      'dotted',
      'double',
      'groove',
      'ridge',
      'inset',
      'outset',
    };
    for (final declaration in declarations) {
      final property = declaration.property;
      final important = RegExp(
        r'!\s*important\s*$',
        caseSensitive: false,
      ).hasMatch(declaration.value);
      final value = declaration.value
          .replaceFirst(RegExp(r'!\s*important\s*$', caseSensitive: false), '')
          .trim();
      if (property == 'padding' ||
          property == 'margin' ||
          property == 'border-width' ||
          property == 'border-style') {
        relevant = true;
        putEdges(property, value, important);
      } else if (RegExp(
        r'^(padding|margin)-(top|right|bottom|left)$',
      ).hasMatch(property)) {
        relevant = true;
        put(property, value, important);
      } else if (RegExp(
        r'^border-(top|right|bottom|left)-(width|style)$',
      ).hasMatch(property)) {
        relevant = true;
        final parts = property.split('-');
        put('border-${parts[2]}-${parts[1]}', value, important);
      } else if (property == 'border' ||
          RegExp(r'^border-(top|right|bottom|left)$').hasMatch(property)) {
        relevant = true;
        final tokens = value.split(RegExp(r'\s+'));
        final width =
            tokens
                .where(
                  (token) =>
                      const {'thin', 'medium', 'thick'}.contains(token) ||
                      RegExp(r'^\d*\.?\d+(?:px|em|rem|%)?$').hasMatch(token),
                )
                .firstOrNull ??
            'medium';
        final style = tokens.where(borderStyles.contains).firstOrNull ?? 'none';
        for (final side
            in property == 'border' ? sides : [property.substring(7)]) {
          put('border-width-$side', width, important);
          put('border-style-$side', style, important);
        }
      } else if (property == 'box-sizing') {
        put(property, value.toLowerCase(), important);
      }
    }
    if (!relevant) return null;
    CssEdges? edges(String key, {bool border = false}) {
      final hasValue = sides.any((side) => values.containsKey('$key-$side'));
      if (!hasValue && !border) return null;
      final edges = [
        for (final side in sides)
          border &&
                  const {
                    'none',
                    'hidden',
                  }.contains(values['border-style-$side']?.$1 ?? 'none')
              ? '0px'
              : values['$key-$side']?.$1 ?? (border ? 'medium' : '0px'),
      ];
      return CssEdges(
        top: edges[0],
        right: edges[1],
        bottom: edges[2],
        left: edges[3],
      );
    }

    final padding = edges('padding');
    final margin = edges('margin');
    final borderWidth = edges('border-width', border: true);
    return CssBoxModel(
      padding: padding,
      margin: margin,
      borderWidth: borderWidth,
      boxSizing: values['box-sizing']?.$1 ?? 'content-box',
      contentWidth: contentWidth?.isFinite == true && contentWidth! >= 0
          ? contentWidth
          : null,
      contentHeight: contentHeight?.isFinite == true && contentHeight! >= 0
          ? contentHeight
          : null,
      borderStyle: sides
          .map((side) => values['border-style-$side']?.$1 ?? 'none')
          .join(' '),
    );
  }

  /// Re-indents a stylesheet block by block: one declaration per line.
  static String format(String source) {
    if (source.length > maxSourceCharacters ||
        diagnostics(source).isNotEmpty ||
        RegExp(r'--[-\w]+\s*:[^;{}]*\{').hasMatch(source)) {
      return source;
    }
    // Re-indent original tokens. Rebuilding from the inspection model would
    // discard comments, @import, @media/@layer nesting and custom-property case.
    final buffer = StringBuffer();
    var start = 0;
    var depth = 0;
    var parentheses = 0;
    var brackets = 0;
    void writeSegment(int end, String suffix) {
      var text = source.substring(start, end).trim();
      if (text.isEmpty && suffix != '}') return;
      final colon = _indexOfTopLevelColon(text);
      if (depth > 0 &&
          colon > 0 &&
          RegExp(
            r'^[-_a-zA-Z][-_a-zA-Z0-9]*$',
          ).hasMatch(text.substring(0, colon))) {
        final property = text.substring(0, colon);
        final value = text.substring(colon + 1).trim();
        text =
            '$property: ${property.startsWith('--') ? value : _collapseWhitespace(value)}';
      }
      buffer.writeln('${'  ' * depth}$text$suffix');
    }

    for (var position = 0; position < source.length; position++) {
      final char = source[position];
      if (char == '"' || char == "'") {
        final close = _skipString(source, position);
        if (close < 0) return source;
        position = close;
        continue;
      }
      if (source.startsWith('/*', position)) {
        final close = source.indexOf('*/', position + 2);
        if (close < 0) return source;
        position = close + 1;
        continue;
      }
      if (char == '(') parentheses++;
      if (char == ')' && parentheses > 0) parentheses--;
      if (char == '[') brackets++;
      if (char == ']' && brackets > 0) brackets--;
      if (parentheses != 0 || brackets != 0) continue;
      if (char == '{') {
        writeSegment(position, ' {');
        depth++;
        start = position + 1;
      } else if (char == ';') {
        writeSegment(position, ';');
        start = position + 1;
      } else if (char == '}') {
        final trailing = source.substring(start, position).trim();
        if (trailing.isNotEmpty) writeSegment(position, ';');
        depth = math.max(0, depth - 1);
        start = position;
        writeSegment(position, '}');
        start = position + 1;
      }
    }
    writeSegment(source.length, '');
    return buffer.toString().trimRight();
  }

  /// Collapses whitespace runs outside quoted strings so re-formatting is
  /// idempotent without touching `content: "a  b"` literals.
  static String _collapseWhitespace(String value) {
    final buffer = StringBuffer();
    var pendingSpace = false;
    for (var index = 0; index < value.length; index++) {
      final char = value[index];
      if (RegExp(r'\s').hasMatch(char)) {
        pendingSpace = buffer.isNotEmpty;
        continue;
      }
      if (char == '"' || char == "'") {
        if (pendingSpace) buffer.write(' ');
        pendingSpace = false;
        final end = _skipString(value, index);
        if (end < 0) return value;
        buffer.write(value.substring(index, end + 1));
        index = end;
        continue;
      }
      if (pendingSpace) {
        buffer.write(' ');
        pendingSpace = false;
      }
      buffer.write(char);
    }
    return buffer.toString();
  }

  static int _indexOfTopLevelColon(String text) {
    var depth = 0;
    for (var index = 0; index < text.length; index++) {
      final unit = text.codeUnitAt(index);
      if (unit == 0x28) depth++;
      if (unit == 0x29 && depth > 0) depth--;
      if (unit == 0x3A && depth == 0) return index;
    }
    return -1;
  }

  static int _skipString(String source, int start) {
    final quote = source.codeUnitAt(start);
    for (var index = start + 1; index < source.length; index++) {
      final unit = source.codeUnitAt(index);
      if (unit == 0x5C) {
        index++;
        continue;
      }
      if (unit == quote) return index;
      if (unit == 0x0A) return -1;
    }
    return -1;
  }

  /// Splits on [separator] at paren/bracket depth zero.
  static List<String> _splitTopLevel(String text, String separator) {
    final parts = <String>[];
    var depth = 0;
    var start = 0;
    for (var index = 0; index < text.length; index++) {
      final unit = text.codeUnitAt(index);
      if (unit == 0x22 || unit == 0x27) {
        final end = _skipString(text, index);
        if (end < 0) break;
        index = end;
        continue;
      }
      if (unit == 0x28 || unit == 0x5B) depth++;
      if ((unit == 0x29 || unit == 0x5D) && depth > 0) depth--;
      if (depth == 0 && text[index] == separator) {
        parts.add(text.substring(start, index));
        start = index + 1;
      }
    }
    parts.add(text.substring(start));
    return parts;
  }

  static (int, int, int) _selectorCounts(String selector) {
    var ids = 0;
    var classes = 0;
    var types = 0;
    var index = 0;
    while (index < selector.length) {
      final char = selector[index];
      if (char == '#') {
        index = _skipIdentifier(selector, index + 1);
        ids++;
      } else if (char == '.') {
        index = _skipIdentifier(selector, index + 1);
        classes++;
      } else if (char == '[') {
        index = _skipBalanced(selector, index, '[', ']');
        classes++;
      } else if (char == ':') {
        final isElement =
            index + 1 < selector.length && selector[index + 1] == ':';
        final nameStart = isElement ? index + 2 : index + 1;
        final nameEnd = _skipIdentifier(selector, nameStart);
        final name = selector.substring(nameStart, nameEnd).toLowerCase();
        index = nameEnd;
        var argument = '';
        if (index < selector.length && selector[index] == '(') {
          final close = _skipBalanced(selector, index, '(', ')');
          argument = selector.substring(
            index + 1,
            math.max(index + 1, close - 1),
          );
          index = close;
        }
        if (isElement ||
            const {
              'before',
              'after',
              'first-line',
              'first-letter',
            }.contains(name)) {
          types++;
          if (name == 'slotted') {
            final counts = _selectorCounts(argument);
            ids += counts.$1;
            classes += counts.$2;
            types += counts.$3;
          }
        } else if (name == 'where') {
          // :where() contributes zero specificity.
        } else if (const {
          'is',
          'not',
          'has',
          'matches',
          'host',
          'host-context',
        }.contains(name)) {
          if (name == 'host' || name == 'host-context') classes++;
          var bestIds = 0;
          var bestClasses = 0;
          var bestTypes = 0;
          for (final part in _splitTopLevel(argument, ',')) {
            final counts = _selectorCounts(part.trim());
            if (_compareCounts(counts, (bestIds, bestClasses, bestTypes)) > 0) {
              bestIds = counts.$1;
              bestClasses = counts.$2;
              bestTypes = counts.$3;
            }
          }
          ids += bestIds;
          classes += bestClasses;
          types += bestTypes;
        } else if (name == 'nth-child' || name == 'nth-last-child') {
          classes++;
          final of = RegExp(
            r'\s+of\s+',
            caseSensitive: false,
          ).firstMatch(argument);
          if (of != null) {
            var best = (0, 0, 0);
            for (final part in _splitTopLevel(
              argument.substring(of.end),
              ',',
            )) {
              final counts = _selectorCounts(part.trim());
              if (_compareCounts(counts, best) > 0) best = counts;
            }
            ids += best.$1;
            classes += best.$2;
            types += best.$3;
          }
        } else {
          classes++;
        }
      } else if (char == '*') {
        index++;
      } else if (_isIdentifierStart(char)) {
        final end = _skipIdentifier(selector, index);
        // `ns|element` keeps only the element part.
        if (end < selector.length &&
            selector[end] == '|' &&
            (end + 1 >= selector.length || selector[end + 1] != '|')) {
          index = end + 1;
        } else {
          types++;
          index = end;
        }
      } else {
        index++;
      }
    }
    return (ids, classes, types);
  }

  static bool _isIdentifierStart(String char) {
    return RegExp('[A-Za-z_]').hasMatch(char);
  }

  static int _skipIdentifier(String selector, int start) {
    var index = start;
    while (index < selector.length &&
        RegExp(r'[-_a-zA-Z0-9\\]').hasMatch(selector[index])) {
      if (selector[index] == '\\') index++;
      index++;
    }
    return index;
  }

  static int _skipBalanced(String text, int start, String open, String close) {
    var depth = 0;
    for (var index = start; index < text.length; index++) {
      if (text[index] == '"' || text[index] == "'") {
        final end = _skipString(text, index);
        if (end < 0) return text.length;
        index = end;
        continue;
      }
      if (text[index] == open) depth++;
      if (text[index] == close) {
        depth--;
        if (depth == 0) return index + 1;
      }
    }
    return text.length;
  }

  /// Expands a 1-4 value shorthand into four edges.
  static CssEdges? _expandEdges(String? value) {
    if (value == null) return null;
    final tokens = _splitTopLevel(
      _collapseWhitespace(value.trim()),
      ' ',
    ).where((part) => part.isNotEmpty).toList();
    if (tokens.isEmpty || tokens.length > 4) return null;
    final top = tokens[0];
    final right = tokens.length >= 2 ? tokens[1] : top;
    final bottom = tokens.length >= 3 ? tokens[2] : top;
    final left = tokens.length >= 4 ? tokens[3] : right;
    return CssEdges(top: top, right: right, bottom: bottom, left: left);
  }
}

int _compareCounts((int, int, int) first, (int, int, int) second) {
  final ids = first.$1.compareTo(second.$1);
  if (ids != 0) return ids;
  final classes = first.$2.compareTo(second.$2);
  return classes != 0 ? classes : first.$3.compareTo(second.$3);
}

class _OpenBlock {
  _OpenBlock({required this.header, required this.location});

  final String header;
  final WebSourceLocation location;
  final List<CssDeclaration> declarations = [];
}

/// One side of a shorthand, kept as text so non-`px` units stay honest.
class CssEdges {
  const CssEdges({
    required this.top,
    required this.right,
    required this.bottom,
    required this.left,
  });

  final String top;
  final String right;
  final String bottom;
  final String left;

  List<String> get values => [top, right, bottom, left];

  String get label => values.join(' ');

  static double? _px(String value) {
    if (double.tryParse(value) == 0) return 0;
    value = value.toLowerCase();
    if (!value.endsWith('px')) return null;
    return double.tryParse(value.substring(0, value.length - 2).trim());
  }

  /// Sum of both horizontal edges, or `null` when a unit is not `px`.
  double? get horizontalPx {
    final leftPx = _px(left);
    final rightPx = _px(right);
    if (leftPx == null || rightPx == null) return null;
    return leftPx + rightPx;
  }

  /// Sum of both vertical edges, or `null` when a unit is not `px`.
  double? get verticalPx {
    final topPx = _px(top);
    final bottomPx = _px(bottom);
    if (topPx == null || bottomPx == null) return null;
    return topPx + bottomPx;
  }

  bool get allPx => horizontalPx != null && verticalPx != null;
}

/// The expanded box model of one rule.
class CssBoxModel {
  const CssBoxModel({
    this.padding,
    this.margin,
    this.borderWidth,
    required this.boxSizing,
    this.contentWidth,
    this.contentHeight,
    this.borderStyle,
  });

  final CssEdges? padding;
  final CssEdges? margin;
  final CssEdges? borderWidth;
  final String boxSizing;
  final double? contentWidth;
  final double? contentHeight;
  final String? borderStyle;

  bool get isBorderBox => boxSizing == 'border-box';

  /// Outer width in px, or `null` when any edge uses a non-px unit.
  ///
  /// `content-box`: content + padding + border (+ margin when included).
  /// `border-box`: the inner size already contains padding and border.
  double? outerWidth({bool includeMargin = false}) {
    final width = contentWidth;
    if (width == null) return null;
    final paddingX = padding?.horizontalPx ?? 0;
    final borderX = borderWidth?.horizontalPx ?? 0;
    final marginX = includeMargin ? (margin?.horizontalPx ?? 0) : 0;
    if ((padding != null && padding!.horizontalPx == null) ||
        (borderWidth != null && borderWidth!.horizontalPx == null) ||
        (includeMargin && margin != null && margin!.horizontalPx == null)) {
      return null;
    }
    return isBorderBox
        ? math.max(width, paddingX + borderX) + marginX
        : width + paddingX + borderX + marginX;
  }

  /// Outer height in px, or `null` when any edge uses a non-px unit.
  double? outerHeight({bool includeMargin = false}) {
    final height = contentHeight;
    if (height == null) return null;
    final paddingY = padding?.verticalPx ?? 0;
    final borderY = borderWidth?.verticalPx ?? 0;
    final marginY = includeMargin ? (margin?.verticalPx ?? 0) : 0;
    if ((padding != null && padding!.verticalPx == null) ||
        (borderWidth != null && borderWidth!.verticalPx == null) ||
        (includeMargin && margin != null && margin!.verticalPx == null)) {
      return null;
    }
    return isBorderBox
        ? math.max(height, paddingY + borderY) + marginY
        : height + paddingY + borderY + marginY;
  }

  /// Human-readable rows for the result card.
  List<(String, String)> toRows() {
    final rows = <(String, String)>[
      ('box-sizing', boxSizing),
      if (padding != null) ('padding', padding!.label),
      if (margin != null) ('margin', margin!.label),
      if (borderWidth != null) ('border-width', borderWidth!.label),
      if (borderStyle != null) ('border-style', borderStyle!),
    ];
    if (contentWidth != null) {
      final outer = outerWidth(includeMargin: true);
      rows.add((
        '外框宽度',
        outer == null
            ? '无法换算（含非 px 单位，内容 ${_number(contentWidth!)} px）'
            : isBorderBox
            ? '${_number(outer)} px（width ${_number(contentWidth!)} 已含内边距与边框，再加外边距）'
            : '${_number(outer)} px（内容 ${_number(contentWidth!)} + 内边距 + 边框 + 外边距）',
      ));
    }
    if (contentHeight != null) {
      final outer = outerHeight(includeMargin: true);
      rows.add((
        '外框高度',
        outer == null
            ? '无法换算（含非 px 单位，内容 ${_number(contentHeight!)} px）'
            : isBorderBox
            ? '${_number(outer)} px（height ${_number(contentHeight!)} 已含内边距与边框，再加外边距）'
            : '${_number(outer)} px（内容 ${_number(contentHeight!)} + 内边距 + 边框 + 外边距）',
      ));
    }
    return rows;
  }

  static String _number(double value) => value == value.roundToDouble()
      ? value.round().toString()
      : value.toStringAsFixed(2);
}
