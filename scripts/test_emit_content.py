#!/usr/bin/env python3
"""Regression tests for scripts/emit_content.py (curriculum aggregation).

Runs without pytest and without writing any aggregate asset: everything goes
through the pure `build()` / `example_document()` helpers, so the shipped
`assets/content/*.json` files are never touched by a test run.

Covered contracts:

* Catalog shape: 160 HTML + 160 CSS + 161 JavaScript = 481 matched topics, with
  the shipped baseline ids preserved and expansion ids continuing at
  html-101 / css-101 / js-102.
* Lesson <-> example correspondence: every lesson has exactly one example, the
  delivered documents are identical modulo the injected check marker, and all
  lesson bodies are distinct.
* Check-marker injection: exactly one marker per document, always outside any
  `<script>` body, and inserted before the document's real `</body>`.

The marker rules exist because the previous implementation used a plain
`str.replace("</body>", ...)`, which (a) replaced *every* `</body>` occurrence and
(b) could target a `</body>` that lived inside a JavaScript string literal. That
corrupted `html-tutorial-137`, whose lesson builds an embedded document string
containing `</body></html>`, and would silently inject duplicate markers
elsewhere. Both are asserted below.

Run: python -X utf8 scripts/test_emit_content.py
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import emit_content  # noqa: E402

MARKER_HTML = 'id="webforge-check"'
_MARKER_SNIPPET = '  <output id="webforge-check" hidden>ok</output>\n'
MARKER_RE = re.compile(r'\s*<output id="webforge-check"[^>]*>ok</output>\s*')


def _normalise(code: str) -> str:
    """Collapse whitespace and drop the injected marker for comparisons."""
    return re.sub(r"\s+", " ", MARKER_RE.sub("\n", code)).strip()


def _documents():
    tutorials, examples = emit_content.build()
    for tutorial in tutorials:
        yield tutorial, tutorial["lessons"][0], examples


def test_catalog_target_counts() -> None:
    tutorials, examples = emit_content.build()
    assert len(tutorials) == 481, len(tutorials)
    assert len(examples) == 481, len(examples)

    topics: dict[str, int] = {}
    for tutorial in tutorials:
        topics[tutorial["language"]] = topics.get(tutorial["language"], 0) + 1
    assert topics == {"html": 160, "css": 160, "javascript": 161}, topics
    assert sum(topics.values()) == 481

    example_topics: dict[str, int] = {}
    for example in examples:
        key = example["language"]
        example_topics[key] = example_topics.get(key, 0) + 1
    assert example_topics == topics, example_topics

    # Every delivered document imports as executable HTML while the subject
    # language stays in metadata (content-import contract).
    assert all(t["type"] == "html" for t in tutorials)
    assert all(e["type"] == "html" for e in examples)
    assert all(e["checkMarker"] == "webforge-check" for e in examples)


def test_ids_preserve_baseline_and_continue() -> None:
    tutorials, _ = emit_content.build()
    expected_sizes = {"html": 160, "css": 160, "javascript": 161}
    prefixes = emit_content.ID_PREFIX

    for language, prefix in prefixes.items():
        ids = [t["id"] for t in tutorials if t["language"] == language]
        # Baseline occupied 001..100 (HTML/CSS) and 001..101 (JS); the generated
        # ids must stay contiguous so no shipped id is renumbered.
        expected = [
            f"{prefix}-tutorial-{index:03d}"
            for index in range(1, expected_sizes[language] + 1)
        ]
        assert ids == expected, (language, ids[:3], ids[-3:], len(ids))

    # Expansion modules must keep their own documented starting ids.
    from curriculum import css_expansion, html_expansion, js_expansion

    assert len(html_expansion.HTML_EXTRA) == 60
    assert len(css_expansion.CSS_EXTRA) == 60
    assert len(js_expansion.JS_EXTRA) == 60
    assert js_expansion.FIRST_ID == 102
    assert js_expansion.LAST_ID == 161


def test_lesson_example_mapping_and_distinctness() -> None:
    by_lesson: dict[str, dict] = {}
    seen_bodies: dict[str, str] = {}

    for tutorial, lesson, _examples in _documents():
        by_lesson[lesson["id"]] = lesson
        digest = hashlib.sha256(lesson["code"].encode("utf-8")).hexdigest()
        assert digest not in seen_bodies, (lesson["id"], seen_bodies.get(digest))
        seen_bodies[digest] = lesson["id"]

    tutorials, examples = emit_content.build()
    lesson_count = sum(len(t["lessons"]) for t in tutorials)
    assert lesson_count == 481, lesson_count
    assert len(by_lesson) == 481
    assert len(seen_bodies) == 481

    example_by_lesson = {e["sourceLessonId"]: e for e in examples}
    assert len(example_by_lesson) == 481

    for lesson_id, lesson in by_lesson.items():
        example = example_by_lesson[lesson_id]
        assert _normalise(lesson["code"]) == _normalise(example["code"]), lesson_id

    for example in examples:
        assert example["sourceLessonId"] in by_lesson, example["id"]

    titles = [t["title"] for t in tutorials]
    assert len(set(titles)) == len(titles)


def test_marker_injected_exactly_once() -> None:
    for tutorial, lesson, _examples in _documents():
        doc = lesson["code"]
        assert doc.count(MARKER_HTML) == 1, (lesson["id"], doc.count(MARKER_HTML))
        # The marker must sit before the document's real structural end tag, as
        # identified by the tokenizer-aware scanner (not by a raw substring
        # search, which can hit inside comments, attributes or raw text).
        offsets = emit_content.structural_end_tag_offsets(doc)
        anchor = offsets.get("body", offsets.get("html"))
        assert anchor is not None, lesson["id"]
        assert doc.index(MARKER_HTML) < anchor, lesson["id"]


def test_marker_not_swallowed_by_comment_after_body() -> None:
    """A `</body>` inside a comment *after* the real body must be ignored.

    The previous implementation picked the last `</body>` in the text, so the
    comment's copy won and the marker landed inside the comment — invisible to
    the runner's `#webforge-check` count.
    """
    code = (
        "<!doctype html>\n<html><body><p>正文</p></body>\n"
        "<!-- 说明：文档以 </body> 结束 -->\n</html>"
    )
    doc, _ = emit_content.example_document("html", {"code": code})

    assert doc.count(MARKER_HTML) == 1
    # The anchor chosen against the original text is the real body end, not the
    # comment copy that appears later in the file.
    body_at = emit_content.structural_end_tag_offsets(code)["body"]
    assert code[body_at:].startswith("</body>")
    assert doc == code[:body_at] + _MARKER_SNIPPET + code[body_at:]
    # Re-scanning the emitted document puts the marker before the real body end
    # and before the comment, so the marker is a live element, not commented out.
    emitted = emit_content.structural_end_tag_offsets(doc)
    assert doc.index(MARKER_HTML) < emitted["body"]
    assert doc.index(MARKER_HTML) < doc.index("<!--")
    # The comment is preserved verbatim, including its lookalike end tag.
    assert "<!-- 说明：文档以 </body> 结束 -->" in doc

    # A comment *before* the body end must be skipped as well.
    code = "<html><body><!-- </body> --><p>x</p></body></html>"
    doc, _ = emit_content.example_document("html", {"code": code})
    assert doc.count(MARKER_HTML) == 1
    body_at = emit_content.structural_end_tag_offsets(code)["body"]
    assert code[body_at:].startswith("</body>")
    assert doc == code[:body_at] + _MARKER_SNIPPET + code[body_at:]
    emitted = emit_content.structural_end_tag_offsets(doc)
    assert doc.index("-->") < doc.index(MARKER_HTML) < emitted["body"]


def test_marker_recognises_case_and_whitespace_end_tags() -> None:
    """`</BODY >`, `</Body\n>` and `</html />` are real end tags too."""
    variants = [
        "<html><body><p>x</p></BODY></HTML>",
        "<html><body><p>x</p></body >\n</html >",
        "<html><body><p>x</p></Body\n></HTML\n>",
        "<html><body><p>x</p></body/></html/>",
        "<HTML><BODY><p>x</p></BoDy ></HtMl >",
    ]
    for code in variants:
        doc, _ = emit_content.example_document("html", {"code": code})
        assert doc.count(MARKER_HTML) == 1, code
        offsets = emit_content.structural_end_tag_offsets(code)
        assert "body" in offsets, code
        # Marker lands immediately before the original body end tag, and that
        # tag keeps its exact spelling and spacing (offsets index the original
        # string, so nothing is rewritten).
        body_at = offsets["body"]
        assert doc == code[:body_at] + _MARKER_SNIPPET + code[body_at:], code
        assert code[body_at:] in doc, code

    # `</html>` alone is the fallback anchor.
    code = "<HTML><BODY><p>x</p></BODY></HTML >"
    doc, _ = emit_content.example_document("html", {"code": code})
    assert doc.count(MARKER_HTML) == 1
    assert doc.index(MARKER_HTML) < doc.index("</HTML")


def test_marker_skips_text_regions() -> None:
    """Quoted attributes, RCDATA, raw text and template content are not anchors."""
    cases = {
        "quoted attribute": '<html><body><div title="</body>">x</div></body></html>',
        "single-quoted attribute": "<html><body><div title='</body>'>x</div></body></html>",
        "textarea (RCDATA)": "<html><body><textarea></body></textarea></body></html>",
        "title (RCDATA)": "<html><head><title></body></title></head><body>x</body></html>",
        "style (raw text)": "<html><head><style>/* </body> */</style></head><body>x</body></html>",
        "noscript (raw text, scripting on)": (
            "<html><body><noscript></body></noscript></body></html>"
        ),
        "template content": (
            "<html><body><template><p></body></p></template></body></html>"
        ),
        "nested template": (
            "<html><body><template><template></body></template></template></body></html>"
        ),
        "bogus comment": "<html><body><p>x</p></body><? </body> ?></html>",
        "doctype-ish bogus comment": "<html><body><p>x</p></body><! </body> ></html>",
    }
    for label, code in cases.items():
        doc, _ = emit_content.example_document("html", {"code": code})
        assert doc.count(MARKER_HTML) == 1, (label, doc)
        offsets = emit_content.structural_end_tag_offsets(code)
        body_at = offsets["body"]
        assert doc == code[:body_at] + _MARKER_SNIPPET + code[body_at:], (label, doc)
        # The chosen anchor must be the real, closing body tag of the document.
        assert code[body_at:].lower().startswith("</body"), label


def test_marker_ignores_body_tag_inside_script() -> None:
    """The exact regression: a `</body>` inside a JS string must be untouched."""
    inner = (
        "'<!doctype html><html><body>"
        '<p id="inner">运行内联的 HTML 文档</p>'
        "</body></html>'"
    )
    code = (
        "<!doctype html>\n<html><head><title>t</title></head>\n<body>\n"
        f"  <script>\n    var innerDoc = {inner};\n  </script>\n"
        "</body>\n</html>\n"
    )
    doc, marker = emit_content.example_document("html", {"code": code})

    assert marker == "webforge-check"
    assert doc.count(MARKER_HTML) == 1, doc.count(MARKER_HTML)
    # The script string survives byte-for-byte (no injected newline, no marker).
    assert inner in doc
    # The single marker is placed inside the real body, after the script.
    assert doc.index(MARKER_HTML) > doc.index("</script>")
    assert doc.rindex(MARKER_HTML) < doc.rindex("</body>")
    # Nothing was appended after the document root.
    assert doc.rstrip().endswith("</html>")

    # The old implementation inserted the marker at *every* `</body>`; prove the
    # naive replacement would have produced two markers for this input.
    assert code.count("</body>") == 2
    assert doc.count(MARKER_HTML) == 1

    # Strictly parseable JavaScript: the injected snippet contains a newline, so
    # landing inside the string literal would have broken the script.
    assert "\n" not in inner


def test_later_body_lookalikes_do_not_duplicate_marker() -> None:
    """Documents whose script mentions `</body>` repeatedly keep one marker."""
    code = (
        "<!doctype html>\n<html><body>\n"
        "<script>\n" + "var pairs = ['</body>', '</body>', '</body>'];\n" + "</script>\n"
        "</body></html>"
    )
    doc, _ = emit_content.example_document("javascript", {"code": code})
    assert doc.count(MARKER_HTML) == 1
    assert "var pairs = ['</body>', '</body>', '</body>'];" in doc


def test_shipped_template_lessons_anchor_at_real_body_end() -> None:
    """The four shipped `<template>` lessons still anchor on the real body end."""
    template_lessons = [
        lesson
        for lessons in emit_content.LANGUAGES.values()
        for lesson in lessons
        if "<template" in lesson["code"]
    ]
    assert len(template_lessons) >= 4, len(template_lessons)
    for lesson in template_lessons:
        offsets = emit_content.structural_end_tag_offsets(lesson["code"])
        assert "body" in offsets, lesson["t"]
        # The anchor is the document's own closing body tag.
        assert lesson["code"][offsets["body"] :].startswith("</body>"), lesson["t"]
        doc, _ = emit_content.example_document("html", lesson)
        assert doc.count(MARKER_HTML) == 1, lesson["t"]
        assert doc.index(MARKER_HTML) < emit_content.structural_end_tag_offsets(doc)["body"]


def test_plaintext_document_has_no_structural_anchor() -> None:
    """`<plaintext>` makes the rest text, so the marker must be appended.

    No shipped lesson uses it; this pins the documented fallback so a future
    lesson cannot silently receive a marker inside raw text.
    """
    code = "<html><body><plaintext></body></plaintext></body></html>"
    offsets = emit_content.structural_end_tag_offsets(code)
    assert offsets == {}, offsets
    doc, _ = emit_content.example_document("html", {"code": code})
    assert doc.count(MARKER_HTML) == 1
    assert doc.rstrip().endswith("</output>")
    assert doc.startswith(code)


def test_marker_fallbacks() -> None:
    # Body only.
    doc, _ = emit_content.example_document("css", {"code": "<p>x</p></body>"})
    assert doc.count(MARKER_HTML) == 1
    assert doc.index(MARKER_HTML) < doc.index("</body>")

    # No body, but an html root: insert before </html>.
    doc, _ = emit_content.example_document("css", {"code": "<html><head></head></html>"})
    assert doc.count(MARKER_HTML) == 1
    assert doc.index(MARKER_HTML) < doc.index("</html>")

    # Fragment: append.
    doc, _ = emit_content.example_document("css", {"code": "<style>p{color:red}</style><p>x</p>"})
    assert doc.count(MARKER_HTML) == 1
    assert doc.rstrip().endswith("</output>")

    # A document truncated inside `<script>` has no safe insertion point (an
    # unclosed script swallows everything that follows), so the helper appends
    # rather than corrupting JavaScript. Such an input is already a broken
    # lesson and the content audit/runner is expected to reject it; what matters
    # here is that the helper stays total and never lands inside the script.
    doc, _ = emit_content.example_document(
        "javascript",
        {"code": "<html><body><script>var s = '</body>';"},
    )
    assert doc.count(MARKER_HTML) == 1
    assert doc.rstrip().endswith("</output>")
    assert "</body>'" in doc


def test_gate_rejects_below_target() -> None:
    """`main()`'s gate must fail when a language falls below its target."""
    minimums = dict(emit_content.MIN_TOPICS)
    total = emit_content.MIN_TOTAL
    try:
        assert minimums == {"html": 160, "css": 160, "javascript": 161}
        assert total == 481
        emit_content.MIN_TOPICS["javascript"] = 999
        tutorials, _ = emit_content.build()
        topics: dict[str, int] = {}
        for tutorial in tutorials:
            topics[tutorial["language"]] = topics.get(tutorial["language"], 0) + 1
        missing = {
            lang: (topics.get(lang, 0), minimum)
            for lang, minimum in emit_content.MIN_TOPICS.items()
            if topics.get(lang, 0) < minimum
        }
        assert missing == {"javascript": (161, 999)}, missing
    finally:
        emit_content.MIN_TOPICS.clear()
        emit_content.MIN_TOPICS.update(minimums)


