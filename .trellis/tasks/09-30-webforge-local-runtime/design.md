# Design

## Current behavior

The shared editor starts `LocalWebServer` and then asks `RunnerService` to run the same HTML file. `RunnerService` starts a second listener. The template writes `src/index.html`, `src/style.css`, and `src/main.js`, while the existing server falls back to HTML for missing asset paths. The product repository currently has no Web-specific tools UI.

## Ownership

- `qfli_web`: Web development server, project configuration, diagnostics, web tools, and product-specific tests.
- `qfli_studio_core`: minimal editor and navigation hooks required to use WebForge's server and tools. Shared behavior must remain unchanged for other products.

## Server contract

Bind loopback on a dynamic port by default. Choose the content root from an explicit project setting or an existing `index.html` at the root or in `src/`. Resolve requested files against that root, reject escapes and symlink targets outside it, and return 404 for missing assets. HTML responses may inject a localhost-only diagnostics and reload bridge. Configuration is project-local JSON under `.qfli/`; malformed settings report a specific error instead of silently falling back.

Proxy rules match path prefixes and forward to an explicit upstream URL. The proxy must preserve request methods, query strings, response status and headers, and stream bodies with bounded resource use. Avoid forwarding hop-by-hop headers. Provide a local request log and explicit stop/dispose behavior.

## Native Nginx assessment

An actual Nginx build requires native binaries and lifecycle integration separately for Windows, Android, and HarmonyOS. In particular, mobile app execution restrictions must be verified before advertising Nginx. Keep the in-process server clearly identified by its real engine while native packaging is investigated.
