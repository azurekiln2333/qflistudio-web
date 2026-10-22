# Standalone offline IDE completeness

## Goal

Deliver the complete request in `research/user-request.txt`: all standalone QFLI products must provide useful offline development workflows and their complete shipped tutorial/example code must run with their current OHOS toolchains. This task retains the full cross-product scope; a WebForge-only pass cannot close it.

## Authorization and background

- User explicitly authorizes Trellis planning followed immediately by implementation, parallel Pi delegation, standardized commits, and pushing when possible. The later “继续” confirms continuation. No additional process approval is needed.
- WebForge is this repository; product-owned catalogs currently contain 301 paired HTML/CSS/JavaScript topics. Each imports as executable HTML while `language` preserves its subject.
- Other live coordinators own their products. C coordinator owns common-core content filters/badges, explorer/workspace, analyzer integration/panels and highlighting. Obtain current evidence and APIs through global `qfli-core-release-sync`; do not concurrently edit their files.
- Initial WebForge worktree has unrelated uncommitted startup/platform/runtime-audit changes. Preserve them and stage only task-owned changes.
- Initial `hdc list targets` is Empty on 2026-10-22. Host/browser and packaging passes cannot prove OHOS execution.

## Requirements

| ID | Required outcome |
| --- | --- |
| R1 | Follow Trellis planning, implementation, review, spec capture and standardized explicit-path commits; push authorized commits where possible, recording actual remote outcomes. |
| R2 | Inventory and actually verify every shipped example and tutorial code for every standalone product on its current OHOS runtime/toolchain. Record per-entry inputs and semantic expectations; fix failures before expansion. |
| R3 | Add substantially more than 100 new substantive runnable examples, with matched complete tutorials where appropriate. Target 180 additional WebForge topics (60 each HTML/CSS/JavaScript, 481 total), and collect other product expansions. Existing counts do not satisfy “新增”. Every new entry must be tested. |
| R4 | Tutorial/example lists support language chips and language circles near titles as in project lists, including distinct C/C++. Preserve subject language separately from executable import format. |
| R5 | Research current VS Code/JetBrains and language tooling. Deliver useful language-specific offline tools directly in the main Tools page, with actual controls; remove generic dedicated-function gateway cards and avoid secondary feature hubs. |
| R6 | Editor shows offline syntax diagnostics with wavy underlines, correct ranges, Problems navigation and unsaved-code feedback. Use real available language backends and expose unavailable status honestly. |
| R7 | File-tree expansion survives sidebar closure/reopening. Provide persistent workspaces with several project roots in one sidebar, correct file ownership and safe project actions. |
| R8 | Deliver feasible real breakpoint/debug, logs, Output/Debug Console/Terminal/Ports workflows in current runtimes. Capabilities and native evidence govern visible controls; no pretend debugging. |
| R9 | Verify highlighting for all languages/extensions, C/C++ local header creation/import/linking, Python standard/common modules and local offline packages under OHOS sandbox restrictions. |
| R10 | Every standalone product stays offline: no login/cloud/Git/network fetch/external-resource entries. Loopback-only local preview and local interprocess tools remain allowed. |

## Acceptance criteria

- [ ] R1–R10 have current authoritative evidence and ownership in `research/acceptance-ledger.md`; missing platform evidence remains open.
- [ ] All products (`c`, `dart`, `go`, `java`, `json`, `lua`, `note`, `python`, `rust`, `sql`, `web`) have exhaustive catalog inventories, validation records, and applicable tool/editor/offline results.
- [ ] WebForge baseline 301 examples and all tutorial code have full coverage with zero mapping failures and meaningful DOM/style/console/interaction assertions; no external requests are permitted.
- [ ] After baseline repairs, WebForge ships at least 481 unique matched topics with 180 newly authored examples; every document works independently and no runner-only fixture masks missing assets.
- [ ] Current OHOS packaged content/runtime executes every shipped item, with exact HAP/core/toolchain identity and per-entry results. Unsigned HAP/desktop Chromium alone is insufficient.
- [ ] Tools actions are directly reachable in Tools at mobile and large-text sizes, produce correct results and preserve terminal access.
- [ ] Shared changes are consumed and tested without conflicting ownership; subjects/import types and unavailable analyzer/debug capabilities remain honest.
- [ ] Full affected analysis/tests, relevant browser/native/integration checks and fresh OHOS packaging pass; pre-existing work is preserved.
- [ ] Work/spec commits and actual push outcomes are recorded; no unrelated dirty files/private signing material are included.

## Exclusions

Network-dependent features/package downloads, fake capabilities, broad unrelated refactors, replacing signing identities, altering another app's data, and silently narrowing the request are excluded. An unavailable device is a pending acceptance gate, not a scope exception.
