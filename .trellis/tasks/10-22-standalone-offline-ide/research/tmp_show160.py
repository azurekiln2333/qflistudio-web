"""Read-only: print the full current source of html-example-160 (index 59)."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "scripts"))
from curriculum import html_expansion as h  # noqa: E402

lesson = h.HTML_EXTRA[59]
print("id:", lesson["id"], "| title:", lesson["t"], "| level:", lesson.get("level"))
for key in ("obj", "explain", "out", "pit", "ex"):
    print("\n---", key, "---")
    print(lesson[key])
print("\n--- code ---")
print(lesson["code"])
