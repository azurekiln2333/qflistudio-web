# Emitter integration & check-marker fix

Scope of this worker (exclusive):

- `scripts/emit_content.py` — integrate the three authored expansion modules, keep
  legacy ids, fix the marker-insertion defect, raise the success gate to the real
  catalog target.
- `scripts/test_emit_content.py` — new regression suite (repo convention: plain
  `main()` + asserts, runnable with the stdlib only, no pytest available here).
- this research note.

Out of scope and untouched: `scripts/run_examples.mjs`, all `*_assertions.mjs`
oracles, `scripts/curriculum/*` data modules, `assets/content/*.json`,
`lib/**`, `main.dart`, platform files, Flutter tests. **No aggregate asset was
written** — root regenerates after every owner lands.

## 1. Wiring

`LANGUAGES` now appends the authored modules after the shipped baseline:

```python
"html":       html_data.* + supplement.HTML5 + html_expansion.HTML_EXTRA,   # 100 + 60
"css":        css_data.* + supplement.CSS6  + css_expansion.CSS_EXTRA,      # 100 + 60
"javascript": js_data.*                     + js_expansion.JS_EXTRA,        # 101 + 60
```

`bulid()` numbers entries per language, so the shipped ids are preserved by
construction and the expansions simply continue:

| subject | baseline ids | new ids | total |
| --- | --- | --- | --- |
| html | `html-*-001…100` | `html-*-101…160` | 160 |
| css | `css-*-001…100` | `css-*-101…160` | 160 |
| javascript | `js-*-001…101` | `js-*-102…161` | 161 |
| **catalog** | 301 | +180 | **481** |

Verified: ids are contiguous per language with no gaps, no renumbering, and
`build()` returns 481 tutorials and 481 examples with 0 lesson/example mapping
issues, 481 distinct lesson bodies and 0 duplicate titles.

`MIN_TOPICS = {"html": 160, "css": 160, "javascript": 161}` and
`MIN_TOTAL = 481` now gate `main()`; it previously accepted `>= 100`, which could
not detect a silently truncated expansion. A below-target run prints the
per-language `(actual, required)` pairs and exits non-zero.

## 2. The real marker bug

### Symptom

The legacy helper did:

```python
marker = "webforge-check"
if "</body>" in code:
    doc = code.replace("</body>", f'  <output id="{marker}" hidden>ok</output>\n</body>')
```

Two independent defects, reproduced by the test suite:

1. **`str.replace` without `count` replaces every occurrence.** Any document with
   more than one `</body>` receives multiple markers; the runner requires
   `document.querySelectorAll('#webforge-check').length === 1`, so the entry is
   reported as a marker failure.
2. **First/all occurrences may live inside a `<script>` body.** A lesson that
   builds an embedded document (an `<object>`/Blob `data` string) legitimately
   contains `'…</body></html>'`. Injecting there puts the marker into JavaScript
   source, and because the injected snippet contains a newline, a single-quoted
   string literal becomes unterminated → `SyntaxError: Invalid or unexpected
   token`, the whole script dies and every downstream assertion fails.

This was not hypothetical: `html-tutorial-137`（object 嵌入文档与回退内容）contains
`</body></html>` inside its embedded-document string and previously received
**two** markers, one of them inside the script.

### Fix

Insertion is performed by one shared, **tokenizer-aware structural end-tag
scanner** used by all three language branches. It walks the document the way an
HTML tokenizer does and records the offset of the last *real* `</body>` / `</html>`,
never a lookalike that a browser would treat as text:

```python
_RAWTEXT_ELEMENTS = {"script", "style", "xmp", "iframe", "noembed", "noframes", "noscript"}
_RCDATA_ELEMENTS  = {"textarea", "title"}
_STRUCTURAL_END_TAGS = ("body", "html")

def structural_end_tag_offsets(code) -> dict[str, int]:   # "body"/"html" -> offset
    ...  # skips comments, bogus comments, quoted attrs, rawtext/RCDATA, <template>

def _insert_check_marker(code, marker=CHECK_MARKER):
    offsets = structural_end_tag_offsets(code)
    for name in _STRUCTURAL_END_TAGS:                     # body first, then html
        at = offsets.get(name)
        if at is not None:
            return code[:at] + snippet + code[at:]        # offset splice, bytes kept
    return code + "\n" + snippet                           # fragment / <plaintext>
```

