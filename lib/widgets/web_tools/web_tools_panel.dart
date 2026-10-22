import 'package:flutter/material.dart';
import 'package:qfli_studio_core/widgets/tool_widgets.dart';

import '../../services/web_source_scan.dart';

/// One section of the integrated tools page: icon + title + optional subtitle
/// and the real controls underneath.
///
/// The WebForge tools page renders these sections inline instead of pushing a
/// second "feature hub" route, so every control is one scroll away.
class WebToolPanel extends StatelessWidget {
  const WebToolPanel({
    super.key,
    required this.icon,
    required this.title,
    this.subtitle,
    required this.child,
  });

  final IconData icon;
  final String title;
  final String? subtitle;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ToolsSectionHeading(icon: icon, title: title, subtitle: subtitle),
        const SizedBox(height: 10),
        child,
      ],
    );
  }
}

/// A bounded list of inspection findings, grouped by severity.
///
/// The cap keeps the page height finite: a document with hundreds of problems
/// reports the first [maxItems] and a "还有 N 条" line.
class WebFindingList extends StatelessWidget {
  const WebFindingList({
    super.key,
    required this.findings,
    this.maxItems = 30,
    this.emptyLabel = '没有发现问题',
  });

  final List<WebFinding> findings;
  final int maxItems;
  final String emptyLabel;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    if (findings.isEmpty) {
      return Row(
        children: [
          Icon(
            Icons.check_circle_outline,
            size: 18,
            color: theme.colorScheme.primary,
          ),
          const SizedBox(width: 6),
          Expanded(child: Text(emptyLabel, style: theme.textTheme.bodySmall)),
        ],
      );
    }
    final shown = findings.take(maxItems).toList();
    final hidden = findings.length - shown.length;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (final finding in shown)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 3),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(
                  switch (finding.severity) {
                    WebFindingSeverity.error => Icons.error_outline,
                    WebFindingSeverity.warning => Icons.warning_amber_outlined,
                    WebFindingSeverity.hint => Icons.info_outline,
                  },
                  size: 18,
                  color: switch (finding.severity) {
                    WebFindingSeverity.error => theme.colorScheme.error,
                    WebFindingSeverity.warning => theme.colorScheme.tertiary,
                    WebFindingSeverity.hint =>
                      theme.colorScheme.onSurfaceVariant,
                  },
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: SelectableText.rich(
                    TextSpan(
                      children: [
                        TextSpan(
                          text: '${finding.location.label}  ',
                          style: const TextStyle(
                            fontFamily: 'monospace',
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        TextSpan(text: finding.message),
                      ],
                    ),
                    style: theme.textTheme.bodySmall,
                  ),
                ),
              ],
            ),
          ),
        if (hidden > 0)
          Text(
            '还有 $hidden 条未显示',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
      ],
    );
  }
}

/// A compact `label: value` row without the shared [ResultRow] width budget,
/// used inside dense inspection output.
class WebValueRow extends StatelessWidget {
  const WebValueRow({
    super.key,
    required this.label,
    required this.value,
    this.monospace = true,
    this.color,
  });

  final String label;
  final String value;
  final bool monospace;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Flexible(
            child: Text(
              label,
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            flex: 2,
            child: SelectableText(
              value,
              style: theme.textTheme.bodySmall?.copyWith(
                fontFamily: monospace ? 'monospace' : null,
                color: color,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Summary chip row used above result lists.
class WebSummaryChips extends StatelessWidget {
  const WebSummaryChips({super.key, required this.entries});

  final List<(String, int)> entries;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Wrap(
      spacing: 8,
      runSpacing: 6,
      children: [
        for (final (label, count) in entries)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: theme.colorScheme.surfaceContainerHighest,
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text('$label $count', style: theme.textTheme.labelSmall),
          ),
      ],
    );
  }
}

/// An outlined surface that keeps a block of tool output visually grouped.
class WebToolOutput extends StatelessWidget {
  const WebToolOutput({super.key, this.title, required this.child});

  final String? title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(top: 10),
      padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: theme.colorScheme.outlineVariant.withValues(alpha: 0.7),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (title != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Text(title!, style: theme.textTheme.titleSmall),
            ),
          child,
        ],
      ),
    );
  }
}

/// Keeps an existing page-style view (its own `ListView`) inside the tools page
/// with a finite height, so both scroll surfaces stay bounded.
class WebEmbeddedPanel extends StatelessWidget {
  const WebEmbeddedPanel({
    super.key,
    required this.height,
    required this.child,
  });

  final double height;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      height: height,
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: theme.colorScheme.outlineVariant.withValues(alpha: 0.7),
        ),
      ),
      child: child,
    );
  }
}
