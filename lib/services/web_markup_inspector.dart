/// Offline HTML/CSS source inspection for the WebForge tools page.
///
/// The scanner reads the literal project files and answers three questions an
/// offline Web IDE can prove without a browser:
///
/// * which resources a document references (JetBrains/WebStorm "unresolved
///   file reference", VS Code HTML link validation) and whether each one is a
///   local file, a site-root path, an inline `data:` value, or an external URL
///   that the offline product forbids;
/// * whether the tag structure is balanced (VS Code HTML "mismatched tag");
/// * which accessibility basics are missing (`lang`, `alt`, labels, `<title>`,
///   viewport meta) — MDN HTML element references.
///
/// It is an inspection, not a validator or a compiler: unknown elements and
/// grammar-level rules are deliberately not reported.
library;

import 'dart:io';
import 'dart:isolate';

import 'package:html/parser.dart' as html;
import 'package:path/path.dart' as p;

import 'web_source_scan.dart';

/// How one referenced URL resolves inside the project.
enum WebResourceKind {
  /// A file that exists under the project root.
  localFile,

  /// A `/absolute` path that resolves against the project root.
  siteRoot,

  /// A local reference whose file is missing.
  missing,

  /// `data:` / `javascript:` / `mailto:` style inline value.
  inline,

  /// `http(s)://`, `//host/...` or another network scheme.
  external,

  /// A path that leaves the project root.
  escaping,

  /// A reference the tool cannot resolve (bad URL, `file:` scheme, ...).
  invalid,
}

/// One `href` / `src` / `url()` reference found in a document.
class WebResourceReference {
  const WebResourceReference({
    required this.element,
    required this.attribute,
    required this.rawValue,
    required this.kind,
    required this.location,
    this.resolvedPath,
    this.exists = false,
    this.origin,
  });

  /// Tag name, or `css` for a `url()` inside CSS.
  final String element;

  /// Attribute name, or `url()` / `@import`.
  final String attribute;
  final String rawValue;
  final WebResourceKind kind;
  final WebSourceLocation location;

  /// Project-relative posix path when the reference stays inside the project.
  final String? resolvedPath;
  final bool exists;

  /// The stylesheet that contained this reference, when it came from CSS.
  final String? origin;

  bool get isNetwork => kind == WebResourceKind.external;
  bool get isMissing => kind == WebResourceKind.missing;

  String get kindLabel => switch (kind) {
    WebResourceKind.localFile => '本地文件',
    WebResourceKind.siteRoot => '站点根路径',
    WebResourceKind.missing => '缺失文件',
    WebResourceKind.inline => '内联值',
    WebResourceKind.external => '外部网络',
    WebResourceKind.escaping => '越出项目',
    WebResourceKind.invalid => '无法解析',
  };
}

/// The complete inspection of one document.
class WebDocumentInspection {
  const WebDocumentInspection({
    required this.documentPath,
    required this.rootPath,
    required this.references,
    required this.findings,
    required this.cssFiles,
  });

  final String documentPath;
  final String rootPath;
  final List<WebResourceReference> references;
  final List<WebFinding> findings;

  /// Project-relative stylesheet paths that were scanned for `url()` values.
  final List<String> cssFiles;

  int countWhere(bool Function(WebResourceReference) test) =>
      references.where(test).length;

  int get localCount => countWhere(
    (reference) =>
        reference.kind == WebResourceKind.localFile ||
        reference.kind == WebResourceKind.siteRoot,
  );
  int get missingCount => countWhere((reference) => reference.isMissing);
  int get externalCount => countWhere((reference) => reference.isNetwork);
  int get inlineCount =>
      countWhere((reference) => reference.kind == WebResourceKind.inline);

  /// True when every reference stays on the device.
  bool get isOfflineClean =>
      missingCount == 0 &&
      externalCount == 0 &&
      !findings.any(
        (finding) =>
            finding.severity == WebFindingSeverity.error ||
            const {
              'document-too-large',
              'reference-limit',
              'base-reference',
              'stylesheet-limit',
              'unreadable-stylesheet',
            }.contains(finding.code),
      ) &&
      countWhere(
            (reference) =>
                reference.kind == WebResourceKind.invalid ||
                reference.kind == WebResourceKind.escaping,
          ) ==
          0;
}

class WebDocumentScan {
  const WebDocumentScan(this.documents, {required this.truncated});

  final List<String> documents;
  final bool truncated;
}

/// One HTML tag occurrence in a document.
class HtmlTag {
  const HtmlTag({
    required this.name,
    required this.isClosing,
    required this.selfClosing,
    required this.attributes,
    required this.start,
    required this.end,
  });

  final String name;
  final bool isClosing;
  final bool selfClosing;

  /// Attribute name (lower-case) to raw value; valueless attributes are `''`.
  final Map<String, String> attributes;
  final int start;
  final int end;

  String? attribute(String name) => attributes[name];

  bool get isVoid => WebMarkupInspector.voidElements.contains(name);

  @override
  String toString() => '<${isClosing ? '/' : ''}$name>';
}

/// HTML elements that never take a closing tag (MDN "void element").
const Set<String> _voidElements = {
  'area',
  'base',
  'br',
  'col',
  'embed',
  'hr',
  'img',
  'input',
  'link',
  'meta',
  'param',
  'source',
  'track',
  'wbr',
};

