import 'dart:convert';
import 'dart:io';

import 'package:path/path.dart' as p;

class WebProxyRule {
  const WebProxyRule({required this.prefix, required this.target});

  final String prefix;
  final Uri target;

  bool matches(String path) => path == prefix || path.startsWith('$prefix/');
}

class WebProjectConfig {
  const WebProjectConfig({
    required this.root,
    required this.port,
    required this.spaFallback,
    required this.proxies,
  });

  final String root;
  final int port;
  final bool spaFallback;
  final List<WebProxyRule> proxies;

  static Future<WebProjectConfig> load(String projectPath) async {
    final file = File(p.join(projectPath, '.qfli', 'web.json'));
    final Map<String, dynamic> data;
    if (await file.exists()) {
      final decoded = jsonDecode(await file.readAsString());
      if (decoded is! Map<String, dynamic>) {
        throw const FormatException('Web 配置必须是 JSON 对象');
      }
      data = decoded;
    } else {
      data = const {};
    }
    return parse(projectPath, data);
  }

  static WebProjectConfig parse(String projectPath, Map<String, dynamic> data) {
    final project = Directory(projectPath);
    if (!project.existsSync()) {
      throw FileSystemException('项目目录不存在', projectPath);
    }
    final rootSetting = data['root'];
    if (rootSetting != null && rootSetting is! String) {
      throw const FormatException('root 必须是相对目录');
    }
    final relativeRoot =
        rootSetting as String? ??
        (File(p.join(projectPath, 'index.html')).existsSync()
            ? '.'
            : File(p.join(projectPath, 'src', 'index.html')).existsSync()
            ? 'src'
            : '.');
    if (p.isAbsolute(relativeRoot) ||
        p.split(relativeRoot).contains('..') ||
        relativeRoot.contains('\\')) {
      throw const FormatException('root 必须位于项目目录内');
    }
    final canonicalProject = project.resolveSymbolicLinksSync();
    final root = Directory(p.join(projectPath, relativeRoot));
    if (!root.existsSync()) {
      throw FileSystemException('Web 根目录不存在', root.path);
    }
    final canonicalRoot = root.resolveSymbolicLinksSync();
    if (canonicalRoot != canonicalProject &&
        !p.isWithin(canonicalProject, canonicalRoot)) {
      throw const FormatException('Web 根目录不能指向项目外');
    }

    final port = data['port'] ?? 0;
    if (port is! int || port < 0 || port > 65535) {
      throw const FormatException('port 必须是 0 到 65535 的整数');
    }
    final spaFallback = data['spaFallback'] ?? false;
    if (spaFallback is! bool) {
      throw const FormatException('spaFallback 必须是布尔值');
    }
    final rawProxies = data['proxies'] ?? const [];
    if (rawProxies is! List) {
      throw const FormatException('proxies 必须是数组');
    }
    final proxies = <WebProxyRule>[];
    for (final item in rawProxies) {
      if (item is! Map<String, dynamic>) {
        throw const FormatException('代理规则必须是对象');
      }
      final prefix = item['prefix'];
      final targetText = item['target'];
      if (prefix is! String ||
          !prefix.startsWith('/') ||
          prefix == '/' ||
          prefix.endsWith('/') ||
          prefix.contains('?') ||
          prefix.contains('#') ||
          targetText is! String) {
        throw const FormatException('代理规则需要有效的 prefix 和 target');
      }
      final target = Uri.tryParse(targetText);
      if (target == null ||
          (target.scheme != 'http' && target.scheme != 'https') ||
          target.host.isEmpty ||
          target.hasQuery ||
          target.hasFragment ||
          target.userInfo.isNotEmpty) {
        throw const FormatException('代理 target 必须是 HTTP(S) 地址');
      }
      proxies.add(WebProxyRule(prefix: prefix, target: target));
    }
    proxies.sort((a, b) => b.prefix.length.compareTo(a.prefix.length));
    return WebProjectConfig(
      root: canonicalRoot,
      port: port,
      spaFallback: spaFallback,
      proxies: List.unmodifiable(proxies),
    );
  }
}
