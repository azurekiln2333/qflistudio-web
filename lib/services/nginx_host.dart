import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/services.dart';
import 'package:path/path.dart' as p;

abstract interface class NginxHost {
  Future<String> version();
  Future<void> validate(Directory prefix);
  Future<NginxInstance> start(Directory prefix);
}

abstract interface class NginxInstance {
  List<Stream<List<int>>> get output;
  Future<int> get exitCode;
  Future<void> stop();
}

class ProcessNginxHost implements NginxHost {
  const ProcessNginxHost(this.executable);
  final String executable;

  @override
  Future<String> version() async {
    final info = await _command(['-v']);
    final version = RegExp(
      r'nginx/(\d+\.\d+\.\d+)',
    ).firstMatch('${info.stderr}')?.group(1);
    if (info.exitCode != 0 || version == null) {
      throw StateError('无法确认 Nginx 运行文件：${info.stderr}');
    }
    return version;
  }

  List<String> _arguments(Directory prefix) => [
    '-p',
    '${prefix.path}${p.separator}',
    '-c',
    'nginx.conf',
  ];

  @override
  Future<void> validate(Directory prefix) async {
    final check = await _command([
      ..._arguments(prefix),
      '-t',
    ], workingDirectory: prefix.path);
    if (check.exitCode != 0) {
      throw StateError('Nginx 配置检查失败：${check.stderr}');
    }
  }

  @override
  Future<NginxInstance> start(Directory prefix) async => _ProcessInstance(
    await Process.start(
      executable,
      _arguments(prefix),
      workingDirectory: prefix.path,
    ),
    () => _command(
      [..._arguments(prefix), '-s', 'stop'],
      workingDirectory: prefix.path,
      timeout: const Duration(seconds: 3),
    ),
  );

  Future<ProcessResult> _command(
    List<String> arguments, {
    String? workingDirectory,
    Duration timeout = const Duration(seconds: 5),
  }) async {
    final process = await Process.start(
      executable,
      arguments,
      workingDirectory: workingDirectory,
    );
    final output = Future.wait<Object>([
      process.exitCode,
      process.stdout.transform(const Utf8Decoder(allowMalformed: true)).join(),
      process.stderr.transform(const Utf8Decoder(allowMalformed: true)).join(),
    ]);
    try {
      final result = await output.timeout(timeout);
      return ProcessResult(process.pid, result[0] as int, result[1], result[2]);
    } catch (_) {
      process.kill(ProcessSignal.sigkill);
      await output;
      rethrow;
    }
  }
}

class _ProcessInstance implements NginxInstance {
  _ProcessInstance(this.process, this.signal) {
    unawaited(process.exitCode.then((_) => exited = true));
  }
  final Process process;
  final Future<ProcessResult> Function() signal;
  bool exited = false;
  Future<void>? stopping;
  @override
  List<Stream<List<int>>> get output => [process.stdout, process.stderr];
  @override
  Future<int> get exitCode => process.exitCode;
  @override
  Future<void> stop() => stopping ??= _stop();

  Future<void> _stop() async {
    try {
      if (!exited) await signal();
      await exitCode.timeout(const Duration(seconds: 3));
    } catch (_) {
      process.kill(ProcessSignal.sigkill);
      await exitCode;
    }
  }
}

class EmbeddedNginxHost implements NginxHost {
  const EmbeddedNginxHost();
  static const channel = MethodChannel('qflistudio/nginx');

  @override
  Future<String> version() async {
    final value = await channel.invokeMethod<String>('version');
    if (value == null || !RegExp(r'^\d+\.\d+\.\d+$').hasMatch(value)) {
      throw StateError('无法确认原生 Nginx 版本');
    }
    return value;
  }

  @override
  Future<void> validate(Directory prefix) async {
    final instance = await _start(prefix, true);
    int code;
    try {
      code = await instance.exitCode.timeout(const Duration(seconds: 5));
    } catch (_) {
      await instance.stop();
      rethrow;
    }
    if (code != 0) {
      final diagnostics = await _diagnostics(prefix);
      throw StateError('Nginx 配置检查失败：$diagnostics');
    }
  }

  @override
  Future<NginxInstance> start(Directory prefix) => _start(prefix, false);

  Future<_EmbeddedInstance> _start(Directory prefix, bool test) async {
    final token = await channel.invokeMethod<int>('start', {
      'prefix': prefix.path,
      'test': test,
    });
    if (token == null || token <= 0) throw StateError('原生 Nginx 启动失败');
    return _EmbeddedInstance(token);
  }

  static Future<String> _diagnostics(Directory prefix) async {
    final file = File(p.join(prefix.path, 'error.log'));
    if (!await file.exists()) return '原生引擎退出';
    final handle = await file.open();
    try {
      final length = await handle.length();
      await handle.setPosition((length - 16384).clamp(0, length));
      return utf8.decode(await handle.read(16384), allowMalformed: true);
    } finally {
      await handle.close();
    }
  }
}

class _EmbeddedInstance implements NginxInstance {
  _EmbeddedInstance(this.token) {
    exitCode = _waitForExit();
    // The session subscribes immediately; avoid an uncaught error before wiring it.
    unawaited(
      exitCode.then<void>((_) {}, onError: (Object _, StackTrace _) {}),
    );
  }
  final int token;
  @override
  late final Future<int> exitCode;
  @override
  List<Stream<List<int>>> get output => const [];
  Future<void>? stopping;

  Future<int> _waitForExit() async {
    while (true) {
      final code = await EmbeddedNginxHost.channel.invokeMethod<int>('poll', {
        'token': token,
      });
      if (code != null) {
        await EmbeddedNginxHost.channel.invokeMethod<void>('release', {
          'token': token,
        });
        return code;
      }
      await Future<void>.delayed(const Duration(milliseconds: 50));
    }
  }

  @override
  Future<void> stop() => stopping ??= _stop();

  Future<void> _stop() async {
    await EmbeddedNginxHost.channel.invokeMethod<void>('stop', {
      'token': token,
    });
    // Prefix and middleware remain owned until native cleanup actually finishes.
    try {
      await exitCode;
    } catch (_) {
      await _waitForExit();
    }
  }
}