/// Elements whose end tag may be omitted (HTML spec, optional tags).
const Set<String> _optionalEndTags = {
  'html',
  'head',
  'body',
  'p',
  'li',
  'dt',
  'dd',
  'tr',
  'td',
  'th',
  'thead',
  'tbody',
  'tfoot',
  'option',
  'optgroup',
  'colgroup',
  'rt',
  'rp',
};

/// Attributes that carry a resource URL, per element.
const Map<String, List<String>> _resourceAttributes = {
  'a': ['href'],
  'area': ['href'],
  'audio': ['src'],
  'base': ['href'],
  'embed': ['src'],
  'iframe': ['src'],
  'img': ['src', 'srcset'],
  'input': ['src'],
  'link': ['href'],
  'object': ['data'],
  'script': ['src'],
  'source': ['src', 'srcset'],
  'track': ['src'],
  'use': ['href', 'xlink:href'],
  'video': ['src', 'poster'],
};

/// Bounded HTML scanner shared by every tool on the tools page.
abstract final class WebMarkupInspector {
  static const Set<String> voidElements = _voidElements;

  /// Files larger than this are not scanned, so a pasted asset cannot stall UI.
  static const int maxDocumentBytes = 1024 * 1024;

  /// Upper bound on reported references.
  static const int maxReferences = 500;

  /// Asynchronous, bounded directory discovery. Excluded directories are never
  /// entered, and symbolic links are never followed.
  static Future<WebDocumentScan> scanDocuments(String rootPath) async {
    const skipped = {'.git', '.qfli', '.dart_tool', 'node_modules', 'build'};
    final pending = <Directory>[Directory(rootPath)];
    final found = <String>[];
    var visited = 0;
    var truncated = false;
    while (pending.isNotEmpty && !truncated) {
      final directory = pending.removeLast();
      try {
        await for (final entity in directory.list(followLinks: false)) {
          if (++visited > 10000 || found.length >= 200) {
            truncated = true;
            break;
          }
          if (entity is Directory) {
            if (!skipped.contains(p.basename(entity.path))) pending.add(entity);
          } else if (entity is File &&
              const {
                '.html',
                '.htm',
              }.contains(p.extension(entity.path).toLowerCase())) {
            found.add(entity.path);
          }
        }
      } on FileSystemException {
        // An unreadable child cannot prevent inspecting the remaining project.
      }
    }
    found.sort();
    return WebDocumentScan(List.unmodifiable(found), truncated: truncated);
  }

  /// Disk reads and source analysis happen away from the UI isolate.
  static Future<WebDocumentInspection> inspectFileAsync(
    String documentPath, {
    required String rootPath,
  }) => Isolate.run(() => inspectFile(documentPath, rootPath: rootPath));

  /// Splits [source] into tags and text runs, tolerating malformed input.
  static List<HtmlTag> tags(String source) => [
    for (final token in _tokenize(source))
      if (token is _TagToken) token.tag,
  ];

  /// Balanced-tag findings, ignoring the HTML optional end tags.
  static List<WebFinding> structureFindings(String source) {
    final index = WebSourceIndex(source);
    final findings = <WebFinding>[];
    final stack = <HtmlTag>[];
    for (final tag in tags(source)) {
      if (tag.isClosing) {
        final match = stack.lastIndexWhere((open) => open.name == tag.name);
        if (match < 0) {
          findings.add(
            WebFinding(
              code: 'stray-end-tag',
              message: '没有对应开始标签的 </${tag.name}>',
              location: index.locate(tag.start),
              severity: WebFindingSeverity.error,
            ),
          );
          continue;
        }
        for (var position = stack.length - 1; position > match; position--) {
          final unclosed = stack.removeAt(position);
          findings.add(
            WebFinding(
              code: 'unclosed-tag',
              message:
                  '<${unclosed.name}> 在 </${tag.name}> 之前没有闭合'
                  '${_optionalEndTags.contains(unclosed.name) ? '（HTML 允许省略结束标签，请确认意图）' : ''}',
              location: index.locate(unclosed.start),
              severity: _optionalEndTags.contains(unclosed.name)
                  ? WebFindingSeverity.hint
                  : WebFindingSeverity.error,
            ),
          );
        }
        stack.removeAt(match);
        continue;
      }
      if (tag.isVoid || tag.selfClosing) continue;
      while (stack.isNotEmpty &&
          stack.last.name == tag.name &&
          _optionalEndTags.contains(tag.name)) {
        stack.removeLast();
      }
      stack.add(tag);
    }
    for (final unclosed in stack) {
      findings.add(
        WebFinding(
          code: 'unclosed-tag',
          message: '<${unclosed.name}> 直到文档结束都没有闭合',
          location: index.locate(unclosed.start),
          severity: _optionalEndTags.contains(unclosed.name)
              ? WebFindingSeverity.hint
              : WebFindingSeverity.error,
        ),
      );
    }
    findings.sort((a, b) => a.location.offset.compareTo(b.location.offset));
    return findings;
  }

