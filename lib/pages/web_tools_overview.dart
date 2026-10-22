import 'package:flutter/material.dart';
import 'package:qfli_studio_core/pages/tools_grid.dart';
import 'package:qfli_studio_core/store/project_store.dart';
import 'package:qfli_studio_core/widgets/tool_widgets.dart';

import '../widgets/web_tools/web_css_tools_view.dart';
import '../widgets/web_tools/web_markup_check_view.dart';
import '../widgets/web_tools/web_source_inspector_view.dart';
import '../widgets/web_tools/web_tools_panel.dart';
import 'web_tools_page.dart';

/// WebForge 的整合工具页：Web 专属能力全部直接铺在这里，不再 push 二级页面。
///
/// 通过 [StudioProfile.toolsTabBuilder] 接线（见 `lib/main.dart`）：内核
/// `FunctionsTab` 会在自己的 Scaffold 里渲染这个 body，因此这个页面就是
/// 「工具」tab 本身，只有一次滚动。
///
/// 结构（自上而下）：
/// 1. 终端入口 —— 复用内核已有的全屏终端路由；
/// 2. 本地服务与 Web 编解码 —— 嵌入 [WebServerToolsView] / [WebCodecToolsView]，
///    各自在一个固定高度的盒子里，靠自己的 `ListView` 有限滚动；
/// 3. Web 专属离线检查 —— 文档资源检查、CSS 颜色与盒子、结构检查与格式化；
/// 4. 通用工具 —— 内核 [commonTools] 卡片，保持原有入口不丢失。
///
/// 这里只展示本机离线能力：HTTP 工具和外部代理属于联网入口，由
/// [WebToolsPage] 按 `offlineOnly` 裁掉，此概览也不暴露它们。
class WebToolsOverview extends StatelessWidget {
  const WebToolsOverview({super.key, required this.store, this.onOpenTerminal});

  final ProjectStore store;

  /// 内核已有的全屏终端路由；终端入口复用而不是自己重建一个。
  final VoidCallback? onOpenTerminal;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return LayoutBuilder(
      builder: (context, constraints) {
        final horizontal = ToolsTheme.horizontalPadding(constraints.maxWidth);
        return CustomScrollView(
          key: const PageStorageKey<String>('web-tools-scroll'),
          slivers: [
            // The whole control column is one sliver child on purpose: slivers
            // stay mounted while `SliverList` children are disposed when they
            // scroll out of view, and unmounting the embedded server view would
            // stop a running 127.0.0.1 preview mid-session. Only the shared
            // card grid below is lazy.
            SliverPadding(
              padding: EdgeInsets.fromLTRB(horizontal, 16, horizontal, 0),
              sliver: SliverToBoxAdapter(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const _OfflineBanner(),
                    if (onOpenTerminal != null) ...[
                      const SizedBox(height: 16),
                      ToolsSectionHeading(
                        icon: Icons.terminal,
                        title: '终端',
                        subtitle: '在本机沙盒中运行命令，离线可用',
                      ),
                      const SizedBox(height: 8),
                      Align(
                        alignment: Alignment.centerLeft,
                        child: FilledButton.tonalIcon(
                          onPressed: onOpenTerminal,
                          icon: const Icon(Icons.terminal),
                          label: const Text('打开终端'),
                        ),
                      ),
                    ],
                    const SizedBox(height: 22),
                    WebToolPanel(
                      icon: Icons.dns_outlined,
                      title: '本地服务',
                      subtitle: '启动 127.0.0.1 预览，查看请求与控制台',
                      child: WebEmbeddedPanel(
                        height: 380,
                        child: WebServerToolsView(store: store),
                      ),
                    ),
                    const SizedBox(height: 22),
                    const WebToolPanel(
                      icon: Icons.data_object,
                      title: 'Web 编解码',
                      subtitle: 'JSON / URL / Base64 互转，纯本机计算',
                      child: WebEmbeddedPanel(
                        height: 460,
                        child: WebCodecToolsView(),
                      ),
                    ),
                    const SizedBox(height: 22),
                    WebToolPanel(
                      icon: Icons.manage_search_outlined,
                      title: WebSourceInspectorInlineView.title,
                      subtitle: '解析 href / src / srcset / url()，找出缺失与外部引用',
                      child: WebSourceInspectorInlineView(store: store),
                    ),
                    const SizedBox(height: 22),
                    const WebToolPanel(
                      icon: Icons.palette_outlined,
                      title: WebCssToolsInlineView.title,
                      subtitle: '颜色换算与 WCAG 对比度、盒模型、选择器优先级',
                      child: WebCssToolsInlineView(),
                    ),
                    const SizedBox(height: 22),
                    const WebToolPanel(
                      icon: Icons.fact_check_outlined,
                      title: WebMarkupCheckInlineView.title,
                      subtitle: '标签配对、可访问性要点与逐标签重排',
                      child: WebMarkupCheckInlineView(),
                    ),
                    const SizedBox(height: 26),
                    const ToolsSectionHeading(
                      icon: Icons.build_outlined,
                      title: '通用工具',
                      subtitle: '内核提供的离线工具，不涉及网络',
                    ),
                    const SizedBox(height: 4),
                  ],
                ),
              ),
            ),
            SliverPadding(
              padding: EdgeInsets.fromLTRB(horizontal, 8, horizontal, 8),
              sliver: ToolsGridSliver(tools: commonTools),
            ),
            SliverPadding(
              padding: EdgeInsets.fromLTRB(horizontal, 12, horizontal, 32),
              sliver: SliverToBoxAdapter(
                child: Text(
                  '以上工具均在本机计算，不上传任何内容；只有 127.0.0.1 回环预览会监听端口。',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}

class _OfflineBanner extends StatelessWidget {
  const _OfflineBanner();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Icon(
            Icons.offline_bolt_outlined,
            size: 18,
            color: theme.colorScheme.primary,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              '离线模式：只做本机解析与本机预览，不访问任何外部服务。',
              style: theme.textTheme.bodySmall,
            ),
          ),
        ],
      ),
    );
  }
}
