# WebForge local web development runtime

## Goal

Deliver a usable local web development server, project tools, and editor integration for WebForge.

## Requirements

- Run a local web project from the editor on supported devices without an external service.
- Resolve both root-level and `src/` HTML entry points and serve their relative assets correctly.
- Provide useful local development behavior: safe static files, console/error capture, request diagnostics, live reload, and configurable API proxying and SPA fallback.
- Expose practical web tools in the product UI, with truthful status and no unfinished-feature labels.
- Port and integrate actual upstream Nginx for local use on feasible target platforms; validate packaging and lifecycle per platform. Do not label an alternative server as Nginx.
- Preserve existing project/editor navigation and unrelated changes in the shared core checkout.
- Commit each coherent implementation change with a conventional message, narrowly staged per repository.

## Acceptance Criteria

- [ ] New and imported HTML projects preview with working CSS, JS, images, and nested routes.
- [ ] Only one public preview endpoint exists per project run; its runtime and
  any private middleware stop when the editor exits.
- [ ] HTTP file serving rejects traversal and symlink escapes; missing assets return 404 rather than HTML.
- [ ] Console, errors, and request failures reach a visible debugging surface.
- [ ] Configured proxy routes and SPA fallback work in integration tests.
- [ ] Web tools are reachable from the existing app navigation and perform real work.
- [ ] Supported desktop and mobile builds pass relevant analysis/tests and runtime smoke checks.
- [ ] All task-owned changes are committed with standard messages; pre-existing work is excluded.
- [ ] A real upstream Nginx binary is integrated and verified; platform restrictions are documented with evidence.

## Notes

`qfli_web` is the product repository. The editor, navigation, and current preview server live in the sibling `qfli_studio_core` repository, which already has unrelated uncommitted changes. Integrating these capabilities requires a narrow change there and separate commits.

Current implementation evidence is recorded in `research/native-nginx.md` and
`vendor/nginx/VALIDATION.md`. Windows native tests and mobile builds passed;
Android x86_64 application smoke passed on an API 37 / 16 KiB emulator.
Android arm64/32-bit devices and HarmonyOS app execution remain open. Keep this
task in progress until those checks are resolved.
