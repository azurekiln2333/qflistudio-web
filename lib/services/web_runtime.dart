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
    if (Platform.isAndroid) {
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
      // iOS and HarmonyOS run the embedded single-process engine in-app; it is
      // delivered as a shared library and never relies on exec permission.
      if (Platform.isIOS || Platform.operatingSystem == 'ohos') {
        // `auto` degrades to the Dart middleware when the embedded library is
        // not packaged or its channel is absent. An explicit `nginx` request
        // never silently substitutes another engine.
        if (config.engine == WebServerEngine.auto &&
            !await _embeddedNginxAvailable()) {
          return WebDevServer.start(projectPath, configuration: config);
        }
        return NginxSession.startWithHost(
          projectPath,
          host: const EmbeddedNginxHost(),
          configuration: config,
        );
      }
      final executable = await nginxExecutable();
      if (executable != null) {
        return NginxSession.start(
          projectPath,
          executable: executable,
          configuration: config,
        );
      }
      if (config.engine == WebServerEngine.nginx) {
        throw StateError('当前设备没有可用的 Nginx 运行文件');
      }
    }
    return WebDevServer.start(projectPath, configuration: config);
  }

  /// Reports whether the embedded lifecycle channel answers with a real version.
  /// A missing plugin or a malformed value means the shared library is absent.
  static Future<bool> _embeddedNginxAvailable() async {
    try {
      await const EmbeddedNginxHost().version();
      return true;
    } on MissingPluginException {
      return false;
    } on StateError {
      return false;
    } on PlatformException {
      return false;
    }
  }
}