  /// Accessibility basics from the MDN HTML references.
  static List<WebFinding> accessibilityFindings(String source) {
    final index = WebSourceIndex(source);
    final documents = _tokenize(source);
    final findings = <WebFinding>[];
    final documentTags = <HtmlTag>[];
    for (final token in documents) {
      if (token is _TagToken && !token.tag.isClosing) {
        documentTags.add(token.tag);
      }
    }
    HtmlTag? first(String name) {
      for (final tag in documentTags) {
        if (tag.name == name) return tag;
      }
      return null;
    }

    final html = first('html');
    if (html != null && ((html.attribute('lang') ?? '').trim().isEmpty)) {
      findings.add(
        WebFinding(
          code: 'missing-lang',
          message: '<html> 缺少 lang 属性，屏幕阅读器无法选择朗读语言',
          location: index.locate(html.start),
        ),
      );
    }
    if (first('title') == null &&
        documentTags.any((tag) => tag.name == 'head')) {
      findings.add(
        WebFinding(
          code: 'missing-title',
          message: '<head> 中没有 <title>，浏览器标签页会显示文件名',
          location: index.locate(first('head')!.start),
        ),
      );
    }
    final hasViewport = documentTags.any(
      (tag) =>
          tag.name == 'meta' &&
          (tag.attribute('name') ?? '').toLowerCase() == 'viewport',
    );
    if (!hasViewport && first('head') != null) {
      findings.add(
        WebFinding(
          code: 'missing-viewport',
          message: '<head> 中没有 viewport meta，移动端预览会按桌面宽度排版',
          location: index.locate(first('head')!.start),
          severity: WebFindingSeverity.hint,
        ),
      );
    }
    final labelledTargets = <String>{
      for (final tag in documentTags)
        if (tag.name == 'label' && (tag.attribute('for') ?? '').isNotEmpty)
          tag.attribute('for')!,
    };
    final emptyTargets = _emptyTextTargets(documents);
    final wrappedInputs = <int>{};
    var labelDepth = 0;
    for (final token in documents.whereType<_TagToken>()) {
      if (token.tag.name == 'label') {
        labelDepth = token.tag.isClosing
            ? (labelDepth - 1).clamp(0, labelDepth)
            : labelDepth + 1;
      }
      if (!token.tag.isClosing && token.tag.name == 'input' && labelDepth > 0) {
        wrappedInputs.add(token.start);
      }
    }
    for (final tag in documentTags) {
      if (tag.name == 'img' && tag.attribute('alt') == null) {
        findings.add(
          WebFinding(
            code: 'missing-alt',
            message: '<img> 缺少 alt 属性，装饰图请写 alt=""',
            location: index.locate(tag.start),
          ),
        );
      }
      if (tag.name == 'input') {
        final type = (tag.attribute('type') ?? 'text').toLowerCase();
        if (const {
          'hidden',
          'submit',
          'button',
          'reset',
          'image',
        }.contains(type)) {
          continue;
        }
        final id = (tag.attribute('id') ?? '').trim();
        final named =
            (tag.attribute('aria-label') ?? '').isNotEmpty ||
            (tag.attribute('aria-labelledby') ?? '').isNotEmpty ||
            wrappedInputs.contains(tag.start) ||
            (id.isNotEmpty && labelledTargets.contains(id));
        if (!named) {
          findings.add(
            WebFinding(
              code: 'unlabelled-input',
              message: '<input> 缺少可访问名称（label for / aria-label）',
              location: index.locate(tag.start),
            ),
          );
        }
      }
      if (!tag.isClosing &&
          (tag.name == 'a' || tag.name == 'button') &&
          emptyTargets.contains(tag.start)) {
        findings.add(
          WebFinding(
            code: 'empty-text-target',
            message: '<${tag.name}> 没有可读文本（aria-label 也没有），链接与按钮无法被识别',
            location: index.locate(tag.start),
          ),
        );
      }
    }
    final headings = documentTags.where((tag) => tag.name == 'h1').length;
    if (headings > 1) {
      findings.add(
        WebFinding(
          code: 'multiple-h1',
          message: '文档有 $headings 个 <h1>，通常每个页面只保留一个主标题',
          location: index.locate(first('h1')!.start),
          severity: WebFindingSeverity.hint,
        ),
      );
    }
    findings.sort((a, b) => a.location.offset.compareTo(b.location.offset));
    return findings;
  }

