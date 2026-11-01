"""Read-only static checks for the repaired HTML lessons (135, 144, 160)."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "scripts"))

import py_compile  # noqa: E402

py_compile.compile(str(REPO / "scripts/curriculum/html_expansion.py"), doraise=True)

from curriculum import html_expansion as h  # noqa: E402

print("compile ok, entries", len(h.HTML_EXTRA), "| unique code:", len({x["code"] for x in h.HTML_EXTRA}) == 60)
for idx in (34, 43, 59):
    lesson = h.HTML_EXTRA[idx]
    code = lesson["code"]
    print(
        "html-example-%03d" % (idx + 101),
        "| viewport meta:", 'content="width=device-width, initial-scale=1"' in code,
        "| complete:", code.rstrip().endswith("</html>"),
        "| pitfalls:", len(lesson["pit"]),
        "| title:", lesson["t"],
    )
