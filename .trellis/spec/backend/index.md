# Backend Development Guidelines

> Guidelines for the Dart services, web runtime and native build/packaging layer
> of `qfli_web`. This is a Flutter product repository, so "backend" covers the
> non-UI runtime rather than a server application.

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Repository and `lib/services` layout, naming | Implemented |
| [Error Handling](./error-handling.md) | Error types, validation gate, diagnostics, HTTP status contract | Implemented |
| [Quality Guidelines](./quality-guidelines.md) | Required checks, forbidden patterns, review checklist | Implemented |
| [Native Nginx Runtime](./native-runtime.md) | Multi-platform engine build/packaging and platform limits | Implemented |
| [Web Runtime](./web-runtime.md) | Preview, project settings, proxies, diagnostics, lifecycle contracts | Implemented |
| [Release Verification](./release-verification.md) | Build modes, native test failures, signing and device evidence | Implemented |

## Pre-Development Checklist

- Serving, preview, proxy or project-config change → read
  [Web Runtime](./web-runtime.md).
- Native engine, packaging or platform-runner change → read
  [Native Nginx Runtime](./native-runtime.md).
- Any runtime change → read [Error Handling](./error-handling.md) and
  [Quality Guidelines](./quality-guidelines.md).

## Quality Check

- Run `flutter analyze --no-pub lib test` and the affected
  `flutter test --no-pub --concurrency=1` suites.
- Verify native claims against real engine behavior and per-platform evidence
  (see [Native Nginx Runtime](./native-runtime.md)); never advertise Nginx
  without a packaged, started and stopped real engine.
