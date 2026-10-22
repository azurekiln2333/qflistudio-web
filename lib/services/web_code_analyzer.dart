import 'dart:convert';
import 'dart:isolate';

import 'package:csslib/parser.dart' as css;
import 'package:html/parser.dart' as html_parser;
import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/services/code_analysis.dart';

import 'web_javascript_syntax.dart';
import 'web_javascript_syntax_stub.dart'
    if (dart.library.io) 'web_javascript_syntax_native.dart';
import 'web_source_scan.dart';

/// Offline parsing of the exact active editor buffer. No project source is
/// opened, overwritten, evaluated, imported, or sent over the network.
class WebCodeAnalyzer implements CodeAnalyzer {
  const WebCodeAnalyzer({this.nativeLibraryPath});

  /// Optional installed native library location for desktop packaging/tools.
  /// Mobile packages resolve their bundled bridge by its platform library name.
  final String? nativeLibraryPath;

  @override
  Future<CodeAnalysisResult> analyze(CodeAnalysisRequest request) async {
    bool ownedPath(String value) =>
        p.isAbsolute(value) &&
        p.normalize(value) == value &&
        p.isWithin(request.projectPath, value);
    if (!p.isAbsolute(request.projectPath) ||
        p.normalize(request.projectPath) != request.projectPath ||
        !ownedPath(request.activeFilePath)) {
      return const CodeAnalysisResult(unavailableReason: '语法分析路径必须属于当前项目');
    }
    if (request.documents.length > 64) {
      return const CodeAnalysisResult(unavailableReason: '打开的源码快照超过语法分析限制');
    }
    CodeDocumentSnapshot? active;
    var totalLength = 0;
    final seen = <String>{};
    for (final document in request.documents) {
      if (!ownedPath(document.path) ||
          !seen.add(p.canonicalize(document.path))) {
        return const CodeAnalysisResult(unavailableReason: '源码快照包含重复或项目外路径');
      }
      totalLength += document.text.length;
      if (p.equals(document.path, request.activeFilePath)) active = document;
    }
    if (active == null || active.revision != request.revision) {
      return const CodeAnalysisResult(unavailableReason: '当前编辑内容的版本快照不可用');
    }
    if (totalLength > 2 * 1024 * 1024 ||
        active.text.length > 512 * 1024 ||
        utf8.encode(active.text).length > 512 * 1024) {
      return const CodeAnalysisResult(unavailableReason: '源码超过离线语法分析大小限制');
    }
    final language = switch (request.language.toLowerCase()) {
      'html' || 'htm' => 'html',
      'css' => 'css',
      'js' || 'javascript' || 'mjs' || 'cjs' => 'javascript',
      _ => '',
    };
    if (language.isEmpty) {
      return const CodeAnalysisResult(unavailableReason: '当前语言未提供 Web 离线语法后端');
    }
    final text = active.text;
    final path = active.path;
    final libraryPath = nativeLibraryPath;
    try {
      return await Isolate.run(() => _parse(text, path, language, libraryPath));
    } catch (error) {
      return CodeAnalysisResult(
        unavailableReason: '离线语法解析器未能完成分析 (${error.runtimeType})',
      );
    }
  }
}

CodeAnalysisResult _parse(
  String text,
  String path,
  String language,
  String? libraryPath,
) {
  final output = _AnalysisOutput(text, path, libraryPath);
  switch (language) {
    case 'html':
      output.html();
    case 'css':
      output.cssText(text, 0);
    case 'javascript':
      final extension = p.extension(path).toLowerCase();
      output.javaScript(
        text,
        0,
        module: extension == '.mjs',
        allowModule: extension == '.js',
      );
  }
  output.diagnostics.sort((a, b) => a.startOffset.compareTo(b.startOffset));
  return CodeAnalysisResult(
    diagnostics: List.unmodifiable(output.diagnostics),
    unavailableReason: output.unavailable.isEmpty
        ? null
        : output.unavailable.join('；'),
  );
}

class _AnalysisOutput {
  _AnalysisOutput(this.text, this.path, this.libraryPath);

  final String text;
  final String path;
  final String? libraryPath;
  final diagnostics = <CodeDiagnostic>[];
  final unavailable = <String>{};

  void add(
    int start,
    int end,
    String message,
    String backend, {
    String code = '',
    CodeDiagnosticSeverity severity = CodeDiagnosticSeverity.error,
  }) {
    if (diagnostics.length >= 100) return;
    if (start < 0 || end < start || end > text.length) {
      unavailable.add('$backend 返回了无效的源码位置');
      return;
    }
    diagnostics.add(
      CodeDiagnostic(
        filePath: path,
        startOffset: start,
        endOffset: end,
        message: message,
        source: backend,
        code: code,
        severity: severity,
      ),
    );
  }

  void cssText(String source, int base) {
    final messages = <css.Message>[];
    css.parse(
      source,
      errors: messages,
      options: const css.PreprocessorOptions(
        useColors: false,
        lessSupport: false,
      ),
    );
    if (messages.isNotEmpty) {
      final unsupported = _unsupportedCssSyntax(source);
      if (unsupported != null) {
        unavailable.add('csslib 尚不支持$unsupported，此样式块未完成语法分析');
        return;
      }
    }
    for (final message in messages) {
      final span = message.span;
      if (span == null) {
        unavailable.add('csslib 返回了没有源码位置的解析消息');
        continue;
      }
      add(
        base + span.start.offset,
        base + span.end.offset,
        message.message,
        'csslib',
        severity: switch (message.level) {
          css.MessageLevel.severe => CodeDiagnosticSeverity.error,
          css.MessageLevel.warning => CodeDiagnosticSeverity.warning,
          css.MessageLevel.info => CodeDiagnosticSeverity.information,
        },
      );
    }
  }