  /// Re-indents the document block by block.
  ///
  /// Text inside phrasing/heading containers stays on its tag's line
  /// (`<p>hi</p>`); everything else is one tag or run per line. The output is a
  /// predictable rewrite, not a browser-grade pretty printer.
  static String formatHtml(String source) {
    if (source.length > maxDocumentBytes) return source;
    final tokens = _tokenize(source);
    // Mixed/inline content and raw-text elements are indivisible: inserting
    // whitespace between spans changes rendered text, and trimming script/pre
    // lines can change a program or the displayed content.
    const blocks = {
      'html',
      'head',
      'body',
      'div',
      'section',
      'article',
      'main',
      'header',
      'footer',
      'nav',
      'aside',
      'ul',
      'ol',
      'dl',
      'table',
      'thead',
      'tbody',
      'tfoot',
      'tr',
      'form',
      'fieldset',
      'figure',
      'details',
      'p',
      'h1',
      'h2',
      'h3',
      'h4',
      'h5',
      'h6',
      'li',
      'dt',
      'dd',
      'br',
      'hr',
      'meta',
      'link',
    };
    final opens = <HtmlTag>[];
    final preserve = <int>{};
    final ends = <int, int>{};
    for (final token in tokens) {
      if (token is _TagToken) {
        final tag = token.tag;
        if (tag.isClosing) {
          if (opens.isEmpty || opens.last.name != tag.name) return source;
          ends[opens.removeLast().start] = tag.end;
        } else {
          // An inline fragment has no containing range that can absorb its
          // separators. Newlines between root siblings would change `AB` to
          // `A B`, so preserve the complete fragment in this case.
          if (opens.isEmpty && !blocks.contains(tag.name)) return source;
          if (!blocks.contains(tag.name) &&
              opens.isNotEmpty &&
              !{
                'script',
                'style',
                'title',
                'meta',
                'link',
              }.contains(tag.name)) {
            preserve.add(opens.last.start);
          }
          if (!blocks.contains(tag.name)) preserve.add(tag.start);
          if (!tag.isVoid && !tag.selfClosing) opens.add(tag);
        }
      } else if (token is _TextToken && token.text.trim().isNotEmpty) {
        if (opens.isEmpty) return source;
        preserve.add(opens.last.start);
      }
    }
    if (opens.isNotEmpty) return source;
    final lines = <String>[];
    var depth = 0;
    var skipUntil = -1;
    for (final token in tokens) {
      if (token.start < skipUntil) continue;
      switch (token) {
        case _TagToken(:final tag, :final raw):
          if (tag.isClosing) {
            depth = depth > 0 ? depth - 1 : 0;
            lines.add('${'  ' * depth}$raw');
          } else {
            final end = ends[tag.start];
            if (preserve.contains(tag.start) && end != null) {
              lines.add('${'  ' * depth}${source.substring(tag.start, end)}');
              skipUntil = end;
            } else {
              lines.add('${'  ' * depth}$raw');
              if (!tag.isVoid && !tag.selfClosing) depth++;
            }
          }
        case _TextToken(:final text):
          if (text.trim().isNotEmpty) lines.add('${'  ' * depth}$text');
        case _RawTextToken(:final text):
          lines.add(text);
        case _CommentToken(:final raw):
          lines.add('${'  ' * depth}$raw');
      }
    }
    return lines.join('\n');
  }

  /// Inspects a document on disk, following local stylesheets for `url()`.
  static WebDocumentInspection inspectFile(
    String documentPath, {
    required String rootPath,
  }) {
    try {
      return _inspectFile(documentPath, rootPath: rootPath);
    } on FileSystemException {
      return _fileFailure(
        documentPath,
        rootPath,
        'unreadable-document',
        '文档无法读取',
      );
    } on FormatException {
      return _fileFailure(
        documentPath,
        rootPath,
        'unreadable-document',
        '文档不是有效的 UTF-8 文本',
      );
    }
  }

  static WebDocumentInspection _fileFailure(
    String document,
    String root,
    String code,
    String message,
  ) => WebDocumentInspection(
    documentPath: document,
    rootPath: root,
    references: const [],
    cssFiles: const [],
    findings: [
      WebFinding(
        code: code,
        message: message,
        location: const WebSourceLocation(line: 1, column: 1, offset: 0),
        severity: WebFindingSeverity.error,
      ),
    ],
  );

  static WebDocumentInspection _inspectFile(
    String documentPath, {
    required String rootPath,
  }) {
    final canonicalRoot = _canonicalPath(rootPath);
    final canonicalDocument = _canonicalPath(documentPath);
    if (canonicalRoot == null ||
        canonicalDocument == null ||
        (canonicalRoot != canonicalDocument &&
            !p.isWithin(canonicalRoot, canonicalDocument))) {
      return _fileFailure(
        documentPath,
        rootPath,
        'escaping-document',
        '文档不在当前项目中',
      );
    }
    final file = File(documentPath);
    if (!file.existsSync()) {
      return WebDocumentInspection(
        documentPath: documentPath,
        rootPath: rootPath,
        references: const [],
        findings: [
          WebFinding(
            code: 'missing-document',
            message: '文档不存在：$documentPath',
            location: const WebSourceLocation(line: 1, column: 1, offset: 0),
            severity: WebFindingSeverity.error,
          ),
        ],
        cssFiles: const [],
      );
    }
    if (file.lengthSync() > maxDocumentBytes) {
      return WebDocumentInspection(
        documentPath: documentPath,
        rootPath: rootPath,
        references: const [],
        findings: [
          WebFinding(
            code: 'document-too-large',
            message: '文档超过 ${maxDocumentBytes ~/ 1024} KB，已跳过检查',
            location: const WebSourceLocation(line: 1, column: 1, offset: 0),
          ),
        ],
        cssFiles: const [],
      );
    }
    return inspectSource(
      file.readAsStringSync(),
      documentPath: documentPath,
      rootPath: rootPath,
    );
  }

