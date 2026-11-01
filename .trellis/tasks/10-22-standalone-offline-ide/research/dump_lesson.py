"""Dump the curriculum entry for given css-example-NNN ids (baseline only).

Usage: python -X utf8 dump_lesson.py 011 044 ...
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repo / "scripts"))

from curriculum import (  # noqa: E402
    css_data,
    css_data2,
    css_data3,
    css_data4,
    css_data5,
    supplement,
)

base = (
    css_data.CSS
    + css_data2.CSS2
    + css_data3.CSS3
    + css_data4.CSS4
    + css_data5.CSS5
    + supplement.CSS6
)

want = {int(a) for a in sys.argv[1:]}
for index, lesson in enumerate(base, start=1):
    if index in want:
        print("=" * 70)
        print(f"css-example-{index:03d}  {lesson['t']}")
        print("-" * 70)
        print(lesson["code"])
        print("-" * 70)
        print("OUT:", lesson["out"])