  void javaScript(
    String source,
    int base, {
    required bool module,
    bool allowModule = false,
  }) {
    WebJavaScriptSyntaxResult result = checkJavaScriptSyntax(
      source,
      module: module,
      nativeLibraryPath: libraryPath,
    );
    if (allowModule && result.message != null) {
      final moduleResult = checkJavaScriptSyntax(
        source,
        module: true,
        nativeLibraryPath: libraryPath,
      );
      // Plain .js may be a classic script or an ES module. Prefer a successful
      // module parse, an explicit resource failure, or the parser that reached
      // farther into the source (e.g. a malformed import after its keyword).
      if (moduleResult.message == null ||
          moduleResult.startOffset! > result.startOffset!) {
        result = moduleResult;
      }
    }
    if (result.unavailableReason case final reason?) unavailable.add(reason);
    if (result.message case final message?) {
      add(
        base + result.startOffset!,
        base + result.endOffset!,
        message,
        'QuickJS 2026-06-04',
        code: 'SyntaxError',
      );
    }
  }

  void html() {
    final parser = html_parser.HtmlParser(
      text,
      generateSpans: true,
      parseMeta: false,
    );
    final document = parser.parse();
    // html normalizes CRLF to LF internally. Its spans refer to that normalized
    // stream, so map every boundary back to the original unsaved UTF-16 buffer.
    final originalOffsets = <int>[0];
    for (var index = 0; index < text.length; index++) {
      if (text.codeUnitAt(index) == 13 &&
          index + 1 < text.length &&
          text.codeUnitAt(index + 1) == 10) {
        index++;
      }
      originalOffsets.add(index + 1);
    }
    int original(int normalized) => originalOffsets[normalized];
    for (final error in parser.errors) {
      final span = error.span;
      if (span == null) {
        unavailable.add('HTML5 解析器返回了没有源码位置的错误');
        continue;
      }
      add(
        original(span.start.offset),
        original(span.end.offset),
        error.message,
        'html5lib',
        code: error.errorCode,
      );
    }
    for (final element in document.querySelectorAll('script, style')) {
      final tag = element.sourceSpan;
      if (tag == null) continue;
      final start = original(tag.end.offset);
      // html5lib does not populate endSourceSpan for raw-text script/style
      // elements. Their text nodes carry the exact source span instead. Empty
      // elements have no text nodes, so their source ends at the opening tag.
      final lastContentSpan = element.nodes.isEmpty
          ? null
          : element.nodes.last.sourceSpan;
      final end = lastContentSpan == null
          ? start
          : original(lastContentSpan.end.offset);
      if (end < start) continue;
      final source = text.substring(start, end);
      final type = (element.attributes['type'] ?? '').trim().toLowerCase();
      if (element.localName == 'style') {
        if (type.isEmpty || type == 'text/css') cssText(source, start);
      } else if (!element.attributes.containsKey('src')) {
        if (type == 'module') {
          javaScript(source, start, module: true);
        } else if (type.isEmpty ||
            const {
              'text/javascript',
              'application/javascript',
              'text/ecmascript',
              'application/ecmascript',
            }.contains(type)) {
          javaScript(source, start, module: false);
        }
      }
    }
  }
}

/// A capability gate for syntax that real csslib probes cannot parse. This is
/// deliberately not a modern CSS validator: only the real parser may report a
/// source error. If it fails on a known unsupported construct, suppress that
/// stylesheet's parser messages and report incomplete analysis instead.
String? _unsupportedCssSyntax(String source) {
  final stripped = stripCssComments(source);
  bool outsideString(int offset) => !isInsideQuotedRun(stripped, offset);
  for (final (pattern, description) in [
    (r'@container\b', ' @container 容器查询'),
    (r'@scope\b', ' @scope 作用域'),
    (r'@layer\b[^{}]*;', ' @layer 层顺序声明'),
    (r':(?:has|is|where)\s*\(', '现代函数选择器'),
  ]) {
    if (RegExp(
      pattern,
      caseSensitive: false,
    ).allMatches(stripped).any((match) => outsideString(match.start))) {
      return description;
    }
  }
  for (final match in RegExp(
    r':(?:not|nth-child|nth-last-child)\s*\(([^)]*)\)',
    caseSensitive: false,
  ).allMatches(stripped)) {
    if (!outsideString(match.start)) continue;
    final arguments = match.group(1)!;
    final argumentStart = match.end - arguments.length - 1;
    if (RegExp(r',|\bof\b', caseSensitive: false)
        .allMatches(arguments)
        .any((token) => outsideString(argumentStart + token.start))) {
      return '选择器列表或 nth-child of 语法';
    }
  }
  for (final match in RegExp(
    r'@media\b([^{}]*)\{',
    caseSensitive: false,
  ).allMatches(stripped)) {
    if (!outsideString(match.start)) continue;
    final prelude = match.group(1)!;
    final preludeStart = match.end - prelude.length - 1;
    if (RegExp('[<>=]')
        .allMatches(prelude)
        .any((token) => outsideString(preludeStart + token.start))) {
      return '范围形式的 @media 查询';
    }
  }
  return null;
}
