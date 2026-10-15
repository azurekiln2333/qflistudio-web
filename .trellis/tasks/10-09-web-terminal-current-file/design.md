# Design

## Behavior gap and contract

The Run gesture already captures the active file; only the HTML preview branch
drops it. Add optional WebFilePreviewSession with String urlForFile(String
absolutePath), in core lib/services/web_preview_file.dart. Keep the existing
WebPreviewSession and webPreviewFactory unchanged.

Use one shared webPreviewUrlForFile resolver in that module: canonicalize the
real document root and file, require an existing file inside the root, encode
individual URI path segments, and throw a short error for invalid targets.

LocalWebServer, WebDevServer and NginxSession implement the optional interface.
Nginx uses its public URL and its middleware's configured root. A regular tap
uses server.url; long press uses the capability. The browser and copy action
receive the same URL. Legacy sessions remain compatible with normal preview;
unsupported per-file preview reports an error rather than opening the default.

Stop a newly started server if target resolution fails. Cancel old debug
subscriptions and stop the previous preview before starting a replacement.
Preserve Java's existing save, Run gesture and terminal changes.

## Expected files

- Core patch: new lib/services/web_preview_file.dart; small changes to
  lib/services/local_web_server.dart and the HTML branch in editor_page.dart.
- Web: lib/services/web_dev_server.dart and lib/services/nginx_session.dart,
  focused tests and relevant runtime-contract documentation.

No global pending-entry state, factory signature change, persistent entry
override, terminal UI rewrite, new shell backend or runtime installation work.

## Validation

Exercise real loopback HTTP for default/selected/default, relative assets,
derived and explicit roots, escaped filenames, invalid targets and the public
Nginx listener. Reuse shared widget coverage for Run gestures and terminal
continuity. Review current source and available terminal captures. Only one
Flutter test runner for this task at a time.
