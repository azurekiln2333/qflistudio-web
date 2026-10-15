import Flutter
import UIKit

final class EmbeddedNginxBridge {
  private let channel: FlutterMethodChannel
  private var activeToken: Int64?
  private var terminationObserver: NSObjectProtocol?

  init(messenger: FlutterBinaryMessenger) {
    channel = FlutterMethodChannel(name: "qflistudio/nginx", binaryMessenger: messenger)
    channel.setMethodCallHandler { [weak self] call, result in
      self?.handle(call, result: result)
    }
    terminationObserver = NotificationCenter.default.addObserver(
      forName: UIApplication.willTerminateNotification, object: nil, queue: .main
    ) { [weak self] _ in
      if let token = self?.activeToken { _ = qfli_nginx_stop(token) }
    }
  }

  deinit {
    if let observer = terminationObserver { NotificationCenter.default.removeObserver(observer) }
    if let token = activeToken {
      _ = qfli_nginx_stop(token)
      // Engine replacement can dispose the channel before Dart releases its token.
      DispatchQueue.global(qos: .utility).async {
        var code: Int32 = 0
        for _ in 0..<200 {
          let state = qfli_nginx_poll(token, &code)
          if state == 1 { _ = qfli_nginx_release(token); return }
          if state < 0 { return }
          Thread.sleep(forTimeInterval: 0.05)
        }
      }
    }
  }

  private func handle(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
    if call.method == "version" {
      result(String(cString: qfli_nginx_version()))
      return
    }
    let arguments = call.arguments as? [String: Any]
    if call.method == "start" {
      guard let prefix = arguments?["prefix"] as? String,
        let test = arguments?["test"] as? Bool, !prefix.utf8.contains(0)
      else {
        result(FlutterError(code: "INVALID_ARGUMENT", message: "Invalid Nginx start arguments", details: nil))
        return
      }
      let token = prefix.withCString { qfli_nginx_start($0, test ? 1 : 0) }
      if token < 0 {
        result(FlutterError(code: "NGINX_START", message: "Native Nginx start failed", details: token))
      } else {
        activeToken = token
        result(token)
      }
      return
    }
    guard ["poll", "stop", "release"].contains(call.method) else {
      result(FlutterMethodNotImplemented)
      return
    }
    guard let token = (arguments?["token"] as? NSNumber)?.int64Value, token > 0 else {
      result(FlutterError(code: "INVALID_ARGUMENT", message: "Invalid Nginx token", details: nil))
      return
    }
    var status: Int32
    if call.method == "poll" {
      var exitCode: Int32 = 0
      status = qfli_nginx_poll(token, &exitCode)
      if status >= 0 { result(status == 0 ? nil : exitCode); return }
    } else if call.method == "stop" {
      status = qfli_nginx_stop(token)
    } else {
      status = qfli_nginx_release(token)
      if status == 0 && activeToken == token { activeToken = nil }
    }
    if status < 0 {
      result(FlutterError(code: "NGINX_SESSION", message: "Native Nginx lifecycle failed", details: status))
    } else {
      result(nil)
    }
  }
}
