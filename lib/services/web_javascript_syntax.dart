/// Result from a genuine JavaScript syntax parser. Offsets are UTF-16 units.
class WebJavaScriptSyntaxResult {
  const WebJavaScriptSyntaxResult({
    this.startOffset,
    this.endOffset,
    this.message,
    this.unavailableReason,
  });

  final int? startOffset;
  final int? endOffset;
  final String? message;
  final String? unavailableReason;
}