def test_no_asset_write() -> None:
    """Building must not create or modify aggregate assets."""
    out = emit_content.OUT
    before = {
        path.name: (path.stat().st_mtime_ns, path.stat().st_size)
        for path in out.glob("*.json")
    } if out.exists() else {}
    emit_content.build()
    after = {
        path.name: (path.stat().st_mtime_ns, path.stat().st_size)
        for path in out.glob("*.json")
    } if out.exists() else {}
    assert before == after, (before, after)


def main() -> int:
    tests = [
        test_catalog_target_counts,
        test_ids_preserve_baseline_and_continue,
        test_lesson_example_mapping_and_distinctness,
        test_marker_injected_exactly_once,
        test_marker_not_swallowed_by_comment_after_body,
        test_marker_recognises_case_and_whitespace_end_tags,
        test_marker_skips_text_regions,
        test_shipped_template_lessons_anchor_at_real_body_end,
        test_plaintext_document_has_no_structural_anchor,
        test_marker_ignores_body_tag_inside_script,
        test_later_body_lookalikes_do_not_duplicate_marker,
        test_marker_fallbacks,
        test_gate_rejects_below_target,
        test_no_asset_write,
    ]
    for test in tests:
        test()
        print(f"ok  {test.__name__}")
    print(
        "PASS: catalog 160/160/161=481, preserved ids, lesson/example mapping, "
        "distinct bodies, single tokenizer-aware marker (comments, quoted "
        "attributes, raw text/RCDATA, template content and case/whitespace end "
        "tags), target gate, no asset writes"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
