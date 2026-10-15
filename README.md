# qfli_web

This Flutter app is an independent Git repository. Check out `qfli_studio_core` next to it before resolving dependencies.

```text
checkout-parent/
  qfli_studio_core/
  qfli_web/
```

Run `flutter pub get` here, then `flutter run` for the target device. The shared editor patch is provided by `../qfli_studio_core/vendor/re_editor`.

## Local web runtime

The product is QFLIWebForge: a local static preview server for HTML/CSS/JS
projects, with console capture, request diagnostics, live reload, API proxying
and SPA fallback. `.qfli/web.json` selects `engine: "auto" | "nginx" |
"webforge"`.

Nginx is the retained upstream 1.31.6 engine. Android and desktop use a process host;
iOS and HarmonyOS use the in-process embedded lifecycle ABI
(`qfli_nginx_version/start/poll/stop/release`). Build, packaging and per-platform
evidence live under `vendor/nginx/` (`README.md`, `VALIDATION.md`,
`SOURCE.json`, `HASHES.sha256`) and `scripts/`. On HarmonyOS the engine ships as
the NAPI shared library `libqfli_nginx_napi.so`; `module.executableBinaryPaths`
makes `bm install` fail and must not be reintroduced.

See `.trellis/spec/backend/web-runtime.md` and
`.trellis/spec/backend/native-runtime.md` for the full contracts.

The offline product hides HTTP-client/proxy configuration, account login,
cloud and Git network entries. Local loopback preview remains available. The
shared shell retains five pages; Web tools are integrated by the product's
`toolsTabBuilder`.

## Offline curriculum verification

WebForge owns 301 tutorials and 301 standalone HTML examples: HTML100, CSS100
and JavaScript101. `language` identifies the subject; `type: html` ensures that
imports receive a previewable `.html` filename. The sibling core catalog is
unchanged.

```text
python -X utf8 scripts/emit_content.py
python -X utf8 scripts/audit_web_content.py --product
npm ci
npx playwright install chromium
npm run verify:content
flutter analyze --no-pub lib test integration_test tool
flutter test --no-pub --concurrency=1
```

Browser verification checks every example with a concrete oracle, isolated
storage and strict resource validation. The only intentional missing resource
is lesson006's image demonstrating alt-text fallback.

## Mobile release validation

Use `flutter build apk --release` and `flutter build hap --release` with the
OHOS-capable Flutter SDK. Keep pub enabled when switching from integration/debug
to release so the plugin registry is regenerated correctly.

The Android release configuration currently uses the debug key and produces a
validation APK. OHOS builds unsigned until a local signing profile matching
`com.azurekiln.qfli.webforge` is configured; the Flutter wrapper may report a
missing signature after Hvigor successfully writes the unsigned release HAP.
Neither artifact has store distribution signing. Exact checks and current
device limits are recorded in `.trellis/tasks/10-15-webforge-store-readiness/`.
