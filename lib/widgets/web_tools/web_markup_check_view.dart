import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../services/web_css_tools.dart';
import '../../services/web_markup_inspector.dart';
import '../../services/web_source_scan.dart';
import 'web_tools_panel.dart';

/// HTML / CSS structure, accessibility and re-indentation in one inline panel.
///
/// The findings are produced by the bounded scanners in
/// `lib/services/web_markup_inspector.dart` and `lib/services/web_css_tools.dart`;
/// they are reported as inspections (`line:column` + message) and never claimed
/// to be a full validating compiler.
class WebMarkupCheckInlineView extends StatefulWidget {
  const WebMarkupCheckInlineView({super.key});

  static const String title = '结构检查与格式化';

  @override
  State<WebMarkupCheckInlineView> createState() =>
      _WebMarkupCheckInlineViewState();
}

class _WebMarkupCheckInlineViewState extends State<WebMarkupCheckInlineView> {
  final _source = TextEditingController(
    text:
        '<!doctype html>\n<html>\n<head>\n  <title>示例</title>\n</head>\n'
        '<body>\n  <img src="logo.png">\n  <div><span>未闭合\n</body>\n</html>',
  );
  bool _html = true;
  bool _showFormatted = false;

  @override
  void dispose() {
    _source.dispose();
    super.dispose();
  }

  List<WebFinding> get _findings => _html
      ? [
          ...WebMarkupInspector.structureFindings(_source.text),
          ...WebMarkupInspector.accessibilityFindings(_source.text),
        ]
      : WebCssTools.diagnostics(_source.text);

  String get _formatted => _html
      ? WebMarkupInspector.formatHtml(_source.text)
      : WebCssTools.format(_source.text);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final findings = _findings;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: SegmentedButton<bool>(
            segments: const [
              ButtonSegment(value: true, label: Text('HTML')),
              ButtonSegment(value: false, label: Text('CSS')),
            ],
            selected: {_html},
            showSelectedIcon: false,
            onSelectionChanged: (value) => setState(() {
              _html = value.first;
              _showFormatted = false;
            }),
          ),
        ),
        const SizedBox(height: 10),
        TextField(
          controller: _source,
          maxLength: WebCssTools.maxSourceCharacters,
          minLines: 6,
          maxLines: 12,
          style: const TextStyle(fontFamily: 'monospace', fontSize: 13),
          onChanged: (_) => setState(() {}),
          decoration: InputDecoration(
            labelText: _html ? 'HTML 片段' : 'CSS 片段',
            helperText: _html
                ? '标签配对 + 可访问性基础检查（不是完整 HTML 校验器）'
                : '括号、注释、字符串与声明检查',
            border: const OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            OutlinedButton.icon(
              onPressed: () => setState(() => _showFormatted = !_showFormatted),
              icon: Icon(
                _showFormatted
                    ? Icons.visibility_off_outlined
                    : Icons.format_align_left,
              ),
              label: Text(_showFormatted ? '隐藏重排结果' : '重排缩进'),
            ),
            if (_showFormatted)
              IconButton(
                tooltip: '复制重排结果',
                onPressed: () async {
                  await Clipboard.setData(ClipboardData(text: _formatted));
                  if (!context.mounted) return;
                  ScaffoldMessenger.of(context)
                    ..hideCurrentSnackBar()
                    ..showSnackBar(const SnackBar(content: Text('已复制')));
                },
                icon: const Icon(Icons.copy_all_outlined),
              ),
          ],
        ),
        WebToolOutput(
          title: findings.isEmpty ? '结构检查通过' : '发现 ${findings.length} 条提示',
          child: WebFindingList(findings: findings),
        ),
        if (_showFormatted)
          WebToolOutput(
            title: '重排结果（逐标签重排）',
            child: SelectableText(
              _formatted,
              style: const TextStyle(
                fontFamily: 'monospace',
                fontSize: 12,
                height: 1.4,
              ),
            ),
          ),
        Padding(
          padding: const EdgeInsets.only(top: 6),
          child: Text(
            '检查器只读取这段文本；不会写入项目，也不会加载任何外部资源。',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
        ),
      ],
    );
  }
}
