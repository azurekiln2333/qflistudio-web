/// Shared source-position and comment helpers for the offline Web inspectors.
///
/// The tools page inspects HTML/CSS that never leaves the device, so every
/// finding must point back at a real `line:column` in the user's own text.
/// Nothing here parses a full grammar: these are bounded scanners over the
/// literal source, and the results are reported as inspections, never as a
/// compiler verdict.
library;

/// A resolved `line`/`column`/`offset` triple inside one source string.
///
/// [line] and [column] are 1-based, [offset] is a 0-based UTF-16 index, matching
/// what an editor selection reports.
class WebSourceLocation {
  const WebSourceLocation({
    required this.line,
    required this.column,
    required this.offset,
  });

  final int line;
  final int column;
  final int offset;

  /// `12:7` shape used in the tool result lists.
  String get label => '$line:$column';

  @override
  String toString() => label;
}

/// Maps raw string offsets to `line:column` without rescanning the source.
class WebSourceIndex {
  WebSourceIndex(String source)
    : _lineStarts = _computeLineStarts(source),
      _length = source.length;

  final List<int> _lineStarts;
  final int _length;

  static List<int> _computeLineStarts(String source) {
    final starts = <int>[0];
    for (var index = 0; index < source.length; index++) {
      final unit = source.codeUnitAt(index);
      if (unit == 0x0A) {
        starts.add(index + 1);
      } else if (unit == 0x0D) {
        // Treat CRLF as one break; a lone CR is also a break.
        if (index + 1 < source.length && source.codeUnitAt(index + 1) == 0x0A) {
          continue;
        }
        starts.add(index + 1);
      }
    }
    return starts;
  }

  WebSourceLocation locate(int offset) {
    final clamped = offset.clamp(0, _length).toInt();
    var low = 0;
    var high = _lineStarts.length - 1;
    while (low < high) {
      final middle = (low + high + 1) >> 1;
      if (_lineStarts[middle] <= clamped) {
        low = middle;
      } else {
        high = middle - 1;
      }
    }
    return WebSourceLocation(
      line: low + 1,
      column: clamped - _lineStarts[low] + 1,
      offset: clamped,
    );
  }
}

/// Severity used by both the markup and CSS inspectors.
enum WebFindingSeverity { error, warning, hint }

/// One reported problem or inspection note with its source position.
class WebFinding {
  const WebFinding({
    required this.code,
    required this.message,
    required this.location,
    this.severity = WebFindingSeverity.warning,
  });

  /// Stable machine code (`unclosed-tag`, `missing-alt`, ...) used by tests.
  final String code;
  final String message;
  final WebSourceLocation location;
  final WebFindingSeverity severity;

  String get severityLabel => switch (severity) {
    WebFindingSeverity.error => '错误',
    WebFindingSeverity.warning => '警告',
    WebFindingSeverity.hint => '提示',
  };

  @override
  String toString() => '${location.label} $code $message';
}

/// Replaces every CSS comment with spaces, keeping offsets and line breaks.
///
/// Spaces are substituted instead of deleting the comment so that every later
/// offset still maps to the original `line:column`. An unterminated comment is
/// reported through [unterminated] with the position of its `/*`.
String stripCssComments(
  String source, {
  void Function(WebSourceLocation)? unterminated,
}) {
  final buffer = StringBuffer();
  var index = 0;
  var quote = '';
  while (index < source.length) {
    if (quote.isNotEmpty) {
      final char = source[index];
      buffer.write(char);
      index++;
      if (char == '\\' && index < source.length) {
        buffer.write(source[index++]);
      } else if (char == quote) {
        quote = '';
      }
      continue;
    }
    if (source[index] == '"' || source[index] == "'") {
      quote = source[index];
      buffer.write(source[index++]);
      continue;
    }
    if (source.startsWith('/*', index)) {
      final end = source.indexOf('*/', index + 2);
      if (end < 0) {
        unterminated?.call(WebSourceIndex(source).locate(index));
        buffer.write(
          source.substring(index).replaceAll(RegExp('[^\n\r]'), ' '),
        );
        break;
      }
      final chunk = source.substring(index, end + 2);
      buffer.write(chunk.replaceAll(RegExp('[^\n\r]'), ' '));
      index = end + 2;
      continue;
    }
    buffer.write(source[index]);
    index++;
  }
  return buffer.toString();
}

/// Whether [offset] sits inside a single- or double-quoted run of [source].
///
/// Used by the colour scanner so `content: "#fff"` is not reported as a colour.
bool isInsideQuotedRun(String source, int offset, {int from = 0}) {
  var quote = 0;
  for (var index = from; index < offset && index < source.length; index++) {
    final unit = source.codeUnitAt(index);
    if (unit == 0x5C) {
      // Skip the escaped character so `\"` does not close a string.
      index++;
      continue;
    }
    if (quote == 0 && (unit == 0x22 || unit == 0x27)) {
      quote = unit;
    } else if (quote == unit) {
      quote = 0;
    } else if (unit == 0x0A || unit == 0x0D) {
      quote = 0;
    }
  }
  return quote != 0;
}

/// Normalises a path-ish reference to forward slashes for display.
String toPosixDisplay(String path) => path.replaceAll('\\', '/');