What the scan skips, and why each mattered:

| region | example | would otherwise break |
| --- | --- | --- |
| comment | `<p>x</p></body><!-- </body> -->` | marker swallowed by the comment → runner sees 0 markers |
| quoted attribute | `<div title="</body>">` | marker injected inside the attribute value |
| raw text | `<script>`, `<style>`, `<noscript>`, `<iframe>`, `<xmp>`, `<noembed>`, `<noframes>` | marker lands in JS/CSS source (newline → `SyntaxError`) |
| RCDATA | `<textarea>`, `<title>` | marker becomes literal text of the element |
| template content | `<template><p></body></p></template>` | marker goes into a separate fragment, not the document |
| bogus comment | `<? </body> ?>`, `<! </body> >` | false anchor |
| `<plaintext>` | everything after it is text | no structural anchor exists at all |

End tags are matched case-insensitively and tolerate whitespace or a stray
solidus before `>`: `</BODY>`, `</body >`, `</Body\n>`, `</body/>` are all real
anchors. Attribute scanning honours both quote styles and entity text inside
them. Insertion is an offset splice into the original string, so the surrounding
bytes — including the anchor tag's own spelling and spacing — are preserved
verbatim and offsets from the scanner remain valid for callers.

`html.parser.HTMLParser` was considered and rejected: it only treats
`script`/`style` as CDATA (`CDATA_CONTENT_ELEMENTS`), so `</body>` inside
`<textarea>`/`<title>` would be reported as a real end tag, it resolves positions
via `(line, col)` rather than offsets, and it normalises/auto-corrects the tree.
A ~60-line explicit scanner keeps byte offsets exact and matches browser
behaviour for the cases above.

Behaviour change is limited to the injected marker position. Verified across the
catalog: **480 of 481 documents are byte-identical to the legacy replacement
output**; the only difference is `html-137` (2 markers → 1, correctly placed
outside the script), plus the newly-handled hazards above, none of which occur in
the shipped corpus.

Properties:

- exactly one insertion — no `replace`, so duplicates are impossible;
- only positions outside comments/attributes/raw text/template content are
  candidates, so JavaScript and CSS source are never modified;
- the last real `</body>` wins, which is the document end, and the marker stays
  inside `<body>` preserving document structure;
- unclosed `<script>` is treated as extending to EOF, so the helper stays total
  instead of panicking on malformed fragments (such a document is already broken
  content and is rejected by the audit/runner, not silently "fixed").

Behaviour change is limited to the injected marker position; the delivered
lesson/example bodies are otherwise byte-identical (`build()` output diffed
against the old module for every non-defective entry).

## 3. Regression suite

`python -X utf8 scripts/test_emit_content.py` → 9 tests, all pass, exit 0.

| test | asserts |
| --- | --- |
| `test_catalog_target_counts` | exactly 481/481, per-language 160/160/161, `type == html`, `checkMarker` set |
| `test_ids_preserve_baseline_and_continue` | ids contiguous from 001, no renumbering; expansion modules are 60/60/60 with JS 102…161 |
| `test_lesson_example_mapping_and_distinctness` | every lesson ↔ one example, equal bodies modulo marker, 481 distinct bodies, unique titles |
| `test_marker_injected_exactly_once` | 1 marker per document, before the scanner-identified structural end tag |
| `test_marker_not_swallowed_by_comment_after_body` | comment after the real `</body>` (and before it) is skipped; comment preserved verbatim |
| `test_marker_recognises_case_and_whitespace_end_tags` | `</BODY>`, `</body >`, `</Body\n>`, `</body/>`, `</HtMl >` are real anchors, spelling preserved |
| `test_marker_skips_text_regions` | quoted/single-quoted attributes, `textarea`, `title`, `style`, `noscript`, nested `template`, bogus comments |
| `test_shipped_template_lessons_anchor_at_real_body_end` | the 4 shipped `<template>` lessons anchor on their own closing body tag |
| `test_plaintext_document_has_no_structural_anchor` | `<plaintext>` ⇒ no anchor, marker appended (documented fallback) |
| `test_marker_ignores_body_tag_inside_script` | the original regression: in-string `</body>` untouched, marker after `</script>` |
| `test_later_body_lookalikes_do_not_duplicate_marker` | three `</body>` literals in an array keep one marker |
| `test_marker_fallbacks` | body-only, html-only, fragment, unclosed-script inputs |
| `test_gate_rejects_below_target` | raising a minimum makes the gate report the shortfall, then restores it |
| `test_no_asset_write` | `build()` never creates or modifies `assets/content/*.json` |

