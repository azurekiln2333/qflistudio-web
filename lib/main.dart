import 'dart:async';

import 'package:flutter/material.dart';

import 'package:qfli_studio_core/app.dart';
import 'package:qfli_studio_core/services/project_templates.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/splash_screen.dart';
import 'package:qfli_studio_core/store/auth_store.dart';
import 'package:qfli_studio_core/store/project_store.dart';
import 'package:qfli_studio_core/store/settings_store.dart';

import 'content/webforge_content_repository.dart';
import 'pages/web_tools_overview.dart';
import 'pages/web_tools_page.dart';
import 'services/web_code_analyzer.dart';
import 'services/web_runtime.dart';

/// 本 App 的产品名。窗口标题、任务切换器和应用内顶栏都读它。
const String _appTitle = StudioProductCatalog.webForge;

/// Web 版档位：同一套内核 UI，收窄成只服务 Web。
///
/// 单独提出来是为了让测试能直接断言档位，而不必为了一个常量去跑 `main()`。
const StudioProfile webProfile = StudioProfile(
  id: 'web',
  appTitle: _appTitle,
  templates: [ProjectTemplate.empty, ProjectTemplate.html],
  isOffline: true,
  productKey: StudioProductCatalog.webForgeKey,
  showHomeTabs: false,
  runtimeKind: 'html-css-javascript-preview',
  runtimeStatus: 'available',
  supportedFileExtensions: ['.html', '.css', '.js'],
  webPreviewFactory: WebRuntime.start,
  codeAnalyzer: WebCodeAnalyzer(),
  toolsPageBuilder: _buildWebTools,
  toolsTabBuilder: _buildWebToolsTab,
  // 教程/示例读 WebForge 自己的离线课程，而不是共享聚合内容。
  contentRepositoryFactory: WebForgeContentRepository.new,
  entryFileNames: ['index.html', 'src/index.html'],
);

/// 该页面仍被内核的「内容工具」与编辑器当前文件菜单复用，因此保留。
Widget _buildWebTools(ProjectStore store) => WebToolsPage(store: store);

/// 工具 tab 的整合 body。设置后内核不再渲染单独的「Web 工具」入口卡片，
/// 工具入口只剩这一个，避免首页与工具页割裂。
Widget _buildWebToolsTab(ProjectStore store, VoidCallback onOpenTerminal) =>
    WebToolsOverview(store: store, onOpenTerminal: onOpenTerminal);

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // 在 runApp 之前定档。
  StudioProfile.current = webProfile;

  final store = ProjectStore();
  final auth = AuthStore();
  final settings = SettingsStore();
  final ready = ValueNotifier<bool>(false);
  // 先 runApp 品牌启动页（与原生遮罩同色，无白屏），数据后台并行加载。
  runApp(QfliApp(store: store, auth: auth, settings: settings, ready: ready));
  // 首帧提交后再做磁盘/插件初始化，避免与首帧构建争用主 isolate。
  WidgetsBinding.instance.addPostFrameCallback((_) {
    unawaited(
      AppBootstrap.run(
        store: store,
        auth: auth,
        settings: settings,
        ready: ready,
      ),
    );
  });
}
