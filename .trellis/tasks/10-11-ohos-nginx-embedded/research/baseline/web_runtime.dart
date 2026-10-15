import 'dart:io';

import 'package:flutter/services.dart';
import 'package:path/path.dart' as p;

import 'nginx_session.dart';
import 'nginx_host.dart';
import 'web_dev_server.dart';
import 'web_project_config.dart';
import 'web_runtime_session.dart';

abstract final class WebRuntime {
  static Future<String?> nginxExecutable() async {
    if (Platform.isAndroid || Platform.operatingSystem == 'ohos') {
      try {
        final path = await const MethodChannel(
          'qflistudio/platform',
        ).invokeMethod<String>('nginxPath');
        if (path != null && await File(path).exists()) return path;
      } on MissingPluginException {
        return null;
      }
      return null;
    }
    if (Platform.isWindows || Platform.isLinux || Platform.isMacOS) {
      final executableName = Platform.isWindows ? 'nginx.exe' : 'nginx';
      final executableDirectory = p.dirname(Platform.resolvedExecutable);
      for (final path in [
        if (Platform.isMacOS)
          p.normalize(p.join(executableDirectory, '..', 'Helpers', 'nginx'))
        else
          p.join(executableDirectory, 'data', 'nginx', executableName),
        p.join(
          Directory.current.path,
          'assets',
          'runtime',
          'nginx',
          Platform.operatingSystem,
          executableName,
        ),
      ]) {
        if (await File(path).exists()) return path;
      }
    }
    return null;
  }

  static Future<WebRuntimeSession> start(String projectPath) async {
    final config = await WebProjectConfig.load(projectPath);
    if (config.engine != WebServerEngine.webforge) {
      if (Platform.isIOS) {
        return NginxSession.startWithHost(
          projectPath,
          host: const EmbeddedNginxHost(),
          configuration: config,
        );
      }
      final executable = await nginxExecutable();
      if (executable != null) {
        try {
          return await NginxSession.start(
            projectPath,
            executable: executable,
            configuration: config,
          );
        } on ProcessException catch (error) {
          // HarmonyOS can forbid exec even for a packaged native binary.
          if (config.engine != WebServerEngine.auto ||
              Platform.operatingSystem != 'ohos' ||
              error.errorCode != 13) {
            rethrow;
          }
          return WebDevServer.start(projectPath, configuration: config);
        }
      }
      if (config.engine == WebServerEngine.nginx) {
        throw StateError('当前设备没有可用的 Nginx 运行文件');
      }
    }
    return WebDevServer.start(projectPath, configuration: config);
  }
}
