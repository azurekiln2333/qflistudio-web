# p6 oracle inputs — image/media URI change list

Send to p6 so the runtime oracle asserts real rendering, not text only.

## Suggested assertions

For every replaced image:
- `img.complete === true` **and** `img.naturalWidth > 0` (the inline SVG really
  decoded), not merely "an `<img>` exists".

For the one intentional exception (`html-006`, `missing.png`):
- the `<img src="missing.png">` element **must** end with
  `naturalWidth === 0` / `complete === true` (broken), proving the 404 was
  deliberate. If it ever loads, the teaching case has regressed.

For audio/video (`html-010`):
- audio: clicking `#beep` creates an `AudioContext` and starts an oscillator
  (`createOscillator`), or (if a WAV data URI is used instead) the element
  reaches `readyState >= 2` / `duration > 0`.
- video: clicking `#play` starts a `setInterval` that redraws the canvas; the
  frame counter (`i`) advances. A static canvas is a failure.

## Lesson IDs

Emitted IDs use 1-based source order:
`html-tutorial-NNN` / `html-example-NNN`, `css-tutorial-NNN` / `css-example-NNN`
(NNN = the number below, zero-padded to 3).

| ID | Lesson | Change | New URI kind |
|---|---|---|---|
| html-006 | 图片与替代文本：img 的正确用法 | first `<img>` placehold.co → inline SVG; `missing.png` **kept (intentional 404)** | svg-data + **MISSING-PNG** |
| html-010 | 多媒体：audio 与 video | `<video>/<audio>` files → runtime canvas + Web Audio | audio-runtime + video-canvas |
| html-014 | 响应式图片：srcset 与 sizes | `small.jpg`/`large.jpg` → two inline SVGs (480w/1080w) | svg-data |
| html-020 | meta 标签与页面 SEO | `og:image cover.png` → inline SVG 600x315 | svg-data |
| html-023 | 内容分组：figure 与 details | `chart.png` → inline SVG 120x90 | svg-data |
| html-027 | 打印与文档元信息：link rel | `favicon.ico` → SVG icon; `style.css` → `data:text/css`; `font.woff2` preload → SVG preload | svg-data + css-data |
| html-029 | HTML 性能：资源提示与懒加载 | `hero.jpg`/`below.jpg` → inline SVGs 600x400 | svg-data |
| html-034 | HTML 综合实战：文章详情页 | `cover.png` → inline SVG 200x140 | svg-data |
| html-043 | 可下载资源：download 与文件链接 | `report.csv` → `data:text/csv` URI | csv-data |
| html-047 | HTML 图片格式选择：webp 与 avif | `photo.avif/webp/jpg` → inline SVGs (`type=image/svg+xml`) | svg-data |
| html-063 | HTML 图片与文字环绕：figure 布局 | `placehold.co/80x60` → inline SVG 80x60 | svg-data |
| html-066 | HTML 网页图标与主题色 | `favicon.ico`/`touch-icon.png` → inline SVG icons | svg-data |
| html-072 | HTML 图片说明与响应式容器 | placehold.co 600x300/400x400 → inline SVGs | svg-data |
| html-083 | HTML 元数据与分享卡片 | `og:image example.com/cover.png` → inline SVG 1200x630 | svg-data |
| html-088 | HTML 图片加载失败的回退 | `missing.png` → deliberately invalid `data:image/png;base64,INVALID`; `onerror` → inline SVG | svg-data (no 404) |
| html-096 | HTML 图片地图与热点 | `placehold.co/240x80` → inline SVG 240x80 (left/right halves), hotspots intact | svg-data |
| css-073 | @font-face / font-display 回退 | `my.woff2` → 内联 `data:font/woff2;base64,...`（fontTools 原创几何字形） | font-data |
| css-021 | 混合与滤镜：filter 与 mix-blend-mode | placehold.co/120x80 → inline SVG | svg-data |
| css-034 | CSS 伪类进阶：:not、:is、:where | placehold.co/40 → inline SVG 40x40 | svg-data |
| css-046 | CSS 图片画廊网格 | three placehold.co/200 → inline SVGs 200x200 | svg-data |
| css-062 | CSS 深色图片与叠加文字 | `url(placehold.co/400x140)` → inline SVG | svg-data |
| css-078 | CSS 背景定位与精灵图 | `url(placehold.co/48x24)` → inline SVG 48x24 (a/b halves) | svg-data |
| css-084 | CSS 对象与背景裁剪 | two placehold.co/400x200 → inline SVGs 400x200 | svg-data |
| css-088 | CSS 多背景叠加 | `url(placehold.co/20)` → inline SVG 20x20 | svg-data |

## Intentional 404 exception (single)

- **Only** `html-006` keeps a failing local `missing.png`.
- `html-088` **no longer 404s**: its broken image now uses an invalid data URI,
  which triggers `onerror` without a network/local fetch. This keeps "no
  fetchable missing local resource" true while still teaching the fallback.

## css-073 font is a real, reproducible WOFF2

`css_data5.py`'s `@font-face` lesson now embeds a genuine 576-byte WOFF2 built
from scratch by `scripts/curriculum/make_demo_font.py` (`FontBuilder` +
`TTGlyphPen`, original geometric glyphs covering `W e b F o r g` — no system or
vendor font). The earlier 189-byte `AAAA…` header was a broken placeholder and
was replaced.

- `head.created`/`head.modified` are pinned to a fixed epoch and
  `recalcTimestamp=False`, so two consecutive runs are byte-identical
  (SHA-256 verified).
- Optional tooling is installed project-locally under the gitignored
  `.trellis/.runtime/font-tools`; regular `emit_content.py` does **not** depend
  on it.

```bash
python -X utf8 -m pip install --target .trellis/.runtime/font-tools \
    fonttools==4.67.0 brotli==1.2.0
PYTHONPATH=.trellis/.runtime/font-tools python -X utf8 \
    scripts/curriculum/make_demo_font.py
PYTHONPATH=.trellis/.runtime/font-tools python -X utf8 \
    .trellis/tasks/10-15-webforge-media-selfcontained/check_demo_font.py
# PASS: real WOFF2, upem=1000, covers 'WebForge' with drawn glyphs
```

Pinned versions: **fonttools==4.67.0**, **brotli==1.2.0**.

### Oracle for p6 (css-073)

- `const f = new FontFace('MyFont', 'url(data:font/woff2;base64,...)')`;
  after `f.load()` assert `f.status === 'loaded'`;
  `await document.fonts.load('16px MyFont', 'WebForge')` resolves to a non-empty
  `FontFaceSet` and `document.fonts.check('16px MyFont')` is `true`.
- Assert no network request for `my.woff2` (the inline font never fetches).

## Deferred items

None. p7 fixed `supplement.py` html-097 ("HTML 内联样式表与关键 CSS") by
generating its non-critical stylesheet at runtime with
`URL.createObjectURL(new Blob([...], {type:'text/css'}))` — no `rest.css`, no
network. The scan's stale `DEFERRED` entry was removed.

The **only** permitted 404 is the intentional `missing.png` teaching case in
`html-006`.

## Not changed (intentional references, never fetched to render)

`canonical`, schema.org `itemtype`, `blockquote cite`, `rel=noopener/nofollow/me`,
CSP meta, `rel=preconnect`/`dns-prefetch`, `hreflang`, `og:url`, `mailto:`/`tel:`,
the `a[href^="https"]` selector, and the MDN `<a href>` navigation link. These
are the lessons' subject matter and are not automatically requested by the page.
