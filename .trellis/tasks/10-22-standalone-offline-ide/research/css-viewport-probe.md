# Existing CSS oracle vs viewport

Unmodified oracle, three viewports. Examples that fail at a narrow viewport: 4/100.

A row is a real portability defect when it
passes on desktop but fails on a narrower viewport: the acceptance runner and the
OHOS catalog harness would then disagree about the same shipped document.

| id | desktop | tablet | phone | failing checks (narrow) |
| --- | --- | --- | --- | --- |
| css-example-001 | pass | pass | pass |  |
| css-example-002 | pass | pass | pass |  |
| css-example-003 | pass | pass | pass |  |
| css-example-004 | pass | pass | pass |  |
| css-example-005 | pass | pass | pass |  |
| css-example-006 | pass | pass | pass |  |
| css-example-007 | pass | pass | pass |  |
| css-example-008 | pass | pass | pass |  |
| css-example-009 | pass | pass | pass |  |
| css-example-010 | pass | pass | pass |  |
| css-example-011 | pass | FAIL | FAIL | three columns at 1280px [cols=2]<br>three columns at 1280px [cols=1] |
| css-example-012 | pass | pass | pass |  |
| css-example-013 | pass | pass | pass |  |
| css-example-014 | pass | pass | pass |  |
| css-example-015 | pass | pass | pass |  |
| css-example-016 | pass | pass | pass |  |
| css-example-017 | pass | pass | pass |  |
| css-example-018 | pass | pass | pass |  |
| css-example-019 | pass | pass | pass |  |
| css-example-020 | pass | pass | pass |  |
| css-example-021 | pass | pass | pass |  |
| css-example-022 | pass | pass | pass |  |
| css-example-023 | pass | pass | pass |  |
| css-example-024 | pass | pass | pass |  |
| css-example-025 | pass | pass | pass |  |
| css-example-026 | pass | pass | pass |  |
| css-example-027 | pass | pass | pass |  |
| css-example-028 | pass | pass | pass |  |
| css-example-029 | pass | pass | pass |  |
| css-example-030 | pass | pass | pass |  |
| css-example-031 | pass | pass | pass |  |
| css-example-032 | pass | pass | pass |  |
| css-example-033 | pass | pass | pass |  |
| css-example-034 | pass | pass | pass |  |
| css-example-035 | pass | pass | pass |  |
| css-example-036 | pass | pass | pass |  |
| css-example-037 | pass | pass | pass |  |
| css-example-038 | pass | pass | pass |  |
| css-example-039 | pass | pass | pass |  |
| css-example-040 | pass | pass | pass |  |
| css-example-041 | pass | pass | pass |  |
| css-example-042 | pass | pass | pass |  |
| css-example-043 | pass | pass | pass |  |
| css-example-044 | pass | pass | FAIL | article width constrained (65ch) [609.883] |
| css-example-045 | pass | pass | pass |  |
| css-example-046 | pass | pass | pass |  |
| css-example-047 | pass | pass | pass |  |
| css-example-048 | pass | pass | pass |  |
| css-example-049 | pass | pass | pass |  |
| css-example-050 | pass | pass | pass |  |
| css-example-051 | pass | pass | FAIL | holy grail three columns at 1280px [396px] |
| css-example-052 | pass | pass | pass |  |
| css-example-053 | pass | pass | pass |  |
| css-example-054 | pass | pass | pass |  |
| css-example-055 | pass | pass | pass |  |
| css-example-056 | pass | pass | pass |  |
| css-example-057 | pass | pass | pass |  |
| css-example-058 | pass | pass | pass |  |
| css-example-059 | pass | pass | pass |  |
| css-example-060 | pass | pass | pass |  |
| css-example-061 | pass | pass | pass |  |
| css-example-062 | pass | pass | pass |  |
| css-example-063 | pass | pass | pass |  |
| css-example-064 | pass | pass | FAIL | burger hidden on wide []<br>menu flex on wide [] |
| css-example-065 | pass | pass | pass |  |
| css-example-066 | pass | pass | pass |  |
| css-example-067 | pass | pass | pass |  |
| css-example-068 | pass | pass | pass |  |
| css-example-069 | pass | pass | pass |  |
| css-example-070 | pass | pass | pass |  |
| css-example-071 | pass | pass | pass |  |
| css-example-072 | pass | pass | pass |  |
| css-example-073 | pass | pass | pass |  |
| css-example-074 | pass | pass | pass |  |
| css-example-075 | pass | pass | pass |  |
| css-example-076 | pass | pass | pass |  |
| css-example-077 | pass | pass | pass |  |
| css-example-078 | pass | pass | pass |  |
| css-example-079 | pass | pass | pass |  |
| css-example-080 | pass | pass | pass |  |
| css-example-081 | pass | pass | pass |  |
| css-example-082 | pass | pass | pass |  |
| css-example-083 | pass | pass | pass |  |
| css-example-084 | pass | pass | pass |  |
| css-example-085 | pass | pass | pass |  |
| css-example-086 | pass | pass | pass |  |
| css-example-087 | pass | pass | pass |  |
| css-example-088 | pass | pass | pass |  |
| css-example-089 | pass | pass | pass |  |
| css-example-090 | pass | pass | pass |  |
| css-example-091 | pass | pass | pass |  |
| css-example-092 | pass | pass | pass |  |
| css-example-093 | pass | pass | pass |  |
| css-example-094 | pass | pass | pass |  |
| css-example-095 | pass | pass | pass |  |
| css-example-096 | pass | pass | pass |  |
| css-example-097 | pass | pass | pass |  |
| css-example-098 | pass | pass | pass |  |
| css-example-099 | pass | pass | pass |  |
| css-example-100 | pass | pass | pass |  |
