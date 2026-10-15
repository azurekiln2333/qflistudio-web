"""CSS-grammar self-containment check for the curriculum sources.

Catches the p6-confirmed defect class the earlier SVG-decoding check missed:
an *unquoted* `url(...)` whose contents contain whitespace, `"`, `'`, `(` or `)`
is dropped by CSS parsing, so the declaration never applies even though the
decoded payload is a valid SVG.

Also flags any `url()` or `@font-face src` that points at a bare local asset
(no scheme), which would 404.

Run: python -X utf8 .trellis/tasks/10-15-webforge-media-selfcontained/check_css_grammar.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SRC = REPO / "scripts" / "curriculum"
FILES = (
    sorted(SRC.glob("html_data*.py"))
    + sorted(SRC.glob("css_data*.py"))
    + [SRC / "supplement.py"]
)

# url( ... ) with optional surrounding quote. Group 1 = quote (may be empty).
URL = re.compile(r"url\(\s*(?P<q>[\"']?)(?P<v>.*?)(?P=q)\s*\)", re.S)
LOCAL_ASSET = re.compile(
    r"^[A-Za-z0-9_./-]+\.(?:png|jpe?g|gif|webp|avif|svg|ico|css|js|"
    r"mp4|webm|mp3|wav|ogg|woff2?|ttf|otf)$",
    re.I,
)


def main() -> int:
    problems: list[str] = []
    total = 0
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        for m in URL.finditer(text):
            quote = m.group("q")
            value = m.group("v")
            total += 1
            if not quote and re.search(r"[\s\"'()]", value):
                problems.append(
                    f"{path.name}: UNQUOTED url() with whitespace/special "
                    f"{value[:50]!r} — CSS drops this declaration"
                )
            if LOCAL_ASSET.match(value.strip("'\"")):
                problems.append(
                    f"{path.name}: url() -> missing local asset {value!r}"
                )
            if quote and "," in value and "data:" not in value:
                pass  # quoted multi-token url is legal CSS
    if problems:
        print("CSS GRAMMAR PROBLEMS:")
        for p in problems:
            print("  -", p)
        return 1
    print(f"OK: {total} url() refs, all CSS-valid (quoted or whitespace-free)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
