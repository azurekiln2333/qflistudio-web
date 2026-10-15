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

Nginx is the retained upstream 1.31.6 engine. Desktop uses a process host;
iOS and HarmonyOS use the in-process embedded lifecycle ABI
(`qfli_nginx_version/start/poll/stop/release`). Build, packaging and per-platform
evidence live under `vendor/nginx/` (`README.md`, `VALIDATION.md`,
`SOURCE.json`, `HASHES.sha256`) and `scripts/`. On HarmonyOS the engine ships as
the NAPI shared library `libqfli_nginx_napi.so`; `module.executableBinaryPaths`
makes `bm install` fail and must not be reintroduced.

See `.trellis/spec/backend/web-runtime.md` and
`.trellis/spec/backend/native-runtime.md` for the full contracts.
