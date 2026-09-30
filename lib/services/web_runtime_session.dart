import 'package:qfli_studio_core/services/studio_profile.dart';

class WebRequestEvent {
  const WebRequestEvent(this.method, this.path, this.status, this.elapsed);

  final String method;
  final String path;
  final int status;
  final Duration elapsed;

  @override
  String toString() => '$method $path  $status  ${elapsed.inMilliseconds} ms';
}

abstract interface class WebRuntimeSession implements WebPreviewSession {
  String get engineName;
  Stream<WebRequestEvent> get requests;
}
