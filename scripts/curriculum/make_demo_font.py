"""Generate an original, tiny, real WOFF2 demo font for the curriculum.

This produces a genuine geometric-glyph font (not a placeholder header) whose
visible ASCII includes the word "WebForge", so a browser can actually load it
and the `@font-face`/`font-display` lesson can assert
`document.fonts.load(...)` succeeds with `FontFace.status === 'loaded'`.

Every glyph is drawn from scratch with `TTGlyphPen` (simple rectangles and
polygons); no system or vendor font is embedded.

Reproducible via the project-local tool install (kept out of global scope and
out of version control):

    python -X utf8 -m pip install --target .trellis/.runtime/font-tools \
        fonttools==4.67.0 brotli==1.2.0
    PYTHONPATH=.trellis/.runtime/font-tools python -X utf8 \
        scripts/curriculum/make_demo_font.py

Two consecutive runs must print the same base64 (reproducible byte-for-byte),
because head.created/modified are pinned to a fixed epoch and
recalcTimestamp is off.

The script prints the base64 WOFF2 to embed; it does NOT edit the curriculum
sources itself (regular `emit_content.py` must not depend on this optional
tooling). Paste the printed value into `css_data5.py`'s `@font-face` lesson.

Pinned tool versions used to author the current embedded value:
    fonttools==4.67.0, brotli==1.2.0
"""
from __future__ import annotations

import base64
import io
import sys

try:
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib import TTFont
    from fontTools.ttLib.tables._h_e_a_d import mac_epoch_diff
    from datetime import datetime, timezone
except ModuleNotFoundError:  # pragma: no cover - optional tooling
    sys.stderr.write(
        "fontTools not importable. Run with:\n"
        "  PYTHONPATH=.trellis/.runtime/font-tools python "
        "scripts/curriculum/make_demo_font.py\n"
    )
    raise

UPEM = 1000
DESCENT = -200

# head times are seconds since the 1904 Mac epoch; unix + |epoch_diff| = mac.
FIXED_TIMESTAMP = int(
    datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp() - mac_epoch_diff
)

# 5x7 box strokes for the glyphs we ship. Each entry is a set of rectangles in
# a 0..4 (x) by 0..6 (y) grid, scaled to UPEM below. Original geometry only.
RECTS: dict[str, list[tuple[int, int, int, int]]] = {
    " ": [],
    "W": [(0, 0, 1, 7), (1, 5, 2, 7), (2, 3, 3, 5), (3, 5, 4, 7), (4, 0, 5, 7)],
    "e": [(0, 3, 5, 4), (0, 0, 1, 7), (4, 0, 5, 7), (0, 0, 5, 1)],
    "b": [(0, 0, 1, 7), (1, 3, 4, 4), (1, 6, 4, 7), (4, 3, 5, 4), (0, 0, 5, 1)],
    "F": [(0, 0, 1, 7), (0, 6, 5, 7), (0, 3, 4, 4)],
    "o": [(0, 0, 5, 1), (0, 6, 5, 7), (0, 0, 1, 7), (4, 0, 5, 7)],
    "r": [(0, 0, 1, 7), (1, 3, 5, 7)],
    "g": [(0, 0, 5, 1), (0, 6, 5, 7), (4, 0, 5, 7), (1, 0, 4, 1)],
}
# Map lowercase-only teaching text to the glyph set we actually draw.
TEXT = "WebForge"
NEEDED = sorted(set(TEXT))


def _scale(v: int) -> int:
    return round(v * UPEM / 10)


def _glyph(rects: list[tuple[int, int, int, int]]):
    pen = TTGlyphPen(None)
    for x1, y1, x2, y2 in rects:
        pen.moveTo((_scale(x1), _scale(y1)))
        pen.lineTo((_scale(x2), _scale(y1)))
        pen.lineTo((_scale(x2), _scale(y2)))
        pen.lineTo((_scale(x1), _scale(y2)))
        pen.closePath()
    return pen.glyph()


def build() -> TTFont:
    fb = FontBuilder(UPEM, isTTF=True)
    order = [".notdef"] + NEEDED
    glyphs = {".notdef": _glyph([(0, 0, 6, 8)])}
    glyphs.update({ch: _glyph(RECTS.get(ch, [])) for ch in NEEDED})
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({ord(ch): ch for ch in NEEDED})
    fb.setupGlyf(glyphs)
    metrics = {}
    for name in order:
        advance = 0 if name == " " else _scale(6)
        rects = RECTS.get(name)
        bearing = _scale(rects[0][0]) if rects else 0
        metrics[name] = (advance, bearing)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=_scale(8), descent=DESCENT)
    # Pin head timestamps BEFORE any save so the output is reproducible.
    head = fb.font["head"]
    head.created = FIXED_TIMESTAMP
    head.modified = FIXED_TIMESTAMP
    fb.font.recalcTimestamp = False
    fb.setupNameTable({
        "familyName": "WebForge Demo",
        "styleName": "Regular",
        "psName": "WebForgeDemo-Regular",
        "fullName": "WebForge Demo Regular",
        "version": "Version 1.000",
        "uniqueFontIdentifier": "WebForgeDemo-Regular-1.000",
    })
    fb.setupOS2(sTypoAscender=_scale(8), sTypoDescender=-200,
                usWinAscent=_scale(8), usWinDescent=200)
    fb.setupPost()
    return fb.font


def main() -> int:
    font = build()
    # Belt-and-braces: ensure no recalculation happens on save.
    font.recalcTimestamp = False
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    data = buf.getvalue()
    assert data[:4] == b"wOF2", data[:4]
    b64 = base64.b64encode(data).decode("ascii")
    print(f"# {len(data)} bytes WOFF2, glyphs: {''.join(NEEDED)}")
    print(f"data:font/woff2;base64,{b64}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
