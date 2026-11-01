# Native ArkWeb probe — real CSS oracles on packaged cases

Generated: 2026-10-22T11:50:53.171Z

| id | result | failing checks |
| --- | --- | --- |
| css-example-031 | pass |  |
| css-example-035 | FAIL | focus ring is 3px solid #8ab4f8 (rgb(138, 180, 248)) |
| css-example-044 | pass |  |
| css-example-114 | pass |  |

## All checks

### css-example-031
- ok   margin-inline 24px
- ok   padding-block 12px
- ok   box background #e8f0fe

### css-example-035
- ok   btn blue
- ok   btn pointer
- ok   btn radius 6px
- ok   btn padding 10px 20px
- ok   disabled opacity is exactly 0.5 — 0.5
- ok   disabled cursor is not-allowed
- ok   Tab focuses the first button
- FAIL focus ring is 3px solid #8ab4f8 — rgb(138, 180, 248)
- ok   hover darkens to #1557b0 — rgb(21, 87, 176)
- ok   pressed button matches :active
- ok   pressed button sinks by 1px — matrix(1, 0, 0, 1, 0, 1)
- ok   released button returns to rest

### css-example-044
- ok   max-width really is 65ch — 592.8 vs 65ch=592.7991333007812
- ok   65ch is a readable measure (500-700px) — 592.7991333007812
- ok   line-height is 1.7 x 16px = 27.2px — 27.2px
- ok   article padding is 16px
- ok   article width is min(65ch, available width) — 318 vs min(592.7991333007812, 318)
- ok   at a narrow width the article fills the available width — 318 vs 318

### css-example-114
- ok   flex-basis:0 items declare a 0px basis — 0px
- ok   first equal item is 200px wide — 200
- ok   second equal item is 200px wide
- ok   third equal item is 200px wide even with long text — 200
- ok   equal items sit at 200px steps — 400
- ok   auto basis row declares auto
- ok   auto basis shares by content, not equally — 109.33036041259766 vs 333.3348083496094