  /// Inspects [source] as if it lived at [documentPath] inside [rootPath].
  ///
  /// [exists] and [readText] are injected so tests can drive the resolver with
  /// real temp files or with a fixed project snapshot.
  static WebDocumentInspection inspectSource(
    String source, {
    required String documentPath,
    required String rootPath,
    bool Function(String absolutePath)? exists,
    String? Function(String absolutePath)? readText,
  }) {
    if (source.length > maxDocumentBytes) {
      return _fileFailure(
        documentPath,
        rootPath,
        'document-too-large',
        '文本超过 1024 K 字符，已跳过检查',
      );
    }
    final fileExists =
        exists ??
        (path) => FileSystemEntity.typeSync(path) == FileSystemEntityType.file;
    final readFile =
        readText ??
        (path) {
          final file = File(path);
          try {
            if (!file.existsSync() || file.lengthSync() > maxDocumentBytes) {
              return null;
            }
            return file.readAsStringSync();
          } on FileSystemException {
            return null;
          } on FormatException {
            return null;
          }
        };
    final index = WebSourceIndex(source);
    final documentDirectory = exists == null
        ? (_canonicalPath(p.dirname(documentPath)) ?? p.dirname(documentPath))
        : p.dirname(documentPath);
    final canonicalRoot = exists == null
        ? (_canonicalPath(rootPath) ?? p.normalize(p.absolute(rootPath)))
        : p.normalize(p.absolute(rootPath));
    final references = <WebResourceReference>[];
    final cssFiles = <String>[];
    final stylesheetValues = <String>{};
    final scanFindings = <WebFinding>[];
    var referenceLimit = false;
    final tokens = _tokenize(source);
    final bases = tokens.whereType<_TagToken>().where(
      (token) =>
          !token.tag.isClosing &&
          token.tag.name == 'base' &&
          token.tag.attribute('href') != null,
    );
    if (bases.isNotEmpty) {
      scanFindings.add(
        WebFinding(
          code: 'base-reference',
          message: '文档含 <base href>，相对引用可能受其影响；请在预览中确认解析结果',
          location: index.locate(bases.first.start),
        ),
      );
    }

    void addReference({
      required String element,
      required String attribute,
      required String rawValue,
      required int offset,
      String? baseDirectory,
      String? origin,
      WebSourceIndex? sourceIndex,
    }) {
      if (references.length >= maxReferences) {
        referenceLimit = true;
        return;
      }
      final value = rawValue.trim();
      if (value.isEmpty || value.startsWith('#')) return;
      references.add(
        _resolve(
          element: element,
          attribute: attribute,
          rawValue: value,
          location: (sourceIndex ?? index).locate(offset),
          baseDirectory: baseDirectory ?? documentDirectory,
          rootPath: canonicalRoot,
          exists: fileExists,
          origin: origin,
          canonicalize: exists == null ? _canonicalPath : (path) => path,
        ),
      );
    }

    for (final token in tokens) {
      if (token is! _TagToken || token.tag.isClosing) continue;
      final tag = token.tag;
      if (tag.name == 'link' &&
          (tag.attribute('rel') ?? '')
              .toLowerCase()
              .split(RegExp(r'\s+'))
              .contains('stylesheet')) {
        stylesheetValues.add((tag.attribute('href') ?? '').trim());
      }
      final attributes = _resourceAttributes[tag.name] ?? const [];
      for (final attribute in attributes) {
        final value = tag.attribute(attribute);
        if (value == null) continue;
        if (attribute == 'srcset') {
          for (final candidate in _srcsetCandidates(value)) {
            addReference(
              element: tag.name,
              attribute: attribute,
              rawValue: candidate,
              offset: token.start,
            );
          }
          continue;
        }
        addReference(
          element: tag.name,
          attribute: attribute,
          rawValue: value,
          offset: token.start,
        );
      }
      final inlineStyle = tag.attribute('style');
      if (inlineStyle != null) {
        final stripped = stripCssComments(inlineStyle);
        for (final match in _cssUrlPattern.allMatches(stripped)) {
          if (isInsideQuotedRun(stripped, match.start)) continue;
          addReference(
            element: tag.name,
            attribute: 'style url()',
            rawValue: match.group(2) ?? match.group(4) ?? '',
            offset: token.start,
          );
        }
      }
      if (tag.name == 'style') {
        final raw = tokens
            .whereType<_RawTextToken>()
            .where((candidate) => candidate.ownerStart == token.start)
            .firstOrNull;
        final css = stripCssComments(raw?.text ?? '');
        for (final match in _cssUrlPattern.allMatches(css)) {
          if (isInsideQuotedRun(css, match.start)) continue;
          addReference(
            element: 'css',
            attribute: _isCssImport(css, match) ? '@import' : 'url()',
            rawValue: match.group(2) ?? match.group(4) ?? '',
            offset: (raw?.start ?? token.start) + match.start,
          );
        }
      }
    }

    // Follow local stylesheets so missing fonts/images are reported too.
    for (var cursor = 0; cursor < references.length; cursor++) {
      final reference = references[cursor];
      if (reference.attribute != '@import' &&
          !(reference.element == 'link' &&
              stylesheetValues.contains(reference.rawValue))) {
        continue;
      }
      if (reference.kind != WebResourceKind.localFile &&
          reference.kind != WebResourceKind.siteRoot) {
        continue;
      }
      final resolved = reference.resolvedPath;
      if (resolved == null) continue;
      if (cssFiles.contains(resolved)) continue;
      if (cssFiles.length >= 32) {
        scanFindings.add(
          WebFinding(
            code: 'stylesheet-limit',
            message: '只检查前 32 个本地样式表，其余文件尚未检查',
            location: reference.location,
          ),
        );
        break;
      }
      final absolute = p.normalize(p.join(canonicalRoot, resolved));
      final css = readFile(absolute);
      cssFiles.add(resolved);
      if (css == null) {
        scanFindings.add(
          WebFinding(
            code: 'unreadable-stylesheet',
            message: '样式表无法读取或超过 1024 KB：$resolved',
            location: reference.location,
          ),
        );
        continue;
      }
      final stripped = stripCssComments(css);
      for (final match in _cssUrlPattern.allMatches(stripped)) {
        if (isInsideQuotedRun(stripped, match.start)) continue;
        addReference(
          element: 'css',
          attribute: _isCssImport(stripped, match) ? '@import' : 'url()',
          rawValue: match.group(2) ?? match.group(4) ?? '',
          offset: match.start,
          baseDirectory: p.dirname(absolute),
          origin: resolved,
          sourceIndex: WebSourceIndex(css),
        );
      }
    }

    final findings = <WebFinding>[
      ...scanFindings,
      if (referenceLimit)
        WebFinding(
          code: 'reference-limit',
          message: '只显示前 $maxReferences 条引用，其余引用尚未检查',
          location: index.locate(source.length),
        ),
      ...structureFindings(source),
      ...accessibilityFindings(source),
      for (final reference in references)
        if (reference.isNetwork)
          WebFinding(
            code: 'external-reference',
            message: '外部引用 ${reference.rawValue}：离线产品不会加载网络资源',
            location: reference.location,
          ),
      for (final reference in references)
        if (reference.isMissing)
          WebFinding(
            code: 'missing-resource',
            message:
                '找不到文件 ${reference.rawValue}'
                '${reference.resolvedPath == null ? '' : '（解析为 ${reference.resolvedPath}）'}',
            location: reference.location,
            severity: WebFindingSeverity.error,
          ),
      for (final reference in references)
        if (reference.kind == WebResourceKind.escaping ||
            reference.kind == WebResourceKind.invalid)
          WebFinding(
            code: 'invalid-resource',
            message: '${reference.kindLabel}：${reference.rawValue}',
            location: reference.location,
            severity: WebFindingSeverity.error,
          ),
    ]..sort((a, b) => a.location.offset.compareTo(b.location.offset));

    return WebDocumentInspection(
      documentPath: documentPath,
      rootPath: canonicalRoot,
      references: List.unmodifiable(references),
      findings: List.unmodifiable(findings),
      cssFiles: List.unmodifiable(cssFiles),
    );
  }

