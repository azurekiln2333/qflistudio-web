"""Integration dry run: where would CSS_EXTRA land in emit_content.py's ids?

Reproduces emit_content.build() ordering without touching the generator: the css
language list is (css_data + css_data2 + ... + css_data5 + supplement.CSS6 +
css_expansion.CSS_EXTRA), so the first expanded entry must be index 100 ->
css-tutorial-101 / css-example-101, and the last 160.

Run: python -X utf8 .trellis/tasks/10-22-standalone-offline-ide/research/check_ids.py
"""
from __future__ import annotations

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
    css_expansion,
    supplement,
)

baseline = (
    css_data.CSS
    + css_data2.CSS2
    + css_data3.CSS3
    + css_data4.CSS4
    + css_data5.CSS5
    + supplement.CSS6
)
expanded = baseline + css_expansion.CSS_EXTRA

print(f"baseline css entries: {len(baseline)}")
print(f"expansion entries:    {len(css_expansion.CSS_EXTRA)}")
print(f"combined css entries: {len(expanded)}")

problems = []
if len(baseline) != 100:
    problems.append(f"baseline is {len(baseline)}, expected 100")
if len(expanded) != 160:
    problems.append(f"combined is {len(expanded)}, expected 160")

# The first expanded entry must be number 101 and the last 160.
first_id = f"css-example-{len(baseline) + 1:03d}"
last_id = f"css-example-{len(expanded):03d}"
print(f"first expansion id:   {first_id}")
print(f"last expansion id:    {last_id}")
if first_id != "css-example-101":
    problems.append(f"first id would be {first_id}")
if last_id != "css-example-160":
    problems.append(f"last id would be {last_id}")

# No title or document body may collide with the shipped 100.
baseline_titles = {lesson["t"] for lesson in baseline}
baseline_bodies = {lesson["code"] for lesson in baseline}
for index, lesson in enumerate(css_expansion.CSS_EXTRA, start=101):
    if lesson["t"] in baseline_titles:
        problems.append(f"css-example-{index}: title collides with baseline: {lesson['t']}")
    if lesson["code"] in baseline_bodies:
        problems.append(f"css-example-{index}: document body identical to a baseline lesson")

oracle_ids = None
oracle_path = repo / "scripts" / "css_expansion_assertions.mjs"
print(f"oracle module:        {oracle_path.name}")

if problems:
    print("PROBLEMS:")
    for p in problems:
        print(" -", p)
    raise SystemExit(1)
print("OK: append-last integration yields css-example-101..160 with no collisions")
