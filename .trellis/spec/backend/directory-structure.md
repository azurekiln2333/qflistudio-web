# Directory Structure

> How `qfli_web` code is organized. This is a Flutter/Dart product repository,
> not a server application: "backend" here means Dart services, the web runtime
> and the native build/packaging layer.

---

## Repository Layout

```
qfli_web/
├── lib/
│   ├── main.dart                 # Product profile + app bootstrap
│   ├── pages/                    # Tools tab body and reusable Web views
│   ├── content/                  # Product-owned offline curriculum adapter
│   └── services/                 # Web runtime, serving, Nginx, project config
├── test/                         # Flutter widget/unit tests (one per service)
├── integration_test/             # On-device content imports and native smoke
├── tool/nginx_smoke.dart         # Runnable native-engine smoke entry point
├── scripts/                      # Native builds, curriculum source and browser checks
├── native/nginx/embedded/        # Embedded engine C ABI + addon config
├── vendor/nginx/                 # Retained upstream source, patches, licenses
├── android/ ios/ macos/ linux/ windows/ ohos/   # Platform runners
├── assets/                       # App icon, licenses and product content JSON
└── web/                          # Flutter web shell (not a served project)
```

`lib/services/` is the runtime layer:

| File | Responsibility |
|------|----------------|
| `web_runtime.dart` | Engine selection entry point (`WebRuntime.start`) |
| `web_runtime_session.dart` | `WebRuntimeSession` interface + request events |
| `web_dev_server.dart` | In-process Dart middleware (static, SPA, proxy, SSE, debug bridge) |
| `nginx_session.dart` | Native engine owner (public listener + private middleware) |
| `nginx_host.dart` | Process vs embedded lifecycle hosts (`ProcessNginxHost`, `EmbeddedNginxHost`) |
| `web_project_config.dart` | `.qfli/web.json` load/parse/validate |

## Where New Code Goes

- A new preview/serving capability → `lib/services/`, behind
  `WebRuntimeSession`. Do not add serving logic to `lib/pages/`.
- A new product screen → `lib/pages/`, following `web_tools_page.dart`.
- Package/bridge-level native work → `native/`, `scripts/` and the owning
  platform runner directory.
- The shared editor, project store and navigation live in the sibling
  `qfli_studio_core` package (imported as `package:qfli_studio_core/...`).
  Platform hooks are injected through `StudioProfile` (`lib/main.dart`
  `webProfile`); do not fork shared widgets into this repo.

## Naming Conventions

- Files and directories: `lower_snake_case.dart`.
- Services: one class per file matching the file name
  (`WebDevServer` in `web_dev_server.dart`, `WebProjectConfig` in
  `web_project_config.dart`).
- Tests mirror the source name: `web_dev_server.dart` →
  `test/web_dev_server_test.dart`.
- Shell scripts: `build_nginx_<target>.sh` / `bundle_nginx_<target>.sh`.

## Examples

- Multi-platform engine wiring: `lib/services/web_runtime.dart`
  (`nginxExecutable()` then `WebRuntime.start`).
- Runtime session contract exercised end to end: `test/web_dev_server_test.dart`,
  `test/nginx_session_test.dart`.
- Native build + packaging conventions: `scripts/build_nginx_desktop.sh`,
  `scripts/bundle_nginx_macos.sh`.
