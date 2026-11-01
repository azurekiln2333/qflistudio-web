# Bug Analysis: host-green curriculum with remaining ArkWeb failures

## 1. Root Cause Category

- **D — Test Coverage Gap:** desktop Chromium 156 passed all 481 documents while
  actual ArkWeb 144 first failed 38, then 7. The second device run, rather than
  another identical host rerun, discriminated native layout/input/API behavior.
- **E — Implicit Assumption:** integer-looking CSS geometry was compared exactly,
  a reused pointer was assumed ready, a popover close button was assumed reachable,
  and a platform Promise was assumed eventually to resolve or reject.
- **C — Change Propagation Failure:** earlier tolerance repairs missed remaining
  strict comparisons in 044/114/116/120. A nominally semantic switch geometry
  check used constants supplied by the oracle and therefore could not fail.
- **B — Cross-Layer Contract:** shared owner-root execution correctly changed the
  project path, but also changed normal preview selection from `session.url` to
  the active file. An explicit `root=public` exposes the broken factory contract.

## 2. Why Fixes Failed

1. Broad host success covered different fonts, pixel snapping, viewport and
   permission plumbing. It was necessary but did not predict the native result.
2. Fixed click delays did not prove checked state. Immediate reads observed an
   unchanged switch, then the previous click on the next attempt.
3. Clipboard `try/catch` handled rejection, but could not end a never-settling
   Promise. Synthetic DOM clicks in the first replacement oracle also bypassed
   real actionability and transient-state timing.
4. CSS fractional geometry was repaired locally rather than auditing every
   comparison in each affected case. Mutation coverage caught the constant
   switch assertion only after reviewer inspection identified the false proof.
5. Project ownership and default preview selection were conflated. Product
   configuration, not an editor's fallback entry, owns its default document URL.

## 3. Prevention Mechanisms

| Priority | Mechanism | Specific action | Status |
| --- | --- | --- | --- |
| P0 | Native evidence | Preserve complete failed runs and require a new exact-asset 481 run after repairs | Required; third native pass pending queue |
| P0 | Observable input | Real reachable clicks, hit testing, bounded checked-state wait and measured pseudo-element geometry | Implemented; native rerun pending |
| P0 | Bounded API state | Lesson watchdog/settle-once, immediate feedback, deferred controlled clipboard responses and late-result rejection | Implemented; new full verification pending |
| P0 | Negative controls | Mutate the feature/fallback, move the popover offscreen, and try old async source; no harness-provided rescue | HTML/CSS checks done; revised JS controls pending |
| P1 | Gesture ownership | `SELF_DRIVEN_IDS` prevents generic pre-clicks; errors propagate; initial terminal state cannot masquerade as a response | Implemented |
| P1 | Preview contract | Ordinary Run uses factory session URL; only longpress resolves current file | Core e025805b, Web current-file9 PASS |
| P1 | Executable specs | Keep geometry/input/clipboard/native identity rules in catalog spec and default URL rule in runtime spec | Updated |

## 4. Systematic Expansion

- Similar hazards apply to geolocation, permission prompts, animation completion,
  responsive controls and generated marker/bridge insertion. Verify the actual
  produced source and final user-visible state rather than runner constants.
- Capability probes must be independent of the tested result and must not choose
  expected behavior from that same result. Keep source fallbacks and mutate them.
- Review every assertion in a repaired case, not only the first failure. Preserve
  host, native, packaged-source, signed/unsigned and current-core evidence as
  separate claims. A later source revision invalidates an earlier package match.

## 5. Knowledge Capture

- Catalog geometry, real gesture ownership, bounded observation and negative
  controls are captured in `.trellis/spec/backend/catalog-verification.md`.
- Factory default URL and startup/offline configuration contracts live in
  `.trellis/spec/backend/web-runtime.md`.
- This product has no `src/templates/markdown/spec` directory; these are product
  specs, not Trellis runtime templates. No duplicate template tree is created.
- Spec changes join the next narrow validated work commit. The parent task stays
  active; authored repairs or a desktop pass do not close the native gate.
