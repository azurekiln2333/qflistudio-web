import 'package:flutter/material.dart';

import '../../services/web_css_tools.dart';
import 'web_tools_panel.dart';

/// Which offline CSS inspection the embedded panel shows.
enum _CssMode { colors, boxModel, specificity, duplicates }

/// Inline CSS inspection: colours with WCAG contrast, the box model, selector
/// specificity and duplicated declarations.
///
/// Everything is recomputed from the pasted text on every keystroke — there is
/// no compiler, no network and no project write. Results are capped so the
/// surrounding tools page keeps a finite height.
class WebCssToolsInlineView extends StatefulWidget {
  const WebCssToolsInlineView({super.key});

  static const String title = 'CSS 颜色与盒子';

  @override
  State<WebCssToolsInlineView> createState() => _WebCssToolsInlineViewState();
}

class _WebCssToolsInlineViewState extends State<WebCssToolsInlineView> {
  static const int _maxRows = 24;

  final _source = TextEditingController(
    text:
        '.hero {\n  color: rebeccapurple;\n  background: #ffffff;\n'
        '  padding: 12px 20px;\n  border-width: 1px;\n  border-style: solid;\n'
        '}\n.title:hover { color: #777; }',
  );
  final _background = TextEditingController(text: '#ffffff');
  final _contentWidth = TextEditingController(text: '320');
  final _contentHeight = TextEditingController(text: '180');
  _CssMode _mode = _CssMode.colors;

