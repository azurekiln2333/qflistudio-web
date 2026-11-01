# Host-owned viewport (no resizing) — responsive fallbacks

Simulated: `viewportSize() === null` and `setViewportSize()` throws, at 360, 412, 599, 600, 800, 900, 1280 px.

| width | id | checks | fallback branch | result | first failure |
| --- | --- | --- | --- | --- | --- |
| 360 | css-example-002 | 5 | no (resizable) | pass |  |
| 360 | css-example-011 | 6 | yes | pass |  |
| 360 | css-example-015 | 8 | yes | pass |  |
| 360 | css-example-044 | 6 | no (resizable) | pass |  |
| 360 | css-example-051 | 2 | yes | pass |  |
| 360 | css-example-064 | 3 | yes | pass |  |
| 360 | css-example-090 | 5 | yes | pass |  |
| 412 | css-example-002 | 5 | no (resizable) | pass |  |
| 412 | css-example-011 | 6 | yes | pass |  |
| 412 | css-example-015 | 8 | yes | pass |  |
| 412 | css-example-044 | 6 | no (resizable) | pass |  |
| 412 | css-example-051 | 2 | yes | pass |  |
| 412 | css-example-064 | 3 | yes | pass |  |
| 412 | css-example-090 | 5 | yes | pass |  |
| 599 | css-example-002 | 5 | no (resizable) | pass |  |
| 599 | css-example-011 | 6 | yes | pass |  |
| 599 | css-example-015 | 8 | yes | pass |  |
| 599 | css-example-044 | 6 | no (resizable) | pass |  |
| 599 | css-example-051 | 2 | yes | pass |  |
| 599 | css-example-064 | 3 | yes | pass |  |
| 599 | css-example-090 | 5 | yes | pass |  |
| 600 | css-example-002 | 5 | no (resizable) | pass |  |
| 600 | css-example-011 | 6 | yes | pass |  |
| 600 | css-example-015 | 8 | yes | pass |  |
| 600 | css-example-044 | 6 | no (resizable) | pass |  |
| 600 | css-example-051 | 2 | yes | pass |  |
| 600 | css-example-064 | 3 | yes | pass |  |
| 600 | css-example-090 | 5 | yes | pass |  |
| 800 | css-example-002 | 5 | no (resizable) | pass |  |
| 800 | css-example-011 | 6 | yes | pass |  |
| 800 | css-example-015 | 8 | yes | pass |  |
| 800 | css-example-044 | 7 | no (resizable) | pass |  |
| 800 | css-example-051 | 2 | yes | pass |  |
| 800 | css-example-064 | 3 | yes | pass |  |
| 800 | css-example-090 | 5 | yes | pass |  |
| 900 | css-example-002 | 5 | no (resizable) | pass |  |
| 900 | css-example-011 | 6 | yes | pass |  |
| 900 | css-example-015 | 8 | yes | pass |  |
| 900 | css-example-044 | 7 | no (resizable) | pass |  |
| 900 | css-example-051 | 2 | yes | pass |  |
| 900 | css-example-064 | 3 | yes | pass |  |
| 900 | css-example-090 | 5 | yes | pass |  |
| 1280 | css-example-002 | 5 | no (resizable) | pass |  |
| 1280 | css-example-011 | 6 | yes | pass |  |
| 1280 | css-example-015 | 8 | yes | pass |  |
| 1280 | css-example-044 | 7 | no (resizable) | pass |  |
| 1280 | css-example-051 | 2 | yes | pass |  |
| 1280 | css-example-064 | 3 | yes | pass |  |
| 1280 | css-example-090 | 5 | yes | pass |  |

Rows: 49. Failures: 0.
Width-branching rows: 35. Of those, rows that did NOT use the width fallback: 0.
