# Design

## Current behavior

The shared editor starts `LocalWebServer` and then asks `RunnerService` to run the same HTML file. `RunnerService` starts a second listener. The template writes `src/index.html`, `src/style.css`, and `src/main.js`, while the existing server falls back to HTML for missing asset paths. The product repository currently has no Web-specific tools UI.

## Ownership

- `qfli_web`: Web development server, project configuration, diagnostics, web tools, and product-specific tests.
- `qfli_studio_core`: minimal editor and navigation hooks required to use WebForge's server and tools. Shared behavior must remain unchanged for other products.

## Server contract

Bind loopback on a dynamic port by default. Choose the content root from an explicit project setting or an existing `index.html` at the root or in `src/`. Resolve requested files against that root, reject escapes and symlink targets outside it, and return 404 for missing assets. HTML responses may inject a localhost-only diagnostics and reload bridge. Configuration is project-local JSON under `.qfli/`; malformed settings report a specific error instead of silently falling back.

Proxy rules match path prefixes and forward to an explicit upstream URL. The proxy must preserve request methods, query strings, response status and headers, and stream bodies with bounded resource use. Avoid forwarding hop-by-hop headers. Provide a local request log and explicit stop/dispose behavior.

## Native Nginx runtime

`WebRuntime.start` reads the persisted engine selection. WebForge starts the
in-process server; auto/native uses a packaged real upstream Nginx executable.
Explicit native selection never substitutes another engine.

Nginx owns the public loopback endpoint and forwards safe project files,
diagnostics, SSE and HTTPS upstream transport to private Dart middleware. HTTP
proxies and WebSocket upgrades are native. Both listeners share a session and
stop together. Native route generation includes HTTPS prefixes so scheme does
not change longest-prefix priority. Startup reserves the requested public port,
writes a session-local config, runs `nginx -t`, and verifies a unique token through
the native health location. Version/config/signal commands are bounded and kill
their process on timeout. Native access logs are read in bounded chunks.

Windows packages the official executable through CMake. Android builds official
source with retained Termux inputs and local Bionic type patches, targets API 24,
and packages PIE executables through legacy native-library extraction. Source
and native artifacts have SHA-256 records. Shell/C/patch inputs keep LF in Git.

HarmonyOS arm64/x86_64 cross-compilation and signed HAP packaging work. On the
phone simulator, shell execution passed but the original app package had mode
100644 and returned EACCES. System `echo` execution inside the app succeeded.
The module now declares both binaries in `executableBinaryPaths`; the signed HAP
retains the declarations, but its app execution still requires verification.
Auto handles permission denial with a WebForge session; explicit Nginx reports
the failure. Android x86_64 app execution passed on an API 37 / 16 KiB emulator.
Android arm64/32-bit device checks and Apple builds remain unverified.

## Desktop completion (2026-10-01)

The Linux runner builds the retained, checksum-verified upstream source and
installs an executable plus its license under the bundle's `data/nginx/`.
The macOS runner builds all requested Xcode architectures, bundles the helper
under `Contents/Helpers/nginx`, and signs it with sandbox inheritance. Native
feature probes use the same architecture flags as the build. No new network
downloads or third-party system libraries are needed beyond the C toolchain.
Runtime discovery resolves these packaged paths and platform-specific checkout
paths. The existing Nginx integration tests use that discovery on each desktop.

The change boundary is the missing Linux/macOS native build, packaging and
discovery chain: `scripts/build_nginx_desktop.sh`, `scripts/bundle_nginx_macos.sh`,
Linux CMake, macOS Xcode/signing, `web_runtime.dart`, and the native integration
suite. Other language products have independent active platform tasks. iOS
retains its in-process WebForge engine because its application cannot launch
the upstream Nginx child process; embedded Nginx would require a different
lifecycle integration and is not established by these desktop changes.
