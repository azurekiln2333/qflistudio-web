import 'dart:convert';
import 'dart:ffi';
import 'dart:io';

import 'package:ffi/ffi.dart';
import 'package:path/path.dart' as p;

import 'web_javascript_syntax.dart';

typedef _CheckNative =
    Int32 Function(
      Pointer<Utf8>,
      Size,
      Int32,
      Pointer<Int32>,
      Pointer<Int32>,
      Pointer<Utf8>,
      Size,
    );
typedef _CheckDart =
    int Function(
      Pointer<Utf8>,
      int,
      int,
      Pointer<Int32>,
      Pointer<Int32>,
      Pointer<Utf8>,
      int,
    );

_CheckDart _open(String? explicitPath) {
  if (explicitPath != null) {
    return DynamicLibrary.open(
      explicitPath,
    ).lookupFunction<_CheckNative, _CheckDart>('qfli_web_syntax_check');
  }
  if (Platform.isIOS) {
    return DynamicLibrary.process().lookupFunction<_CheckNative, _CheckDart>(
      'qfli_web_syntax_check',
    );
  }
  final executableDirectory = p.dirname(Platform.resolvedExecutable);
  final names = Platform.isWindows
      ? [
          p.join(executableDirectory, 'qfli_web_syntax.dll'),
          'qfli_web_syntax.dll',
        ]
      : Platform.isMacOS
      ? [
          p.normalize(
            p.join(
              executableDirectory,
              '..',
              'Frameworks',
              'libqfli_web_syntax.dylib',
            ),
          ),
          'libqfli_web_syntax.dylib',
        ]
      : Platform.isLinux
      ? [
          p.join(executableDirectory, 'lib', 'libqfli_web_syntax.so'),
          'libqfli_web_syntax.so',
        ]
      // Android/OHOS resolve packaged libraries through their native linker
      // namespace; the executable's directory is not the app library root.
      : ['libqfli_web_syntax.so'];
  for (final name in names) {
    try {
      return DynamicLibrary.open(
        name,
      ).lookupFunction<_CheckNative, _CheckDart>('qfli_web_syntax_check');
    } on ArgumentError {
      // Try the next installed-library location before reporting unavailable.
    }
  }
  return DynamicLibrary.process().lookupFunction<_CheckNative, _CheckDart>(
    'qfli_web_syntax_check',
  );
}

WebJavaScriptSyntaxResult checkJavaScriptSyntax(
  String source, {
  required bool module,
  String? nativeLibraryPath,
}) {
  late final _CheckDart check;
  try {
    check = _open(nativeLibraryPath);
  } on ArgumentError {
    return const WebJavaScriptSyntaxResult(
      unavailableReason: '当前安装包未提供 QuickJS 离线 JavaScript 语法后端',
    );
  }
  final length = utf8.encode(source).length;
  if (length > 512 * 1024) {
    return const WebJavaScriptSyntaxResult(
      unavailableReason: 'JavaScript 源码超过 512 KiB 语法分析限制',
    );
  }
  return using((arena) {
    final input = source.toNativeUtf8(allocator: arena);
    final start = arena<Int32>();
    final end = arena<Int32>();
    const capacity = 2048;
    final output = arena<Uint8>(capacity).cast<Utf8>();
    final status = check(
      input,
      length,
      module ? 1 : 0,
      start,
      end,
      output,
      capacity,
    );
    if (status == 0) return const WebJavaScriptSyntaxResult();
    final description = output.toDartString();
    if (status != 1 ||
        start.value < 0 ||
        end.value < start.value ||
        end.value > source.length) {
      return WebJavaScriptSyntaxResult(
        unavailableReason: 'QuickJS 无法完成语法分析：$description',
      );
    }
    return WebJavaScriptSyntaxResult(
      startOffset: start.value,
      endOffset: end.value,
      message: description,
    );
  });
}
