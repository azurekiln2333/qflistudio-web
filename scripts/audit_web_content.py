#!/usr/bin/env python3
"""WebForge content auditor.

Audits the HTML/CSS/JavaScript tutorial and example content that WebForge
actually reads. Two modes:

  --shared   audit the shared core aggregate assets (default when run with no
             --product flag), i.e. qfli_studio_core/assets/content/*.json.
  --product  audit WebForge's own assets/content/*.json.

Checks: schema shape, required fields, scope-unique ids, cross-reference
integrity (example.sourceLessonId -> tutorial lesson id), placeholder and
template detection (title/explain/code/output uniqueness, normalised-body
duplication), and per-type counts.

Exit code is non-zero when any hard issue is found. Output is Markdown when
--report is given, otherwise a short summary.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
SHARED = REPO.parent / "qfli_studio_core" / "assets" / "content"
PRODUCT = REPO / "assets" / "content"
WEB_TYPES = ("html", "css", "javascript")


def topic_of(entry: dict) -> str:
    """Delivered entries use type=html; the topic lives in `language`."""
    return (entry.get("language") or entry.get("topic") or entry.get("type") or "").lower()

_WS = re.compile(r"\s+")
_NUM = re.compile(r"\d+")


def normalise(text: str) -> str:
    """Whitespace-collapsed, digit-masked body used for duplicate detection."""
    return _NUM.sub("N", _WS.sub(" ", text)).strip()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def web_entries(doc: dict[str, Any]) -> list[dict[str, Any]]:
    return [e for e in doc.get("entries", []) if topic_of(e) in WEB_TYPES]


def missing(entry: dict[str, Any], fields: tuple[str, ...]) -> list[str]:
    out = []
    for f in fields:
        v = entry.get(f)
        if v is None or (isinstance(v, str) and not v.strip()) or (
            isinstance(v, list) and not v
        ):
            out.append(f)
    return out


def audit(root: Path, label: str) -> tuple[list[str], dict[str, Any]]:
    issues: list[str] = []
    stats: dict[str, Any] = {"label": label, "root": str(root)}
    tut_path = root / "tutorials.json"
    ex_path = root / "examples.json"
    for p in (tut_path, ex_path):
        if not p.exists():
            issues.append(f"missing asset {p}")
    if issues:
        return issues, stats

    tut = load(tut_path)
    ex = load(ex_path)
    if tut.get("schemaVersion") != 1:
        issues.append(f"tutorials schemaVersion != 1: {tut.get('schemaVersion')}")
    if ex.get("schemaVersion") != 1:
        issues.append(f"examples schemaVersion != 1: {ex.get('schemaVersion')}")

    wt = web_entries(tut)
    we = web_entries(ex)
    stats["tutorials"] = len(wt)
    stats["examples"] = len(we)

    # --- ids unique within this document set ---
    ids: dict[str, str] = {}
    for i, e in enumerate(wt):
        eid = e.get("id", "")
        if eid in ids:
            issues.append(f"duplicate tutorial id {eid!r} at [{i}]")
        ids[eid] = "tutorial"

    lesson_ids: set[str] = set()
    explanations: list[str] = []
    outputs: list[str] = []
    titles: list[str] = []
    concepts: dict[str, int] = {}
    type_counts: dict[str, int] = {t: 0 for t in WEB_TYPES}
    for i, e in enumerate(wt):
        t = topic_of(e)
        if t in type_counts:
            type_counts[t] += 1
        for f in missing(
            e,
            ("id", "language", "type", "locale", "level", "title", "summary",
             "concepts", "source", "license", "updatedAt"),
        ):
            issues.append(f"tutorial[{i}] {e.get('id')} missing {f}")
        titles.append(e.get("title", ""))
        for c in e.get("concepts", []):
            concepts[c] = concepts.get(c, 0) + 1
        lessons = e.get("lessons") or []
        if not lessons:
            issues.append(f"tutorial[{i}] {e.get('id')} has no lessons")
        for j, l in enumerate(lessons):
            lid = l.get("id", "")
            if lid in lesson_ids:
                issues.append(f"duplicate lesson id {lid!r}")
            lesson_ids.add(lid)
            for f in missing(
                l, ("id", "title", "summary", "explain", "code", "output", "concepts")
            ):
                issues.append(f"tutorial {e.get('id')} lesson[{j}] missing {f}")
            explanations.append(l.get("explain", ""))
            outputs.append(l.get("output", ""))

    # --- examples ---
    ex_ids: set[str] = set()
    ex_titles: list[str] = []
    ex_bodies: list[str] = []
    ex_type_counts: dict[str, int] = {t: 0 for t in WEB_TYPES}
    linked = 0
    for i, e in enumerate(we):
        t = topic_of(e)
        if t in ex_type_counts:
            ex_type_counts[t] += 1
        eid = e.get("id", "")
        if eid in ex_ids:
            issues.append(f"duplicate example id {eid!r} at [{i}]")
        ex_ids.add(eid)
        for f in missing(
            e,
            ("id", "language", "type", "locale", "level", "title", "summary",
             "concepts", "source", "license", "updatedAt", "code",
             "templateType"),
        ):
            issues.append(f"example[{i}] {eid} missing {f}")
        ex_titles.append(e.get("title", ""))
        ex_bodies.append(e.get("code", ""))
        src = e.get("sourceLessonId")
        if src:
            linked += 1
            if src not in lesson_ids:
                issues.append(f"example {eid} sourceLessonId {src!r} not found")

    # --- placeholder / template detection ---
    def uniqueness(values: list[str]) -> tuple[int, int]:
        nonempty = [v for v in values if v]
        return len(set(nonempty)), len(nonempty)

    stats["unique"] = {
        "tutorial_titles": uniqueness(titles),
        "explain": uniqueness(explanations),
        "lesson_output": uniqueness(outputs),
        "example_titles": uniqueness(ex_titles),
        "example_bodies": uniqueness(ex_bodies),
    }
    stats["type_counts"] = type_counts
    stats["example_type_counts"] = ex_type_counts
    stats["linked_examples"] = linked
    stats["normalised_example_bodies"] = len({normalise(b) for b in ex_bodies})
    stats["normalised_lesson_code"] = len(
        {normalise(l.get("code", "")) for e in wt for l in e.get("lessons", [])}
    )
    stats["normalised_titles"] = len({normalise(t) for t in titles})
    stats["normalised_example_titles"] = len({normalise(t) for t in ex_titles})
    for key, vals in (
        ("normalised tutorial titles", titles),
        ("normalised example titles", ex_titles),
    ):
        uniq = len({normalise(v) for v in vals})
        if uniq < len(vals):
            issues.append(
                f"placeholder: {key} only {uniq}/{len(vals)} unique "
                "after number normalisation"
            )
    stats["distinct_concepts"] = len(concepts)
    stats["concept_top"] = sorted(concepts.items(), key=lambda kv: -kv[1])[:8]

    # hard placeholder rules
    for key, (uniq, total) in stats["unique"].items():
        if total and uniq < total:
            issues.append(
                f"placeholder: {key} only {uniq}/{total} unique"
            )
    if stats["normalised_example_bodies"] < len(ex_bodies):
        issues.append(
            "placeholder: example bodies duplicate after number normalisation "
            f"({stats['normalised_example_bodies']}/{len(ex_bodies)})"
        )
    return issues, stats


def markdown(stats: dict[str, Any], issues: list[str]) -> str:
    u = stats["unique"]
    lines = [f"## {stats['label']}", "", f"- root: `{stats['root']}`",
             f"- web tutorials: {stats['tutorials']}",
             f"- web examples: {stats['examples']}",
             f"- distinct concepts: {stats['distinct_concepts']}",
             f"- linked examples: {stats['linked_examples']}",
             f"- normalised unique example bodies: "
             f"{stats['normalised_example_bodies']}/{stats['examples']}",
             f"- normalised unique lesson code: {stats['normalised_lesson_code']}",
             f"- normalised unique tutorial titles: "
             f"{stats['normalised_titles']}/{stats['tutorials']}",
             f"- normalised unique example titles: "
             f"{stats['normalised_example_titles']}/{stats['examples']}",
             "", "| metric | unique/total |", "| --- | --- |"]
    for k, (uniq, total) in u.items():
        lines.append(f"| {k} | {uniq}/{total} |")
    lines += ["", "| type | tutorials | examples |", "| --- | --- | --- |"]
    for t in WEB_TYPES:
        lines.append(
            f"| {t} | {stats['type_counts'][t]} | {stats['example_type_counts'][t]} |"
        )
    lines += ["", "Top concepts: " + ", ".join(
        f"{c}({n})" for c, n in stats["concept_top"])]
    lines += ["", f"Issues: {len(issues)}"]
    for i in issues:
        lines.append(f"- {i}")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shared", action="store_true")
    ap.add_argument("--product", action="store_true")
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()
    if not args.shared and not args.product:
        args.shared = True

    chunks = []
    total_issues = 0
    if args.shared:
        issues, stats = audit(SHARED, "Shared core assets (baseline audit)")
        total_issues += len(issues)
        chunks.append(markdown(stats, issues))
    if args.product:
        issues, stats = audit(PRODUCT, "WebForge product assets")
        total_issues += len(issues)
        chunks.append(markdown(stats, issues))

    out = "\n".join(chunks)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(out, encoding="utf-8")
    print(out)
    return 1 if total_issues else 0


if __name__ == "__main__":
    sys.exit(main())
