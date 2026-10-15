# Final handoff — CSS data-URI root cause and close-out

> Corrected attribution. This supersedes the earlier wording in this file that
> suggested the three CSS failures were markup-oracle misreads. That was wrong:
> p6's controlled probe proved the **source** was at fault. The earlier stage is
> kept below as history.

## Root cause (p6 controlled probe — authoritative)

`css-example-062`, `css-example-078`, `css-example-088` failed because their CSS
declared an **unquoted `url(data:image/svg+xml,...)` that contains spaces**. A
CSS `url()` token with unescaped spaces and no quoting is parsed as invalid, so
the browser drops the declaration and the computed `background-image` is `none`.
The function `url(data:...)` with spaces must be wrapped in quotes (or the
spaces percent-encoded):

```css
/* dropped by the CSS parser (invalid token) */
background: url(data:image/svg+xml,%3Csvg xmlns=%27...%27 width=%2748%27 ...);

/* valid */
background: url("data:image/svg+xml,%3Csvg xmlns=%27...%27 width=%2748%27 ...");
```

p6's probe confirmed the computed value was `none` for the **source as written**,
and that quoting the URL makes it resolve. This is a source defect, not an
assertion defect.

## Ownership

- `css_data4.py` (css-062) and `css_data5.py` (css-078, css-088): quote the data
  URIs. Owned by the HTML/CSS source owner (p5).
- `css_data5.py` (css-073): remove the external `@font-face src: url("my.woff2")`
  (inline a data-URI font or drop the external font, keeping the fallback
  teaching point). Owned by p5.
- `supplement.py` html-097 (`rest.css`): **fixed** — replaced the external
  stylesheet with a runtime `Blob`-generated non-critical stylesheet
  (`onload` -> `revokeObjectURL`). Owner: this task (allowed scope).
- `supplement.py` html-096 (image map): **fixed** by p5 — inline SVG data URI,
  `usemap`/`area` and 240x80 coordinates preserved.

## Runner policy (final)

- Same-origin decided by `new URL(url).origin === serverOrigin`; `data:`,
  `blob:`, `about:` allowed by protocol; everything else (including images)
  blocked and recorded. `page.setDefaultTimeout(3000)`.
- Broken internal resources (`requestfailed` / HTTP>=400, same-origin) fail,
  except an exact `URL.pathname` allowlist entry. Single source of truth:
  p6's `MISSING_RESOURCE_ALLOWLIST` if exported, else the runner default
  `html-example-006 -> ["/missing.png"]`. No substring matching, no global
  exemption.
- One isolated browser context per example.

## Close-out (pending p5 CSS fix)

On p5's completion event: run `python -X utf8 scripts/emit_content.py` once,
then a single full `node scripts/run_examples.mjs`, and freeze only on
**301/301 with mapping issues = 0**. The full per-id table lands in
[`example-execution-report.md`](./example-execution-report.md).

---

## Historical (pre-correction notes, kept for traceability)

An earlier revision of this file described these failures as markup-assertion
problems. That conclusion was disproven by p6's probe and is not valid; the
authoritative cause is the unquoted data URI above.
