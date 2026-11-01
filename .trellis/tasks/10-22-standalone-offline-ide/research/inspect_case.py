"""Show the oracle code and lesson source for given css-example ids.

Usage: python -X utf8 inspect_case.py 031 114 ...
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[4]

JSON = repo / ".trellis/tasks/10-22-standalone-offline-ide/research/ohos-481-initial.json"
ORACLE_BASE = repo / "scripts/web_markup_assertions.mjs"
ORACLE_EXP = repo / "scripts/css_expansion_assertions.mjs"

fails = {}
doc = json.loads(JSON.read_text(encoding="utf-8"))
for result in doc["results"]:
    if result.get("pass"):
        continue
    fails[result["id"]] = result["failed"]


def oracle_block(path: Path, case_id: str) -> str:
    src = path.read_text(encoding="utf-8")
    marker = f"CSS_CASES.set('{case_id}'"
    start = src.find(marker)
    if start < 0:
        return "<not in this module>"
    end = src.find("\nCSS_CASES.set(", start + 1)
    if end < 0:
        end = len(src)
    return src[start:end].rstrip()


def lesson_source(entry: dict) -> str:
    code = entry["code"]
    style = re.search(r"<style>(.*?)</style>", code, re.S)
    body = re.search(r"<body[^>]*>(.*?)</body>", code, re.S)
    out = []
    if style:
        out.append("STYLE:")
        out.append(style.group(1).strip())
    if body:
        out.append("BODY:")
        out.append(body.group(1).strip()[:1200])
    return "\n".join(out)


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

base = (
    css_data.CSS
    + css_data2.CSS2
    + css_data3.CSS3
    + css_data4.CSS4
    + css_data5.CSS5
    + supplement.CSS6
)
all_lessons = list(base) + list(css_expansion.CSS_EXTRA)

for arg in sys.argv[1:]:
    num = int(arg)
    case_id = f"css-example-{num:03d}"
    lesson = all_lessons[num - 1]
    print("=" * 78)
    print(f"{case_id}  {lesson['t']}")
    print("FAILED CHECKS:")
    for f in fails.get(case_id, [{"name": "<not failing in this run>", "detail": ""}]):
        print(f"  - {f['name']}  detail={f['detail']!r}")
    print("-" * 78)
    print(lesson_source(lesson))
    print("-" * 78)
    print("ORACLE (baseline):")
    print(oracle_block(ORACLE_BASE, case_id))
    print("ORACLE (expansion):")
    print(oracle_block(ORACLE_EXP, case_id))
    print()
