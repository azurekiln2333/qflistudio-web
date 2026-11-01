"""Print exact assertion lines (with line numbers) for css expansion cases."""
import re
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[4]
path = repo / "scripts/css_expansion_assertions.mjs"
lines = path.read_text(encoding="utf-8").split("\n")

starts = {}
for i, line in enumerate(lines):
    m = re.match(r"CSS_CASES\.set\('css-example-(\d+)'", line)
    if m:
        starts[m.group(1)] = i

order = sorted(starts, key=lambda k: starts[k])
for case in sys.argv[1:]:
    if case not in starts:
        print(f"### css-example-{case}: not found")
        continue
    begin = starts[case]
    idx = order.index(case)
    end = starts[order[idx + 1]] if idx + 1 < len(order) else len(lines)
    print(f"### css-example-{case} (lines {begin + 1}-{end})")
    for n in range(begin, end):
        print(f"{n + 1}: {lines[n]}")
    print()