  /// Classifies one reference against the project root.
  static WebResourceReference _resolve({
    required String element,
    required String attribute,
    required String rawValue,
    required WebSourceLocation location,
    required String baseDirectory,
    required String rootPath,
    required bool Function(String absolutePath) exists,
    required String? Function(String absolutePath) canonicalize,
    String? origin,
  }) {
    final value =
        (html.parseFragment(rawValue, container: 'textarea').text ?? rawValue)
            .trim();
    final schemeMatch = RegExp(
      r'^([a-zA-Z][a-zA-Z0-9+.-]*):',
    ).firstMatch(value);
    if (value.startsWith('//')) {
      return WebResourceReference(
        element: element,
        attribute: attribute,
        rawValue: value,
        kind: WebResourceKind.external,
        location: location,
        origin: origin,
      );
    }
    if (schemeMatch != null) {
      final scheme = schemeMatch.group(1)!.toLowerCase();
      final kind =
          scheme == 'http' ||
              scheme == 'https' ||
              scheme == 'ws' ||
              scheme == 'wss' ||
              scheme == 'ftp'
          ? WebResourceKind.external
          : scheme == 'data' ||
                scheme == 'javascript' ||
                scheme == 'mailto' ||
                scheme == 'tel' ||
                scheme == 'sms' ||
                scheme == 'blob'
          ? WebResourceKind.inline
          : WebResourceKind.invalid;
      return WebResourceReference(
        element: element,
        attribute: attribute,
        rawValue: value,
        kind: kind,
        location: location,
        origin: origin,
      );
    }

    final withoutQuery = value.split('#').first.split('?').first;
    if (withoutQuery.isEmpty) {
      return WebResourceReference(
        element: element,
        attribute: attribute,
        rawValue: value,
        kind: WebResourceKind.inline,
        location: location,
        origin: origin,
      );
    }
    String decoded;
    try {
      decoded = Uri.decodeFull(withoutQuery);
    } on ArgumentError {
      return WebResourceReference(
        element: element,
        attribute: attribute,
        rawValue: value,
        kind: WebResourceKind.invalid,
        location: location,
        origin: origin,
      );
    } on FormatException {
      return WebResourceReference(
        element: element,
        attribute: attribute,
        rawValue: value,
        kind: WebResourceKind.invalid,
        location: location,
        origin: origin,
      );
    }
    final siteRoot = decoded.startsWith('/');
    final base = siteRoot ? rootPath : baseDirectory;
    final relative = siteRoot ? decoded.substring(1) : decoded;
    final absolute = p.normalize(p.absolute(p.join(base, relative)));
    final normalizedRoot = p.normalize(rootPath);
    final inside =
        absolute == normalizedRoot || p.isWithin(normalizedRoot, absolute);
    if (!inside) {
      return WebResourceReference(
        element: element,
        attribute: attribute,
        rawValue: value,
        kind: WebResourceKind.escaping,
        location: location,
        origin: origin,
      );
    }
    final display = toPosixDisplay(p.relative(absolute, from: normalizedRoot));
    final trailingSlash = decoded.endsWith('/');
    final target = trailingSlash ? p.join(absolute, 'index.html') : absolute;
    final realTarget = canonicalize(target);
    if (realTarget == null ||
        (realTarget != normalizedRoot &&
            !p.isWithin(normalizedRoot, realTarget))) {
      return WebResourceReference(
        element: element,
        attribute: attribute,
        rawValue: value,
        kind: WebResourceKind.escaping,
        location: location,
        origin: origin,
      );
    }
    final found = exists(target);
    return WebResourceReference(
      element: element,
      attribute: attribute,
      rawValue: value,
      kind: found
          ? (siteRoot ? WebResourceKind.siteRoot : WebResourceKind.localFile)
          : WebResourceKind.missing,
      location: location,
      resolvedPath: display,
      exists: found,
      origin: origin,
    );
  }

