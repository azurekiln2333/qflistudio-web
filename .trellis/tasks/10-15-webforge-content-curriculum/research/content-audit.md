# Content Audit — Shared Core HTML/CSS/JS (baseline)

Task: `10-15-webforge-content-curriculum`. Date: 2026-10-15.
Tool: `scripts/audit_web_content.py --shared`.
Raw report: [`audit-shared-baseline.md`](./audit-shared-baseline.md).

## Why this file

WebForge's `webProfile` has no `contentRepositoryFactory`, so
`home_page.dart` (`_sharedContentRepository`) falls back to the shared core
`AssetContentRepository`, reading
`qfli_studio_core/assets/content/{tutorials,examples}.json`. This audit records
what that fallback actually serves for the WebForge-visible types
(`html`, `css`, `javascript`).

## Verdict

**Placeholder / machine-generated filler. Not a usable curriculum.**

Quantified evidence (300 tutorials + 300 examples across the three web types):

| Metric | Shared result | Usable threshold |
| --- | --- | --- |
| Web tutorials | 300 | >= 100 |
| Web examples | 300 | >= 100 |
| Distinct concepts | 27 | meaningful spread |
| `explain` uniqueness | **1 / 300** | 100% distinct |
| Lesson `output` uniqueness | **200 / 300** | distinct per lesson |
| Normalised tutorial titles | **72 / 300** | ~100% distinct |
| Normalised example titles | **72 / 300** | ~100% distinct |
| Normalised example bodies | **3 / 300** | distinct per example |
| Normalised lesson code | **3** | distinct per lesson |

Concepts are spam: `可测试实现`, `边界条件`, `发布检查` each appear in all 300
lessons.

## Concrete samples

Titles are recycled and, worse, describe backend topics unrelated to the web:

- `HTML 001: 数据建模与不变量`
- `HTML 002: 接口校验与错误边界`
- `CSS 003: 文件格式与编码`
- `JavaScript 004: 日志与可观测性`

Only 24 title suffixes cycle four times per language. All 300 lessons share one
`explain` paragraph ("把问题分成输入、状态变化和输出三层…"). HTML examples are
identical modulo a number:

```html
<!doctype html>
<main data-case="1"><h1>Measurement 1</h1><output>weighted=22</output></main>
```

with `expectedOutput` of `preview-ready\ncase=1`. CSS examples are a single
`.measurement-N { … color: hsl(N 65% 35%); }` pattern; JavaScript examples are
the same `values.reduce(...)` weighting snippet. `expectedOutput: weighted=22`
recurs across lessons.

## Conclusion

Per the user's instruction, WebForge's content source must be replaced with a
product-owned curriculum. The shared core aggregate is left untouched (other
products consume it); WebForge switches via `StudioProfile.contentRepositoryFactory`.
The product assets are audited with `--product` and must report 0 issues.
