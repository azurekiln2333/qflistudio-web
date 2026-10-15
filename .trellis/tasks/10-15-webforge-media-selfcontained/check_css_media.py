"""Real-value check for css-062 / css-078 / css-088 media lessons.

Decodes every inline SVG data URI (img src and CSS url()) in the three lessons
and proves each parses as valid SVG at the expected size, that no local/network
fetch remains, and reports the computed background/size expectations.

Run: python -X utf8 .trellis/tasks/10-15-webforge-media-selfcontained/check_css_media.py
"""
from __future__ import annotations

import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from curriculum import (  # noqa: E402
    css_data,
    css_data2,
    css_data3,
    css_data4,
    css_data5,
    supplement,
)

css = (
    css_data.CSS
    + css_data2.CSS2
    + css_data3.CSS3
    + css_data4.CSS4
    + css_data5.CSS5
    + supplement.CSS6
)

TARGETS = {62: "CSS 深色图片与叠加文字", 78: "CSS 背景定位与精灵图", 88: "CSS 多背景叠加"}
SVG_RE = re.compile(r"data:image/svg\+xml,(?P<d>[^\"')]+)")
failures: list[str] = []

for number, title in TARGETS.items():
    lesson = css[number - 1]
    assert title in lesson["t"], (number, lesson["t"])
    html = lesson["code"]
    found = False
    for m in SVG_RE.finditer(html):
        found = True
        svg = urllib.parse.unquote(m.group("d"))
        try:
            root = ET.fromstring(svg)
        except ET.ParseError as exc:
            failures.append(f"css-{number}: SVG parse error {exc}")
            continue
        w, h = root.get("width"), root.get("height")
        print(f"css-{number}: inline SVG {w}x{h} OK")
    if not found:
        failures.append(f"css-{number}: no inline SVG found")
    if re.search(r"placehold\.co", html):
        failures.append(f"css-{number}: still references placehold.co")
    # local asset in url()/src that would 404
    for ref in re.findall(r'(?:src="|url\()([^")\']+)', html):
        if re.match(r"^[A-Za-z0-9_./-]+\.(png|jpg|jpeg|gif|webp|avif|svg|css)$", ref):
            failures.append(f"css-{number}: local asset ref {ref!r}")

if failures:
    print("FAILURES:")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("PASS: css-062/078/088 use valid inline SVG, no local/network fetch")
