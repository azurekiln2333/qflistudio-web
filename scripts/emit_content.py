#!/usr/bin/env python3
"""Emit WebForge's product-owned curriculum JSON from authored data modules.

Reads the three language data modules (shipped baseline plus the authored
`*_expansion` modules), builds 481 matched tutorials and one derived example per
tutorial — 160 HTML, 160 CSS and 161 JavaScript — and writes:

  assets/content/tutorials.json
  assets/content/examples.json

Every delivered document is a complete, self-contained, browser-previewable
HTML page. Each carries exactly one `webforge-check` marker element, injected
before the document's real closing `</body>` while ignoring any `</body>` that
appears inside a `<script>` body; the Playwright runner uses it only as a
cross-cutting sanity check (the page loaded and was not replaced). Semantic
verification is the job of the per-example oracles:
`scripts/js_example_assertions.mjs`, `scripts/js_expansion_assertions.mjs`
(JavaScript) and `scripts/web_markup_assertions.mjs` (HTML/CSS). The marker is
never the sole or authoritative assertion.

Run: python -X utf8 scripts/emit_content.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from curriculum import (  # noqa: E402
    html_data,
    html_data2,
    html_data3,
    html_data4,
    css_data,
    css_data2,
    css_data3,
    css_data4,
    css_data5,
    js_data,
    js_data2,
    js_data3,
    js_data4,
    js_data5,
    supplement,
    html_expansion,
    css_expansion,
    js_expansion,
)
from curriculum.common import LICENSE, SOURCE, UPDATED  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "assets" / "content"

LANGUAGES = {
    "html": html_data.HTML
    + html_data2.HTML2
    + html_data3.HTML3
    + html_data4.HTML4
    + supplement.HTML5
    + html_expansion.HTML_EXTRA,
    "css": css_data.CSS
    + css_data2.CSS2
    + css_data3.CSS3
    + css_data4.CSS4
    + css_data5.CSS5
    + supplement.CSS6
    + css_expansion.CSS_EXTRA,
    "javascript": js_data.JS
    + js_data2.JS2
    + js_data3.JS3
    + js_data4.JS4
    + js_data5.JS5
    + js_expansion.JS_EXTRA,
}

# Catalog target: 160 HTML + 160 CSS + 161 JavaScript = 481 matched topics.
# The shipped baseline occupied 100/100/101, so authored expansions continue at
# html-example-101, css-example-101 and js-example-102.
MIN_TOPICS = {"html": 160, "css": 160, "javascript": 161}
MIN_TOTAL = sum(MIN_TOPICS.values())

ID_PREFIX = {"html": "html", "css": "css", "javascript": "js"}

# Every delivered example/lesson is a complete, standalone, browser-previewable
# HTML document. The content `type` is therefore always `html` so the shared
# CodeImportService suggests `index.html`, creates an HTML project and previews
# it. The topic (html/css/javascript) is preserved in `language` metadata and in
# the asset layout.
DELIVERY_TYPE = "html"


def slug_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# Example generation
# ---------------------------------------------------------------------------

CHECK_MARKER = "webforge-check"

# A lesson document may legitimately contain the text `</body>` in places where
# a browser tokenizer would treat it as plain text: inside a `<script>` string, a
# `<style>` block, a `<textarea>`/`<title>`, an HTML comment, a quoted attribute
# value, or `<template>` content. Only a *real* structural end tag may receive the
# marker, otherwise the marker is either swallowed (comment) or injected into
# JavaScript/CSS source and breaks the page.
_RAWTEXT_ELEMENTS = frozenset(
    # Content is raw text: no markup is recognised until the matching end tag.
    # `noscript` belongs here because delivered pages run with scripting enabled.
    {"script", "style", "xmp", "iframe", "noembed", "noframes", "noscript"}
)
_RCDATA_ELEMENTS = frozenset({"textarea", "title"})
_STRUCTURAL_END_TAGS = ("body", "html")

_TAG_NAME = re.compile(r"[A-Za-z][^\s/>]*")


def _skip_tag_tail(code: str, index: int) -> int:
    """Return the offset just past a tag's closing `>`, honouring quotes.

    Quoted attribute values are skipped so `<div title="</body>">` is not
    mistaken for a structural end tag.
    """
    quote = ""
    length = len(code)
    while index < length:
        char = code[index]
        if quote:
            if char == quote:
                quote = ""
        elif char in "\"'":
            quote = char
        elif char == ">":
            return index + 1
        index += 1
    return length


def _raw_text_close(code: str, index: int, name: str) -> int:
    """Return the offset of the `</name` that closes a raw text/RCDATA element."""
    pattern = re.compile(r"</" + re.escape(name) + r"(?=[\s/>])", re.IGNORECASE)
    match = pattern.search(code, index)
    return match.start() if match else len(code)


def structural_end_tag_offsets(code: str) -> dict[str, int]:
    """Map `body`/`html` to the offset of their last *real* end tag.

    A real end tag is one the HTML tokenizer would actually emit for the document
    structure, so the scan skips:

    * comments (`<!-- … -->`) and bogus comments (`<!…>`, `<?…>`),
    * quoted attribute values inside start tags,
    * raw text elements (`script`, `style`, `noscript`, …) and RCDATA elements
      (`textarea`, `title`), whose content is text rather than markup,
    * the content of `<template>` elements, which belongs to a separate fragment.

    End tags are matched case-insensitively and tolerate whitespace or a stray
    solidus before `>` (`</BODY >`, `</body/>`). Returned offsets index the
    original string, so callers can splice without rewriting surrounding bytes.
    """
    offsets: dict[str, int] = {}
    length = len(code)
    index = 0
    template_depth = 0

    while index < length:
        open_at = code.find("<", index)
        if open_at == -1:
            break
        index = open_at

        if code.startswith("<!--", index):
            close = code.find("-->", index + 4)
            index = length if close == -1 else close + 3
            continue

        if code.startswith("<!", index) or code.startswith("<?", index):
            index = _skip_tag_tail(code, index + 2)
            continue

        if code.startswith("</", index):
            match = _TAG_NAME.match(code, index + 2)
            if not match:
                index += 1
                continue
            name = match.group(0).lower()
            if name == "template":
                if template_depth:
                    template_depth -= 1
            elif template_depth == 0 and name in _STRUCTURAL_END_TAGS:
                offsets[name] = index
            index = _skip_tag_tail(code, match.end())
            continue

        match = _TAG_NAME.match(code, index + 1)
        if not match:
            # A stray `<` that cannot begin a tag is text.
            index += 1
            continue
        name = match.group(0).lower()
        index = _skip_tag_tail(code, match.end())
        if name == "template":
            template_depth += 1
        elif name == "plaintext":
            # Everything after <plaintext> is text by definition.
            index = length
        elif name in _RAWTEXT_ELEMENTS or name in _RCDATA_ELEMENTS:
            index = _raw_text_close(code, index, name)

    return offsets


def _insert_check_marker(code: str, marker: str = CHECK_MARKER) -> str:
    """Insert exactly one hidden check marker into a complete HTML document.

    The marker goes immediately before the document's real closing `</body>`
    (preferred) or `</html>`. Occurrences a browser would treat as text — inside
    comments, quoted attributes, raw text/RCDATA elements or `<template>` content
    — are ignored. Documents without a real structural end tag get the marker
    appended. Existing bytes are never rewritten.
    """
    snippet = f'  <output id="{marker}" hidden>ok</output>\n'
    offsets = structural_end_tag_offsets(code)
    for name in _STRUCTURAL_END_TAGS:
        at = offsets.get(name)
        if at is not None:
            return code[:at] + snippet + code[at:]
    return code + "\n" + snippet


def example_document(language: str, lesson: dict) -> tuple[str, str]:
    """Return (code, marker) where marker is asserted by the runner."""
    code = lesson["code"]
    marker = CHECK_MARKER

    if language == "html":
        # HTML lessons are already complete documents; add only the marker.
        return _insert_check_marker(code, marker), marker

    if language == "css":
        # CSS lessons are already complete documents with a <style> block and
        # matching markup, so they are directly previewable. Add only the
        # check marker.
        return _insert_check_marker(code, marker), marker

    # javascript: the lesson is already a complete document containing its own
    # <script>; add only the marker element.
    return _insert_check_marker(code, marker), marker


# ---------------------------------------------------------------------------
# Build entries
# ---------------------------------------------------------------------------

def build() -> tuple[list[dict], list[dict]]:
    tutorials: list[dict] = []
    examples: list[dict] = []
    counters = {lang: 0 for lang in LANGUAGES}

    for language, lessons in LANGUAGES.items():
        prefix = ID_PREFIX[language]
        for lesson in lessons:
            counters[language] += 1
            n = counters[language]
            tid = f"{prefix}-tutorial-{n:03d}"
            lesson_id = f"{tid}-lesson"
            summary = slug_text(lesson["obj"])
            concepts = list(dict.fromkeys(lesson["con"]))

            # The lesson's delivered code is the same complete, previewable HTML
            # document as its example, so importing a tutorial lesson also yields
            # a runnable web page rather than a bare CSS/JS fragment.
            doc, marker = example_document(language, lesson)

            tutorials.append(
                {
                    "id": tid,
                    "language": language,
                    "type": DELIVERY_TYPE,
                    "topic": language,
                    "locale": "zh-CN",
                    "level": lesson["level"],
                    "title": f"{lesson['t']}",
                    "summary": summary,
                    "concepts": concepts,
                    "source": SOURCE,
                    "license": LICENSE,
                    "updatedAt": UPDATED,
                    "lessons": [
                        {
                            "id": lesson_id,
                            "title": lesson["t"],
                            "summary": summary,
                            "concepts": concepts,
                            "objective": lesson["obj"],
                            "prerequisites": lesson["pre"],
                            "explain": lesson["explain"],
                            "code": doc,
                            "output": lesson["out"],
                            "pitfalls": lesson["pit"],
                            "exercises": [
                                {"prompt": p, "hint": h, "answer": a}
                                for (p, h, a) in lesson["ex"]
                            ],
                        }
                    ],
                }
            )

            eid = f"{prefix}-example-{n:03d}"
            examples.append(
                {
                    "id": eid,
                    "language": language,
                    "type": DELIVERY_TYPE,
                    "topic": language,
                    "locale": "zh-CN",
                    "level": lesson["level"],
                    "title": f"示例：{lesson['t']}",
                    "summary": f"可运行的 {language.upper()} 示例，验证：{summary}",
                    "concepts": concepts,
                    "source": SOURCE,
                    "license": LICENSE,
                    "updatedAt": UPDATED,
                    "code": doc,
                    "expectedOutput": lesson["out"],
                    "inputFixtures": {},
                    "templateType": DELIVERY_TYPE,
                    "sourceLessonId": lesson_id,
                    "checkMarker": marker,
                }
            )
    return tutorials, examples


def main() -> int:
    tutorials, examples = build()
    OUT.mkdir(parents=True, exist_ok=True)

    def write(path: Path, kind: str, entries: list[dict]) -> None:
        document = {
            "schemaVersion": 1,
            "kind": kind,
            "product": "webforge",
            "updatedAt": UPDATED,
            "entries": entries,
        }
        path.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    write(OUT / "tutorials.json", "tutorials", tutorials)
    write(OUT / "examples.json", "examples", examples)

    counts: dict[str, int] = {}
    topics: dict[str, int] = {}
    for t in tutorials:
        counts[t["type"]] = counts.get(t["type"], 0) + 1
        topics[t["language"]] = topics.get(t["language"], 0) + 1
    print(f"tutorials: {len(tutorials)} types={counts} topics={topics}")
    ex_topics: dict[str, int] = {}
    for e in examples:
        ex_topics[e["language"]] = ex_topics.get(e["language"], 0) + 1
    print(f"examples: {len(examples)} topics={ex_topics}")

    missing_topics = {
        lang: (topics.get(lang, 0), minimum)
        for lang, minimum in MIN_TOPICS.items()
        if topics.get(lang, 0) < minimum
    }
    if missing_topics:
        print(f"ERROR: topic count below target (actual, required): {missing_topics}")
    ok = (
        len(tutorials) >= MIN_TOTAL
        and len(examples) >= MIN_TOTAL
        and not missing_topics
        and all(t["type"] == DELIVERY_TYPE for t in tutorials)
        and all(e["type"] == DELIVERY_TYPE for e in examples)
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
