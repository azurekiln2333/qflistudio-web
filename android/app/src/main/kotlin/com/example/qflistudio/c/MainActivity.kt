package com.azurekiln.qfli.webforge

import android.content.ActivityNotFoundException
import android.content.Intent
import android.net.Uri
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "qflistudio/platform")
            .setMethodCallHandler { call, result ->
                if (call.method != "openUrl") {
                    result.notImplemented()
                    return@setMethodCallHandler
                }
                val url = call.argument<String>("url")
                val uri = url?.let(Uri::parse)
                if (uri == null || (uri.scheme != "http" && uri.scheme != "https") || uri.host.isNullOrEmpty()) {
                    result.error("INVALID_URL", "Invalid HTTP(S) URL", null)
                    return@setMethodCallHandler
                }
                try {
                    startActivity(Intent(Intent.ACTION_VIEW, uri))
                    result.success(null)
                } catch (error: ActivityNotFoundException) {
                    result.error("NO_BROWSER", "No browser can open this URL", null)
                }
            }
    }
}
