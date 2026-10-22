# Design

## Ownership and boundaries

This parent retains the whole user request. Product coordinators own sibling apps and the C coordinator is the sole common-core integrator. WebForge owns its `lib/pages`, `lib/services`, `lib/content`, curriculum assets/generators, browser oracles, product tests and OHOS test adapter. Do not modify core or another product without a narrow agreed allocation. Use global `qfli-core-release-sync` for exact API/evidence handoffs.

Existing source behavior gaps: tools currently push feature routes from `WebToolsOverview`; the user needs controls embedded on Tools. Catalog baseline has 301 real independent documents but no current OHOS per-entry proof. Web profile has no syntax-analysis callback. New Web content is absent. Shared filters/diagnostics/explorer are being implemented by another owner.

## Content pipeline

Keep subject (`language`) distinct from executable format (`type: html`). Author 60 new complete topics per subject in separate modules. Each topic has Chinese explanation, prerequisites, concepts, complete offline document, expected result, pitfalls and an exercise. Preserve existing IDs; new IDs continue at HTML101/CSS101/JS102. One integrator updates `emit_content.py` and aggregate JSON only after baseline repairs. Browser runner must require an exact per-entry oracle, isolated context, no external traffic, independent companion assets and complete tutorial/example mapping. New oracles live in separate modules to avoid concurrent edits.

## Tools and editor

Reuse existing `WebServerToolsView`/`WebCodecToolsView` as embedded controls with finite scroll ownership. Add concrete offline Web tools only when their parser/runtime is available and covered by semantic tests (local asset/link inspection, structured formatting/validation, color and layout utilities, browser console/request logs). Do not label ad-hoc token heuristics a full compiler. Consume the core owner's typed unsaved-buffer analyzer contract before wiring source ranges. Actual source snapshots, availability, generation cancellation and no program execution/network/source writes are required.

Preserve pre-existing `main.dart` edits; profile wiring uses a narrow reviewed hunk only after the common API is published. Editor panels, breakpoints and ports must reflect actual runtime capabilities. Local server request/console logs already exist; integrate these instead of duplicating transcript stores.

## OHOS verification

Inspect current ArkWeb bridge and native runtime paths. Deliver a device-executable exhaustive catalog harness using the shipped catalogs and semantic oracles. Distinguish host browser results, unsigned packaging, signed installation and OHOS execution. `hdc` Empty is an open device gate. No sibling signing identity, externally downloaded runtime, test-only fixture or historical artifact can satisfy the gate.

## Compatibility, rollback and risks

Keep catalog IDs/import format stable; preserve terminal access and five shell destinations. Follow product offline gates and loopback bind. Commit coherent explicit paths, preserve unrelated WIP, and do not amend. Revert task-owned commits to roll back. Serialize Flutter OHOS builds, generated registries and aggregate catalog generation. Cross-product completion needs current evidence from every coordinator, not counts from historical reports.
