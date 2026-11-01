"""Append an oracle fragment into scripts/css_expansion_assertions.mjs.

Inserts the fragment immediately before the `/** Ids this module covers. */`
marker so COVERED_IDS keeps deriving from the case map. Used only during
authoring to keep large batches out of fragile inline edits.

Usage: python scripts/.../research/append_oracle.py <fragment.mjs>
"""
from __future__ import annotations

import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[4]
target = repo / "scripts" / "css_expansion_assertions.mjs"
marker = "/** Ids this module covers. */"

fragment = Path(sys.argv[1]).read_text(encoding="utf-8").rstrip() + "\n\n"
src = target.read_text(encoding="utf-8")
if marker not in src:
    raise SystemExit("marker missing")
if fragment.split("CSS_CASES.set('")[1][:20] in src:
    raise SystemExit("fragment already applied")
head, tail = src.split(marker, 1)
target.write_text(head + fragment + marker + tail, encoding="utf-8")
print("appended", len(fragment), "bytes")
