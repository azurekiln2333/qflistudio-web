# Core patch review package — current-file HTML preview

Task: `10-09-web-terminal-current-file`
Scope: core-side change only, delivered as a reviewable git patch. Core working
tree was **not** modified; only read.

## Artifacts

| Path | Purpose |
| --- | --- |
| `core-web-preview-file.patch` | Standard `git apply` patch (LF, `a/lib/...` / `b/lib/...`). |
| `core-baseline/lib/...` | Captured copies of the three core files as they existed in the core working tree when the patch was produced. Unchanged across revisions. |
| `proposed/lib/...` | Post-patch file copies used to generate the patch. |
| `README-core-patch.md` | This file. |

## Patch summary

```
 lib/editor/editor_page.dart        | 48 +++++++++++++++++++----
 lib/services/local_web_server.dart | 14 ++++++-
 lib/services/web_preview_file.dart | 80 ++++++++++++++++++++++++++++++++++++++
 3 files changed, 132 insertions(+), 10 deletions(-)
```

Verified locally:
- `git apply --check` against the captured core baseline: **OK**
- `git apply` then `dart analyze` on the three files: **No issues found!**
- Resolver URL probe: `main2.html` → `.../main2.html`, `src/index.html` →
  `.../src/index.html`, `a b/c#d.html` → `.../a%20b/c%23d.html`.

## Design decisions (per reviewer constraints)

- **No factory signature change.** `webPreviewFactory` stays
  `Future<WebPreviewSession> Function(String projectPath)`.
- **No static pending field.**
- **No fallback outside the root.** `webPreviewUrlForFile` throws a short
  `FileSystemException`; the editor stops the just-started server instead of
  opening the default page.
- **Optional capability interface.** `WebFilePreviewSession implements
  WebPreviewSession` in `lib/services/web_preview_file.dart`. Normal preview
  only needs `WebPreviewSession`; long press additionally requires the
  capability.
- **Resolution lives in the session domain.** `webPreviewUrlForFile` takes
  `baseUrl` + `documentRoot` + `filePath`, canonicalizes both root and file,
  checks containment, and rejects hidden path segments (except `.well-known`),
  backslashes and NUL so the result is never a URL the server would 403. The URL
  is built with `Uri.parse(baseUrl).replace(pathSegments: ['', ...segments])` so
  `Uri` encodes each segment once — no manual `encode` + string concat.
- **Short English errors:** `preview root does not exist` / `file does not
  exist` / `file is outside the preview root` / `preview does not support
  individual files`. Existing Chinese UI strings are untouched.
- **Cleanup ordering.** Before starting a replacement: `await` cancel the old
  `_debugSub` and null it, then move the old `_previewServer` into a local, null
  the field, and stop it — so no stopped object is referenced. On any failure,
  including `SocketException`, a single `catch` cancels the new debug
  subscription, clears `_previewServer` when it is the failed session, and stops
  the new server. Errors surface through the existing `_showSnack` UI.
- **Untouched:** Java-side UI, gestures, save logic, and the normal tap path
  (`entryOverride == null` → `server.url`).

## Web-side follow-up contract (not in this patch)

- `WebDevServer` and `NginxSession` implement `WebFilePreviewSession` by calling
  `webPreviewUrlForFile` with their real document root.
- Nginx uses the **public** URL and `_bridge.config.root`.
- `main.dart` / `WebRuntime.start` are unchanged: the session's `url` getter
  stays the default entry; `urlForFile` is the only new surface.


## Applied status

Codex applied this reviewed patch to qfli_studio_core with approved filesystem
access. Do not reapply it to the current working tree. A subsequent Java-side
format pass reflowed one HTML error-display line; the behavior remains present
and passed the final 47 Web plus 61 shared-core tests. See final-verification.md.
