"""Real-DOM check for the html-096 image map lesson.

Parses the exact lesson HTML, extracts the <img>, decodes its data: URI, proves
it is valid SVG at the declared 240x80 size, and verifies the <map>/<area>
hotspots still cover the image with no external/network reference.

Run: python -X utf8 .trellis/tasks/10-15-webforge-media-selfcontained/check_html096.py
"""
from __future__ import annotations

import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from curriculum import supplement  # noqa: E402

lesson = supplement.HTML5[1]  # html-096: HTML 图片地图与热点
assert lesson["t"].startswith("HTML 图片地图"), lesson["t"]
html = lesson["code"]

failures: list[str] = []

img = re.search(r"<img\b[^>]*>", html)
if not img:
    failures.append("no <img> element")
    print("FAILURES:", failures)
    sys.exit(1)
img_tag = img.group(0)

src = re.search(r'\bsrc="([^"]*)"', img_tag)
if not src:
    failures.append("<img> has no src")
else:
    value = src.group(1)
    if re.match(r"^https?://", value):
        failures.append(f"src still external: {value}")
    elif value.startswith("data:image/svg+xml,"):
        svg = urllib.parse.unquote(value[len("data:image/svg+xml,"):])
        try:
            root = ET.fromstring(svg)
        except ET.ParseError as exc:
            failures.append(f"SVG does not parse: {exc}")
            root = None
        if root is not None:
            if not root.tag.endswith("svg"):
                failures.append(f"root tag is {root.tag}, not svg")
            w = root.get("width")
            h = root.get("height")
            if (w, h) != ("240", "80"):
                failures.append(f"SVG size {w}x{h} != 240x80")
            print(f"OK img: valid inline SVG {w}x{h}")
    elif re.match(r"^[a-zA-Z0-9_./-]+$", value):
        failures.append(f"src is a local path (would 404): {value}")

if 'usemap="#m"' not in img_tag:
    failures.append("usemap/#m lost")
if not re.search(r'<map name="m">', html):
    failures.append("map name=m lost")

# Hotspot rectangles must stay within the 240x80 image.
areas = re.findall(r'<area[^>]*coords="([^"]*)"[^>]*>', html)
rects = [tuple(int(n) for n in c.split(",")) for c in areas]
for rect in rects:
    x1, y1, x2, y2 = rect
    if not (0 <= x1 < x2 <= 240 and 0 <= y1 < y2 <= 80):
        failures.append(f"area coords out of bounds: {rect}")
print(f"areas: {rects}")

# No network reference anywhere in the lesson.
if re.search(r"https?://(?!www\.w3\.org)", html):
    failures.append("lesson still contains an external http(s) reference")

if failures:
    print("FAILURES:")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("PASS: html-096 image is a valid 240x80 inline SVG, hotspots intact, no network")
