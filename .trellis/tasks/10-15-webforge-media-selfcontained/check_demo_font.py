"""Validate the generated demo WOFF2 is a real, loadable font.

Confirms: WOFF2 signature, upem, non-empty outlines for each drawn glyph, and
that the cmap covers every character of "WebForge".

Run: PYTHONPATH=.trellis/.runtime/font-tools python -X utf8 \
        .trellis/tasks/10-15-webforge-media-selfcontained/check_demo_font.py
"""
from __future__ import annotations

import base64
import io
import re
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

REPO = Path(__file__).resolve().parents[3]
src = (REPO / "scripts" / "curriculum" / "css_data5.py").read_text(encoding="utf-8")
m = re.search(r"data:font/woff2;base64,([A-Za-z0-9+/=]+)", src)
if not m:
    print("FAIL: no data:font/woff2 found in css_data5.py")
    sys.exit(1)
raw = base64.b64decode(m.group(1))
print(f"bytes={len(raw)} magic={raw[:4]!r}")
if raw[:4] != b"wOF2":
    print("FAIL: not a WOFF2 container")
    sys.exit(1)

font = TTFont(io.BytesIO(raw))
glyf = font["glyf"]
cmap = font.getBestCmap()
need = "WebForge"
missing = [c for c in need if ord(c) not in cmap]
if missing:
    print("FAIL: cmap missing", missing)
    sys.exit(1)

empty = []
for ch in sorted(set(need)):
    name = cmap[ord(ch)]
    g = glyf[name]
    n = len(g.getCoordinates(glyf)[0]) if g.numberOfContours else 0
    if n == 0:
        empty.append(ch)
    else:
        print(f"  {ch!r} -> {name}: {n} points")
if empty:
    print("FAIL: empty outlines for", empty)
    sys.exit(1)

print(f"PASS: real WOFF2, upem={font['head'].unitsPerEm}, "
      f"covers {need!r} with drawn glyphs")
