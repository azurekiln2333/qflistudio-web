"""Task-local dump of the 60 HTML expansion documents for browser verification.

Mirrors scripts/emit_content.py's marker injection exactly (the emitter is
root-owned and must not be run here). Writes a JSON file next to this script so
the Playwright harness can serve the real delivered documents.

Run: python -X utf8 .trellis/tasks/10-22-standalone-offline-ide/research/dump_html_expansion.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "scripts"))

from curriculum import html_expansion  # noqa: E402

MARKER = "webforge-check"


def example_document(code: str) -> str:
    """Same transformation as emit_content.example_document for HTML."""
    if "</body>" in code:
        return code.replace(
            "</body>", f'  <output id="{MARKER}" hidden>ok</output>\n</body>'
        )
    return code + f'\n<output id="{MARKER}" hidden>ok</output>'


def main() -> int:
    entries = []
    for index, lesson in enumerate(html_expansion.HTML_EXTRA, start=101):
        entries.append(
            {
                "id": f"html-example-{index:03d}",
                "language": "html",
                "type": "html",
                "title": lesson["t"],
                "code": example_document(lesson["code"]),
                "expectedOutput": lesson["out"],
            }
        )
    out = Path(__file__).resolve().parent / "html-expansion-documents.json"
    out.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(entries)} documents -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