**Regression validity was proven negatively** twice: monkeypatching the legacy
`str.replace` implementation back in makes four tests fail (`html-tutorial-137` →
2 markers, comment-swallowed marker, uppercase/whitespace anchor missed, quoted
attribute mis-split), and monkeypatching the intermediate regex-masking version
back in makes the comment/uppercase/attribute tests fail. The suite therefore
guards the real defects rather than describing the new code.

## 4. Verification log (Python only, per scope)

```
python -X utf8 scripts/test_emit_content.py
  ok  test_catalog_target_counts
  ok  test_ids_preserve_baseline_and_continue
  ok  test_lesson_example_mapping_and_distinctness
  ok  test_marker_injected_exactly_once
  ok  test_marker_not_swallowed_by_comment_after_body
  ok  test_marker_recognises_case_and_whitespace_end_tags
  ok  test_marker_skips_text_regions
  ok  test_shipped_template_lessons_anchor_at_real_body_end
  ok  test_plaintext_document_has_no_structural_anchor
  ok  test_marker_ignores_body_tag_inside_script
  ok  test_later_body_lookalikes_do_not_duplicate_marker
  ok  test_marker_fallbacks
  ok  test_gate_rejects_below_target
  ok  test_no_asset_write
  PASS   (exit 0)
```

Additional ad-hoc invariants checked with `build()` (no writes):

- 481 tutorials / 481 examples; topics `{html: 160, css: 160, javascript: 161}`;
- ids contiguous: `html-*-001…160`, `css-*-001…160`, `js-*-001…161`;
- 0 mapping issues, 481 distinct bodies, 0 duplicate titles, all `type == html`;
- 0 marker defects: every raw lesson and every emitted document has exactly one
  marker, and it sits before the scanner-identified structural end tag;
- parity: **1 of 481** documents differs from the legacy replacement output
  (`html-137`, 2 markers → 1); the other 480 are byte-identical;
- 0 residual marker text after `run_examples.mjs`'s `normaliseDoc` strip;
- every document still contains its own `</body>`;
- `assets/content/*.json` unchanged (`examples.json` / `tutorials.json` retain
  their 2026-10-15 mtimes).

Flutter was not run (out of scope). The runner and oracles were not executed by
this worker; the browser pass belongs to root after regeneration.

## 5. Handover notes for root

1. Regenerate once all owners are done: `python -X utf8 scripts/emit_content.py`
   → expect `tutorials: 481 … topics={'html': 160, 'css': 160, 'javascript': 161}`
   and `examples: 481 …`. Exit code 0 only when the target is met.
2. `run_examples.mjs` needs the expansion oracle dispatch (`html/css/js
   expansion` modules) before the full browser pass; that file is not mine.
3. `scripts/test_emit_content.py` is stdlib-only and read-only, so it can run in
   CI alongside the browser runner without touching shipped assets.
4. Known deliberate behaviours: `<plaintext>` documents have no structural end
   tag by definition, so the marker is appended (no shipped lesson uses it); a
   document truncated inside `<script>` is treated as raw text to EOF and also
   falls back to appending — both are broken-content cases the audit/runner is
   expected to reject rather than something the emitter should silently repair.
