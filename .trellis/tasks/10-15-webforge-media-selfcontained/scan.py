"""Static self-containment scan for the WebForge HTML/CSS curriculum sources.

Flags (a) fetchable external URLs in render positions and (b) references to
local files that do not exist on disk. Prints a report; exit 1 if any hit.

Run: python -X utf8 .trellis/tasks/10-15-webforge-media-selfcontained/scan.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SRC = REPO / "scripts" / "curriculum"
FILES = (
    sorted(SRC.glob("html_data*.py"))
    + sorted(SRC.glob("css_data*.py"))
    + [SRC / "supplement.py"]
)

# Positions that cause the browser to fetch a resource *when the page renders*.
# `src`/`srcset`/`poster`/`action` always fetch. `href` only fetches for a
# resource-typed <link> (stylesheet/icon/preload/...) or a download target, not
# for <a> navigation or reference rels (canonical/alternate/preconnect/...).
FETCH_ATTR = re.compile(
    r'(?:src|srcset|poster|action)\s*=\s*"(?P<v>[^"]*)"', re.I
)
LINK_FETCH = re.compile(
    r'<link[^>]*\brel\s*=\s*"(?:stylesheet|icon|apple-touch-icon|preload|'
    r'prefetch|manifest)"[^>]*\bhref\s*=\s*"(?P<v>[^"]*)"',
    re.I,
)
CSS_URL = re.compile(r"url\((?P<v>[^)'\"]+)\)", re.I)
# A bare local asset reference (no scheme, not an anchor, not a data URI).
LOCAL_ASSET = re.compile(
    r"^(?!https?:|data:|blob:|mailto:|tel:|#|/|"
    r"https?://|about:)[^\s\"']+\.(?:png|jpe?g|gif|webp|avif|svg|ico|"
    r"css|js|mp4|webm|mp3|wav|ogg|woff2?|csv|json|pdf|txt)$",
    re.I,
)

# Reference-only attributes: never fetched to render the page.
REFERENCE_ATTRS = {"href"}  # hrefs are checked only when they look like assets

# No deferred items: the only permitted 404 is the intentional `missing.png`
# teaching case in html-006, handled via `allowed_404`.
DEFERRED: dict[tuple[str, str], str] = {}


def main() -> int:
    problems: list[str] = []
    deferred: list[str] = []
    allowed_404 = {"missing.png"}
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        for regex in (FETCH_ATTR, LINK_FETCH):
            for m in regex.finditer(text):
                value = m.group("v")
                if value in allowed_404:
                    continue
                if (path.name, value) in DEFERRED:
                    deferred.append(f"{path.name}: {DEFERRED[(path.name, value)]}")
                    continue
                if LOCAL_ASSET.match(value):
                    problems.append(
                        f"{path.name}: fetch attr -> missing local asset {value!r}"
                    )
                if re.match(r"^https?://", value, re.I) and not value.startswith(
                    "http://www.w3.org/2000/svg"
                ):
                    problems.append(
                        f"{path.name}: fetch attr -> external URL {value[:60]!r}"
                    )
        for m in CSS_URL.finditer(text):
            value = m.group("v").strip().strip("'\"")
            if LOCAL_ASSET.match(value):
                problems.append(
                    f"{path.name}: css url() -> missing local asset {value!r}"
                )
            if re.match(r"^https?://", value, re.I) and not value.startswith(
                "http://www.w3.org/2000/svg"
            ):
                problems.append(
                    f"{path.name}: css url() -> external URL {value[:60]!r}"
                )
        # placehold.co anywhere is a network dependency.
        if "placehold.co" in text:
            problems.append(f"{path.name}: still references placehold.co")

    if problems:
        print("SELF-CONTAINMENT PROBLEMS:")
        for problem in problems:
            print("  -", problem)
        return 1
    for item in deferred:
        print("DEFERRED (out of scope, reported):", item)
    print(
        f"OK: {len(FILES)} files, no in-scope fetchable external or missing "
        "local asset"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
