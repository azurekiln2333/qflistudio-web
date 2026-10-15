# Guideline completion review

The existing project-specific guidelines were reviewed against current source
and are included in Git explicitly, because local Trellis defaults ignore spec
files. Backend and frontend indexes now resolve to committed documents.

Updated obsolete `_WebToolsPageState` / `_serverTab` references to
`_WebServerToolsViewState.build`, documented the integrated ToolsGrid body and
five-page product boundary, and corrected engine fallback and mobile smoke
failure contracts. Content import contracts distinguish subject `language`
from executable `type: html`. Release verification records pub-enabled mode
transitions, binding exception propagation, independent watch probes, artifact
freshness and signing limitations.

Evidence: 2026-10-15 live-source analyze has no issues, all 82 product tests pass,
116 shared regression tests pass, and four shared About identity tests pass.
No new native Linux or Apple build result is inferred from these checks.

The bootstrap scope is complete. Platform device/signing work remains tracked
in the product release/runtime tasks with its own explicit limitations.