  static Set<int> _emptyTextTargets(List<_Token> tokens) {
    final active = <HtmlTag>[];
    final readable = <int>{};
    final empty = <int>{};
    void content() {
      readable.addAll(active.map((tag) => tag.start));
    }

    for (final token in tokens) {
      switch (token) {
        case _TagToken(tag: final candidate):
          if (candidate.isClosing &&
              (candidate.name == 'a' || candidate.name == 'button')) {
            final match = active.lastIndexWhere(
              (tag) => tag.name == candidate.name,
            );
            if (match >= 0) {
              final tag = active.removeAt(match);
              if (!readable.contains(tag.start)) empty.add(tag.start);
            }
          } else if (!candidate.isClosing) {
            final named =
                (candidate.attribute('aria-label') ?? '').trim().isNotEmpty ||
                (candidate.attribute('aria-labelledby') ?? '')
                    .trim()
                    .isNotEmpty ||
                (candidate.attribute('title') ?? '').trim().isNotEmpty;
            if (named ||
                (candidate.name == 'img' &&
                    (candidate.attribute('alt') ?? '').trim().isNotEmpty)) {
              content();
            }
            if (candidate.name == 'a' || candidate.name == 'button') {
              active.add(candidate);
              if (named) readable.add(candidate.start);
            }
          }
        case _TextToken(text: final text):
          if (text.trim().isNotEmpty) content();
        case _RawTextToken(text: final text):
          if (text.trim().isNotEmpty) content();
        case _CommentToken():
          break;
      }
    }
    return empty;
  }

  static Iterable<String> _srcsetCandidates(String value) sync* {
    var position = 0;
    while (position < value.length) {
      while (position < value.length &&
          (_isHtmlSpace(value[position]) || value[position] == ',')) {
        position++;
      }
      final start = position;
      while (position < value.length && !_isHtmlSpace(value[position])) {
        position++;
      }
      var url = value.substring(start, position);
      final separated = url.endsWith(',');
      while (url.endsWith(',')) {
        url = url.substring(0, url.length - 1);
      }
      if (url.isNotEmpty) yield url;
      if (separated) continue;
      while (position < value.length && value[position] != ',') {
        position++;
      }
    }
  }

  static final RegExp _cssUrlPattern = RegExp(
    r'''url\(\s*(['"]?)([^'")]*)\1\s*\)|@import\s+(?:url\()?\s*(['"])([^'"]*)\3''',
    caseSensitive: false,
  );

  static bool _isCssImport(String source, RegExpMatch match) =>
      match.group(3) != null ||
      RegExp(
        r'@import\s*$',
        caseSensitive: false,
      ).hasMatch(source.substring(0, match.start));

  static List<_Token> _tokenize(String source) {
    final tokens = <_Token>[];
    final lower = source.toLowerCase();
    var position = 0;
    while (position < source.length) {
      final open = source.indexOf('<', position);
      if (open < 0) {
        tokens.add(_TextToken(source.substring(position), position));
        break;
      }
      if (open > position) {
        tokens.add(_TextToken(source.substring(position, open), position));
      }
      if (source.startsWith('<!--', open)) {
        final close = source.indexOf('-->', open + 4);
        final end = close < 0 ? source.length : close + 3;
        tokens.add(
          _CommentToken(
            source.substring(open, end),
            start: open,
            end: end,
            isFormatted: close >= 0,
          ),
        );
        position = end;
        continue;
      }
      if (source.startsWith('<!', open) || source.startsWith('<?', open)) {
        final close = source.indexOf('>', open + 2);
        final end = close < 0 ? source.length : close + 1;
        tokens.add(
          _CommentToken(
            source.substring(open, end),
            start: open,
            end: end,
            isFormatted: close >= 0,
          ),
        );
        position = end;
        continue;
      }
      final parsed = _readTag(source, open);
      if (parsed == null) {
        tokens.add(_TextToken('<', open));
        position = open + 1;
        continue;
      }
      final token = _TagToken(parsed, source.substring(open, parsed.end), open);
      tokens.add(token);
      position = parsed.end;
      if (!parsed.isClosing &&
          !parsed.selfClosing &&
          (parsed.name == 'script' ||
              parsed.name == 'style' ||
              parsed.name == 'textarea' ||
              parsed.name == 'title')) {
        final marker = '</${parsed.name}';
        var close = lower.indexOf(marker, position);
        while (close >= 0) {
          final afterName = close + marker.length;
          if (afterName < source.length &&
              (_isHtmlSpace(source[afterName]) ||
                  source[afterName] == '/' ||
                  source[afterName] == '>')) {
            break;
          }
          close = lower.indexOf(marker, afterName);
        }
        final rawEnd = close < 0 ? source.length : close;
        if (rawEnd > position) {
          tokens.add(
            _RawTextToken(
              source.substring(position, rawEnd),
              start: position,
              ownerStart: open,
              ownerName: parsed.name,
            ),
          );
        }
        position = rawEnd;
      }
    }
    return tokens;
  }

