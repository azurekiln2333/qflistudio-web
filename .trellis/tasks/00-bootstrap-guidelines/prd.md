# Project guideline bootstrap

## Goal
Document the actual Flutter/Dart product conventions so future work can load
repository-backed guidance before implementation and verification.

## Requirements
- Cover backend services, native runtime/packaging and frontend UI/state/testing.
- Reference real paths and symbols, with examples and observable error contracts.
- Exclude generic ORM, React hook and TypeScript templates that do not apply.
- Keep shared editor/shell ownership in qfli_studio_core and product tools/content
  in qfli_web.

## Acceptance
- [x] Backend directory, errors, quality, native runtime, Web runtime and release
  verification guides are populated and linked from the backend index.
- [x] Frontend directory, components, state, quality and content imports are
  populated and linked from the frontend index.
- [x] Examples cite actual widgets, services and checks; no unfilled templates.
- [x] All index links resolve and relevant spec files are included in Git.

## Verification
The initial source review was completed on 2026-10-11. On 2026-10-15 the guides
were reconciled with the integrated tools page, product curriculum, embedded
Nginx engine selection, native tests and release build workflow. See
[verification-2026-10-15.md](./verification-2026-10-15.md).

Backend evidence: lib/services/, native/nginx/embedded/, scripts/build_nginx_*,
vendor/nginx/SOURCE.json and tool/nginx_smoke.dart. Frontend evidence:
lib/main.dart, lib/pages/, lib/content/ and the product widget/import suites.
Native or device success is recorded only in the owning platform tasks;
bootstrap completion does not imply every platform was tested.
