#!/usr/bin/env python3
"""Stage exact product catalogs in the test-only OHOS rawfile source set.

Run after catalog generation, or use --check to reject stale staging.
No example source or missing companion resource is synthesized.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "ohos/entry/src/ohosTest/resources/rawfile/ohos_catalog"


def inventory(examples: dict, tutorials: dict) -> dict[str, int]:
    for name, document in (("examples", examples), ("tutorials", tutorials)):
        if document.get("schemaVersion") != 1 or not isinstance(document.get("entries"), list):
            raise ValueError(f"{name}: expected schemaVersion 1 and entries array")
        if not document["entries"]:
            raise ValueError(f"{name}: refusing an empty catalog")
        ids = [entry.get("id") for entry in document["entries"]]
        if any(not isinstance(key, str) or not key for key in ids) or len(set(ids)) != len(ids):
            raise ValueError(f"{name}: missing or duplicate entry ID")
    lessons = {}
    for tutorial in tutorials["entries"]:
        if not isinstance(tutorial.get("lessons"), list) or not tutorial["lessons"]:
            raise ValueError(f"{tutorial['id']}: missing lessons")
        for lesson in tutorial["lessons"]:
            key = lesson.get("id")
            if not isinstance(key, str) or not key or key in lessons:
                raise ValueError(f"{tutorial['id']}: missing or duplicate lesson ID")
            lessons[key] = lesson
    covered = set()
    for example in examples["entries"]:
        if example.get("type") != "html" or not isinstance(example.get("code"), str) or not example["code"].strip():
            raise ValueError(f"{example['id']}: expected independently runnable HTML document")
        lesson = lessons.get(example.get("sourceLessonId"))
        if lesson is None or lesson.get("code") != example["code"]:
            raise ValueError(f"{example['id']}: missing or source-mismatched tutorial lesson")
        if example["sourceLessonId"] in covered:
            raise ValueError(f"{example['id']}: multiple examples map to one lesson")
        covered.add(example["sourceLessonId"])
    if covered != set(lessons):
        raise ValueError("tutorial lesson inventory and example inventory differ")
    if len(examples["entries"]) > 45536:
        raise ValueError("example inventory exceeds unique-origin ports20000..65535")
    return {"examples": len(examples["entries"]), "tutorials": len(tutorials["entries"]), "lessons": len(lessons)}


def staged_files(root: Path) -> dict[str, bytes]:
    sources = {name: root / "assets/content" / f"{name}.json" for name in ("examples", "tutorials")}
    payloads = {name: source.read_bytes() for name, source in sources.items()}
    documents = {name: json.loads(data.decode("utf-8")) for name, data in payloads.items()}
    counts = inventory(documents["examples"], documents["tutorials"])
    manifest = {
        "schemaVersion": 1,
        "kind": "qfli-ohos-catalog",
        "files": {
            name: {"path": f"ohos_catalog/{name}.json", "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in payloads.items()
        },
        "counts": counts,
    }
    if any(source.read_bytes() != payloads[name] for name, source in sources.items()):
        raise ValueError("product catalogs changed during preparation; retry after generation completes")
    return {**{f"{name}.json": data for name, data in payloads.items()},
            "manifest.json": (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")}


def atomic_write(path: Path, payload: bytes) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify exact current staging without writing")
    args = parser.parse_args()
    try:
        files = staged_files(ROOT)
        if args.check:
            stale = [name for name, payload in files.items()
                     if not (OUTPUT / name).is_file() or (OUTPUT / name).read_bytes() != payload]
            if stale:
                raise ValueError("missing/stale test-only catalogs: " + ", ".join(stale))
        else:
            OUTPUT.mkdir(parents=True, exist_ok=True)
            for name, payload in files.items():
                atomic_write(OUTPUT / name, payload)
        manifest = json.loads(files["manifest.json"])
        print(json.dumps({"action": "checked" if args.check else "prepared", "output": str(OUTPUT), **manifest},
                         ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print(f"OHOS catalog preparation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
