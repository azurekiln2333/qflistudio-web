#!/usr/bin/env python3
"""Emit WebForge's product-owned curriculum JSON from authored data modules.

Reads the three language data modules, builds >=100 tutorials and one derived
example per tutorial, and writes:

  assets/content/tutorials.json
  assets/content/examples.json

Every delivered document is a complete, self-contained, browser-previewable
HTML page. Each carries a `webforge-check` marker element, which the Playwright
runner uses only as a cross-cutting sanity check (the page loaded and was not
replaced). Semantic verification is the job of the per-example oracles:
`scripts/js_example_assertions.mjs` (JavaScript) and
`scripts/web_markup_assertions.mjs` (HTML/CSS). The marker is never the sole or
authoritative assertion.

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
)
from curriculum.common import LICENSE, SOURCE, UPDATED  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "assets" / "content"

LANGUAGES = {
    "html": html_data.HTML
    + html_data2.HTML2
    + html_data3.HTML3
    + html_data4.HTML4
    + supplement.HTML5,
    "css": css_data.CSS
    + css_data2.CSS2
    + css_data3.CSS3
    + css_data4.CSS4
    + css_data5.CSS5
    + supplement.CSS6,
    "javascript": js_data.JS
    + js_data2.JS2
    + js_data3.JS3
    + js_data4.JS4
    + js_data5.JS5,
}

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


def example_document(language: str, lesson: dict) -> tuple[str, str]:
    """Return (code, marker) where marker is asserted by the runner."""
    code = lesson["code"]
    if language == "html":
        # HTML lessons are already complete documents; ensure there is a
        # checkable marker by appending an output element driven by a script.
        marker = "webforge-check"
        if "</body>" in code:
            doc = code.replace(
                "</body>",
                f'  <output id="{marker}" hidden>ok</output>\n</body>',
            )
        else:
            doc = code + f'\n<output id="{marker}" hidden>ok</output>'
        return doc, marker

    if language == "css":
        # CSS lessons are already complete documents with a <style> block and
        # matching markup, so they are directly previewable. Add only the
        # check marker.
        marker = "webforge-check"
        if "</body>" in code:
            doc = code.replace(
                "</body>",
                f'  <output id="{marker}" hidden>ok</output>\n</body>',
            )
        else:
            doc = code + f'\n<output id="{marker}" hidden>ok</output>'
        return doc, marker

    # javascript: the lesson is already a complete document containing its own
    # <script>; add only the marker element.
    marker = "webforge-check"
    if "<script" in code and "</body>" in code:
        return (
            code.replace(
                "</body>",
                f'  <output id="{marker}" hidden>ok</output>\n</body>',
            ),
            marker,
        )
    return code + f'\n<output id="{marker}" hidden>ok</output>', marker


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
    ok = (
        len(tutorials) >= 100
        and len(examples) >= 100
        and all(t["type"] == DELIVERY_TYPE for t in tutorials)
        and all(e["type"] == DELIVERY_TYPE for e in examples)
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
