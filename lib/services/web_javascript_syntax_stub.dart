import 'web_javascript_syntax.dart';

WebJavaScriptSyntaxResult checkJavaScriptSyntax(
  String source, {
  required bool module,
  String? nativeLibraryPath,
}) => const WebJavaScriptSyntaxResult(
  unavailableReason: '当前平台未提供 QuickJS 离线 JavaScript 语法后端',
);