  @override
  void dispose() {
    _source.dispose();
    _background.dispose();
    _contentWidth.dispose();
    _contentHeight.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextField(
          controller: _source,
          maxLength: WebCssTools.maxSourceCharacters,
          minLines: 5,
          maxLines: 10,
          style: const TextStyle(fontFamily: 'monospace', fontSize: 13),
          onChanged: (_) => setState(() {}),
          decoration: const InputDecoration(
            labelText: '样式表',
            helperText: '只在本机解析，不会写入项目文件',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 10),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: SegmentedButton<_CssMode>(
            segments: const [
              ButtonSegment(value: _CssMode.colors, label: Text('颜色')),
              ButtonSegment(value: _CssMode.boxModel, label: Text('盒模型')),
              ButtonSegment(value: _CssMode.specificity, label: Text('优先级')),
              ButtonSegment(value: _CssMode.duplicates, label: Text('重复声明')),
            ],
            selected: {_mode},
            showSelectedIcon: false,
            onSelectionChanged: (value) => setState(() => _mode = value.first),
          ),
        ),
        const SizedBox(height: 10),
        switch (_mode) {
          _CssMode.colors => _buildColors(context, theme),
          _CssMode.boxModel => _buildBoxModel(context, theme),
          _CssMode.specificity => _buildSpecificity(context, theme),
          _CssMode.duplicates => _buildDuplicates(context, theme),
        },
      ],
    );
  }

  Widget _buildColors(BuildContext context, ThemeData theme) {
    final uses = WebCssTools.findColors(_source.text);
    final background = CssColor.parse(_background.text);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: TextField(
                controller: _background,
                onChanged: (_) => setState(() {}),
                decoration: InputDecoration(
                  labelText: '背景色（用于对比度）',
                  isDense: true,
                  errorText: background == null ? '无法解析该颜色' : null,
                  border: const OutlineInputBorder(),
                ),
              ),
            ),
            if (background != null) ...[
              const SizedBox(width: 10),
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: Color.fromARGB(
                    (background.alpha * 255).round(),
                    background.red,
                    background.green,
                    background.blue,
                  ),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: theme.colorScheme.outlineVariant),
                ),
              ),
            ],
          ],
        ),
        if (uses.isEmpty)
          const Padding(
            padding: EdgeInsets.only(top: 10),
            child: Text('未找到颜色值'),
          )
        else
          WebToolOutput(
            title: '找到 ${uses.length} 个颜色',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                for (final use in uses.take(_maxRows))
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        WebValueRow(
                          label: '${use.location.label} ${use.raw}',
                          value:
                              '${use.color.hex}  ${use.color.rgb}  ${use.color.hsl}',
                        ),
                        if (background != null)
                          WebValueRow(
                            label: '  对比度',
                            value: _contrastLabel(use.color, background),
                            color: _contrastColor(use.color, background, theme),
                          ),
                      ],
                    ),
                  ),
                if (uses.length > _maxRows)
                  Text(
                    '还有 ${uses.length - _maxRows} 个颜色未显示',
                    style: theme.textTheme.bodySmall,
                  ),
              ],
            ),
          ),
      ],
    );
  }

  String _contrastLabel(CssColor foreground, CssColor background) {
    final ratio = CssColor.contrastRatio(foreground, background);
    if (ratio == null) return '需要不透明颜色才能计算对比度';
    final pass = ratio >= 4.5
        ? 'AA 正文通过'
        : ratio >= 3
        ? '仅大字号通过 AA'
        : '不满足 AA';
    return '${ratio.toStringAsFixed(2)}:1 · $pass';
  }

  Color? _contrastColor(
    CssColor foreground,
    CssColor background,
    ThemeData theme,
  ) {
    final ratio = CssColor.contrastRatio(foreground, background);
    if (ratio == null) return theme.colorScheme.onSurfaceVariant;
    return ratio >= 4.5 ? theme.colorScheme.primary : theme.colorScheme.error;
  }

  Widget _buildBoxModel(BuildContext context, ThemeData theme) {
    final sheet = WebCssTools.parse(_source.text);
    final width = double.tryParse(_contentWidth.text.trim());
    final height = double.tryParse(_contentHeight.text.trim());
    final models = <(String, String, CssBoxModel)>[];
    for (final rule in sheet.rules) {
      final model = WebCssTools.boxModel(
        rule.declarations,
        contentWidth: width,
        contentHeight: height,
      );
      if (model == null) continue;
      models.add((rule.selector, rule.location.label, model));
    }
    if (models.isEmpty) {
      return const Padding(
        padding: EdgeInsets.only(top: 10),
        child: Text('没有 padding / margin / border-width 声明'),
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _contentWidth,
                keyboardType: TextInputType.number,
                onChanged: (_) => setState(() {}),
                decoration: const InputDecoration(
                  labelText: 'width 值 px',
                  isDense: true,
                  border: OutlineInputBorder(),
                ),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: TextField(
                controller: _contentHeight,
                keyboardType: TextInputType.number,
                onChanged: (_) => setState(() {}),
                decoration: const InputDecoration(
                  labelText: 'height 值 px',
                  isDense: true,
                  border: OutlineInputBorder(),
                ),
              ),
            ),
          ],
        ),
        for (final (selector, location, model) in models.take(_maxRows))
          WebToolOutput(
            title: '$selector  ·  $location',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                for (final (label, value) in model.toRows())
                  WebValueRow(label: label, value: value),
              ],
            ),
          ),
        if (models.length > _maxRows)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(
              '还有 ${models.length - _maxRows} 条规则未显示',
              style: theme.textTheme.bodySmall,
            ),
          ),
      ],
    );
  }

  Widget _buildSpecificity(BuildContext context, ThemeData theme) {
    final entries = WebCssTools.specificities(_source.text)
      ..sort((a, b) => b.compareTo(a));
    if (entries.isEmpty) {
      return const Padding(
        padding: EdgeInsets.only(top: 10),
        child: Text('没有选择器'),
      );
    }
    return WebToolOutput(
      title: '按 (ID, 类, 类型) 从高到低',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          for (final entry in entries.take(_maxRows))
            WebValueRow(
              label: entry.location.label,
              value: '${entry.label}  ${entry.selector}',
            ),
          if (entries.length > _maxRows)
            Text(
              '还有 ${entries.length - _maxRows} 个选择器未显示',
              style: theme.textTheme.bodySmall,
            ),
        ],
      ),
    );
  }

  Widget _buildDuplicates(BuildContext context, ThemeData theme) {
    final duplicates = WebCssTools.duplicateDeclarations(_source.text);
    if (duplicates.isEmpty) {
      return Row(
        children: [
          Icon(
            Icons.check_circle_outline,
            size: 18,
            color: theme.colorScheme.primary,
          ),
          const SizedBox(width: 6),
          const Expanded(child: Text('没有重复声明')),
        ],
      );
    }
    return WebToolOutput(
      title: '${duplicates.length} 处重复声明（需结合有效值与 !important 判断）',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          for (final duplicate in duplicates.take(_maxRows))
            WebValueRow(
              label: duplicate.selector,
              value:
                  '${duplicate.property}  ×${duplicate.occurrences.length}  '
                  '${duplicate.occurrences.map((item) => item.location.label).join(' → ')}',
            ),
        ],
      ),
    );
  }
}
