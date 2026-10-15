# CSS source fix — precise remaining items (unquoted data URI + missing font)

> Attribution corrected per p6's controlled probe: these are **source** defects.
> The unquoted `url(data:image/svg+xml,...)` containing spaces is an invalid CSS
> token, so the browser drops the declaration and computed `background-image`
> is `none`. The markup oracle is correct; it is not a misread.

Coordinator asked me to converge directly. Evidence from the current
`scripts/curriculum/css_data*.py`:

```
css_data.py    unquoted_data=0 quoted_data=0 my.woff2=False
css_data2.py   unquoted_data=0 quoted_data=0 my.woff2=False
css_data3.py   unquoted_data=0 quoted_data=0 my.woff2=False
css_data4.py   unquoted_data=1 quoted_data=0 my.woff2=False
   UNQUOTED: url(data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%27400%27 heigh...
css_data5.py   unquoted_data=2 quoted_data=0 my.woff2=True
   UNQUOTED: url(data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%2748%27 height...
   UNQUOTED: url(data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%2720%27 height...
```

Affected examples (runner failures): `css-example-062` (css_data4),
`css-example-078` + `css-example-088` (css_data5), and `css-example-073`
(`css_data5` `@font-face src: url("my.woff2")`).

## Required fixes (p5, CSS sources)

1. `css_data4.py` (css-062): quote the data URI ->
   `background: url("data:image/svg+xml,...");`
2. `css_data5.py` (css-078, css-088): quote both data URIs the same way.
3. `css_data5.py` (css-073): remove the external `@font-face` `my.woff2`
   (inline a data-URI font, or drop the external font and keep the
   `font-display`/fallback teaching point).

After these, the only intentional 404 is `html-example-006` `/missing.png`
(runner exact id+path allowlist).

I will not edit CSS sources. On your "done" event I run
`python -X utf8 scripts/emit_content.py` once, then a single full
`node scripts/run_examples.mjs`, targeting 301/301 with mapping 0.
