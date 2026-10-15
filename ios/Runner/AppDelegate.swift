import Flutter
import SafariServices
import UIKit

@main
@objc class AppDelegate: FlutterAppDelegate, FlutterImplicitEngineDelegate {
  private var nginxBridge: EmbeddedNginxBridge?
  override func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
  ) -> Bool {
    return super.application(application, didFinishLaunchingWithOptions: launchOptions)
  }

  func didInitializeImplicitFlutterEngine(_ engineBridge: FlutterImplicitEngineBridge) {
    GeneratedPluginRegistrant.register(with: engineBridge.pluginRegistry)
    guard let registrar = engineBridge.pluginRegistry.registrar(forPlugin: "WebForgePlatform") else {
      return
    }
    nginxBridge = EmbeddedNginxBridge(messenger: registrar.messenger())
    let channel = FlutterMethodChannel(
      name: "qflistudio/platform", binaryMessenger: registrar.messenger())
    channel.setMethodCallHandler { call, result in
      guard call.method == "openUrl" else {
        result(FlutterMethodNotImplemented)
        return
      }
      guard let arguments = call.arguments as? [String: Any],
        let value = arguments["url"] as? String,
        let url = URL(string: value),
        ["http", "https"].contains(url.scheme?.lowercased() ?? ""),
        let host = url.host, !host.isEmpty
      else {
        result(FlutterError(code: "INVALID_URL", message: "Invalid HTTP(S) URL", details: nil))
        return
      }
      let scenes = UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }
      guard var presenter = scenes.flatMap({ $0.windows })
        .first(where: { $0.isKeyWindow })?.rootViewController
      else {
        result(FlutterError(code: "NO_WINDOW", message: "No active preview window", details: nil))
        return
      }
      while let presented = presenter.presentedViewController {
        presenter = presented
      }
      // Keep the app's local server running while its preview is visible.
      presenter.present(SFSafariViewController(url: url), animated: true) {
        result(nil)
      }
    }
  }
}
