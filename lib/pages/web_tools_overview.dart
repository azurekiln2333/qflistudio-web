import 'package:flutter/material.dart';
import 'package:qfli_studio_core/pages/tools_grid.dart';
import 'package:qfli_studio_core/store/project_store.dart';

import 'web_tools_page.dart';

/// WebForge 的整合工具页，直接嵌入内核的工具 tab。
///
/// 通过 [StudioProfile.toolsTabBuilder] 接线（见 `lib/main.dart`）：内核
/// `FunctionsTab` 会在自己的 Scaffold 里渲染这个 body，于是工具入口只剩一个，
/// 不再需要 push 一个重复的「Web 工具」页面。产品只贡献自己的卡片，通用离线
/// 工具与终端入口仍由内核的 [ToolsGrid] 提供。
///
/// 这里只展示本机离线能力：本地服务预览与编解码。HTTP 工具和外部代理属于联网
/// 入口，由 [WebToolsPage] 按 `offlineOnly` 裁掉，此概览也不暴露它们。
class WebToolsOverview extends StatelessWidget {
  const WebToolsOverview({super.key, required this.store, this.onOpenTerminal});

  final ProjectStore store;

  /// 内核已有的全屏终端路由；终端卡片复用而不是自己重建一个。
  final VoidCallback? onOpenTerminal;

  @override
  Widget build(BuildContext context) {
    return ToolsGrid(
      onOpenTerminal: onOpenTerminal,
      sections: [
        ToolSection(
          title: '本地预览',
          icon: Icons.language,
          tools: [
            ToolDefinition(
              icon: Icons.dns_outlined,
              title: '本地服务',
              description: '启动 127.0.0.1 预览，查看请求与控制台',
              onTap: () =>
                  _open(context, '本地服务', WebServerToolsView(store: store)),
            ),
          ],
        ),
        const ToolSection(
          title: '编解码',
          icon: Icons.swap_horiz,
          tools: [
            ToolDefinition(
              icon: Icons.data_object,
              title: 'Web 编解码',
              description: 'JSON / URL / Base64 互转，纯本机计算',
              builder: _buildCodec,
            ),
          ],
        ),
      ],
    );
  }

  static Widget _buildCodec(BuildContext context) {
    return const Scaffold(body: SafeArea(child: WebCodecToolsView()));
  }

  void _open(BuildContext context, String title, Widget body) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => Scaffold(
          appBar: AppBar(title: Text(title)),
          body: body,
        ),
      ),
    );
  }
}
