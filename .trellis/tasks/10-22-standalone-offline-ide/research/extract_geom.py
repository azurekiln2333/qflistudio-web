"""Extract the geometry assertions from css_expansion_assertions.mjs cases."""
import re
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[4]
src = (repo / "scripts/css_expansion_assertions.mjs").read_text(encoding="utf-8")

ids = sys.argv[1:]
for case in ids:
    pattern = re.compile(
        r"CSS_CASES\.set\('css-example-" + case + r"'.*?(?=\nCSS_CASES\.set\()", re.S
    )
    match = pattern.search(src)
    if not match:
        print(f"### css-example-{case}: not found")
        continue
    print(f"### css-example-{case}")
    for line in match.group(0).split("\n"):
        stripped = line.strip()
        if any(token in stripped for token in ("box(", "=== 1", "=== 2", "=== 3", "=== 4", "=== 6", "=== 8", "=== 5")):
            print("   ", stripped[:200])
    print()
