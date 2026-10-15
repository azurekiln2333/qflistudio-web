# Example & tutorial browser verification

Date: 2026-10-15. Task: `10-15-webforge-content-curriculum`.
Runner: `scripts/run_examples.mjs` (Playwright Chromium, per-example isolated
browser context).

## Oracles (ownership split, no cross-editing)

| Topic | Module | Owner | Contract |
| --- | --- | --- | --- |
| JavaScript (101) | `scripts/js_example_assertions.mjs` | this task | `owns(id)`, `assertJs(page, ctx)` |
| HTML/CSS (200) | `scripts/web_markup_assertions.mjs` | p6 | `assertMarkupExample(page, example, addCheck) -> bool`, `COVERED_IDS` (array), optional `MISSING_RESOURCE_ALLOWLIST` (Map<id, exact-path[]>) |

The runner never falls back to a green result for an uncovered id; a missing
oracle entry is a hard failure.

## Cross-cutting checks (runner, every example)

- No page errors.
- `#webforge-check` marker present.
- **No external requests of any kind**, including images (offline store
  requirement, no exemptions).
- **No broken internal resources**: same-origin `requestfailed` / HTTP >= 400 is
  a failure unless the example's oracle declares that exact id+path as an
  intentional missing teaching resource (minimal match, never global).
- Each example runs in a **fresh browser context** (isolated localStorage,
  cookies, storage); clipboard permissions are granted per context.

## Lesson/example mapping proof

Every lesson's delivered code must equal its example's code after marker
normalisation (full normalised body, not a shared first line), all 301 bodies
are distinct, and every entry's `type` is `html` with `language` carrying the
topic. Mapping issues are reported and fail the run.

## Current result

- Examples: 301. Assertions: 1820. **Passed 301 / Failed 0. Mapping issues 0.**
- JavaScript: **101 / 101 pass** (each has a concrete expected console / DOM /
  interaction / canvas result).
- HTML/CSS: **200 / 200 pass.**
- `scripts/audit_web_content.py --product` → 0 issue; emit is byte-idempotent.

Earlier failures (unquoted `url(data:image/svg+xml,…)` with spaces dropped by
CSS, external `my.woff2` font, `placehold.co` images) were fixed at the source
by p5; see [`final-verification-handoff.md`](./final-verification-handoff.md)
for the corrected attribution.

The full per-id table is written to
[`example-execution-report.md`](./example-execution-report.md).
