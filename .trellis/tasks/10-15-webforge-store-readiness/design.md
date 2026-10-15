# Design and ownership

Use existing StudioProfile extension points and offlineOnly policy. Web preview
and tools stay in the product; retain shared shell/terminal contracts. Override
content through contentRepositoryFactory and product assets when required.

## Verified workers
All three pi cwd values resolve to `D:/MyNewProjects/qfli_web`.
- `wD:p5`: terminal audit, product terminal tests/delegate, own child task.
- `wD:p6`: main.dart, Web tools UI, existing profile/UI tests, own child task.
- `wD:p7`: content assets/repository/generator/tests, pubspec.yaml, own child task.
- Main (`wD:p1`): platform/native review, builds/device runs, integration records.

Workers stage explicit owned paths and commit verified batches. Main serializes
platform builds. Content wiring in main.dart is coordinated between UI/content
workers. Shared-core findings are recorded before any coordinated shared write.

## Compatibility and rollback
Retain five-page core shell and preview session capabilities. Preserve initial
dirty work; review and commit relevant native changes separately. Revert scoped
commits to roll back, never reset concurrent work.