  static HtmlTag? _readTag(String source, int start) {
    var position = start + 1;
    var closing = false;
    if (position < source.length && source[position] == '/') {
      closing = true;
      position++;
    }
    while (position < source.length && _isHtmlSpace(source[position])) {
      position++;
    }
    final nameStart = position;
    while (position < source.length &&
        RegExp(r'[A-Za-z0-9:_-]').hasMatch(source[position])) {
      position++;
    }
    if (position == nameStart) return null;
    final name = source.substring(nameStart, position).toLowerCase();
    final attributes = <String, String>{};
    var selfClosing = false;
    while (position < source.length) {
      while (position < source.length && _isHtmlSpace(source[position])) {
        position++;
      }
      if (position >= source.length) break;
      final char = source[position];
      if (char == '>') {
        position++;
        break;
      }
      if (char == '/' &&
          position + 1 < source.length &&
          source[position + 1] == '>') {
        selfClosing = true;
        position += 2;
        break;
      }
      final attributeStart = position;
      while (position < source.length &&
          !_isHtmlSpace(source[position]) &&
          !'=/>'.contains(source[position])) {
        position++;
      }
      final attributeName = source
          .substring(attributeStart, position)
          .toLowerCase();
      if (attributeName.isEmpty) {
        position++;
        continue;
      }
      while (position < source.length && _isHtmlSpace(source[position])) {
        position++;
      }
      var value = '';
      if (position < source.length && source[position] == '=') {
        position++;
        while (position < source.length && _isHtmlSpace(source[position])) {
          position++;
        }
        if (position < source.length &&
            (source[position] == '"' || source[position] == "'")) {
          final quote = source[position];
          position++;
          final valueStart = position;
          while (position < source.length && source[position] != quote) {
            position++;
          }
          value = source.substring(valueStart, position);
          if (position < source.length) position++;
        } else {
          final valueStart = position;
          while (position < source.length &&
              !_isHtmlSpace(source[position]) &&
              source[position] != '>') {
            position++;
          }
          value = source.substring(valueStart, position);
        }
      }
      attributes.putIfAbsent(attributeName, () => value);
    }
    return HtmlTag(
      name: name,
      isClosing: closing,
      selfClosing: selfClosing,
      attributes: Map.unmodifiable(attributes),
      start: start,
      end: position,
    );
  }

  static bool _isHtmlSpace(String char) =>
      char == ' ' ||
      char == '\n' ||
      char == '\r' ||
      char == '\t' ||
      char == '\f';
}

/// Resolve existing ancestors too, so a missing child of an escaping symlink
/// cannot be mistaken for a path confined to this project.
String? _canonicalPath(String path) {
  var existing = p.normalize(p.absolute(path));
  final suffix = <String>[];
  try {
    while (FileSystemEntity.typeSync(existing, followLinks: false) ==
        FileSystemEntityType.notFound) {
      final parent = p.dirname(existing);
      if (parent == existing) return null;
      suffix.insert(0, p.basename(existing));
      existing = parent;
    }
    return p.normalize(
      p.joinAll([File(existing).resolveSymbolicLinksSync(), ...suffix]),
    );
  } on FileSystemException {
    return null;
  }
}

sealed class _Token {
  const _Token(this.start);

  final int start;
}

class _TextToken extends _Token {
  const _TextToken(this.text, int start) : super(start);

  final String text;
}

class _RawTextToken extends _Token {
  const _RawTextToken(
    this.text, {
    required int start,
    required this.ownerStart,
    required this.ownerName,
  }) : super(start);

  final String text;

  /// Offset of the opening `<style>` / `<script>` tag that owns this run.
  final int ownerStart;

  /// Lower-case name of the owning raw-text element.
  final String ownerName;
}

class _CommentToken extends _Token {
  const _CommentToken(
    this.raw, {
    required int start,
    required int end,
    required this.isFormatted,
  }) : super(start);

  final String raw;

  /// False when the comment/declaration had no closing marker.
  final bool isFormatted;
}

class _TagToken extends _Token {
  const _TagToken(this.tag, this.raw, int start) : super(start);

  final HtmlTag tag;
  final String raw;
}
