# Mutation test — repaired baseline CSS cases

Mutations: 36. Detected: 36. Undetected: 0.

| id | mutation | detected | first failing checks |
| --- | --- | --- | --- |
| css-example-011 | drop the 900px breakpoint | yes | 900px viewport renders 3 column(s) |
| css-example-011 | move the 2-col breakpoint to 700px | yes | 600px viewport renders 2 column(s) |
| css-example-011 | wrong gap | yes | gap 8px |
| css-example-015 | drop auto-fit (fixed 3 columns) | yes | narrow viewport drops to two tracks; narrow viewport wraps the third card onto a second row |
| css-example-015 | shrink the minmax floor | yes | narrow viewport drops to two tracks; narrow viewport wraps the third card onto a second row |
| css-example-015 | wrong radius | yes | card border radius 12px |
| css-example-021 | weaken grayscale | yes | photo filter is grayscale(1) contrast(1.2) |
| css-example-021 | wrong contrast | yes | photo filter is grayscale(1) contrast(1.2) |
| css-example-021 | wrong blur | yes | glass backdrop-filter is blur(6px) |
| css-example-029 | stop hiding the nav when printing | yes | nav is removed when printing; nav display is none under print |
| css-example-029 | drop break-inside | yes | cards avoid breaking across pages |
| css-example-029 | print with dark background | yes | body prints on white paper |
| css-example-035 | disabled barely translucent | yes | disabled opacity is exactly 0.5 |
| css-example-035 | hover shade equals base | yes | hover darkens to #1557b0 |
| css-example-035 | no press sink | yes | pressed button sinks by 1px |
| css-example-035 | focus ring colour | yes | focus ring is 3px solid #8ab4f8 |
| css-example-036 | single-layer card shadow | yes | card shadow has two layers; card shadow layer 2 is 0 4px 12px |
| css-example-036 | wrong text shadow offset | yes | h1 text-shadow is 0 1px 2px 20% black; text-shadow is offset downward |
| css-example-041 | drop the red top border | yes | ::after top and right borders are red #ea4335 |
| css-example-041 | make the triangle edges opaque | yes | ::after bottom and left borders are transparent |
| css-example-041 | move the triangle off the corner | yes | ::after sits at the top-right corner |
| css-example-044 | wrong measure | yes | max-width really is 65ch; article width is min(65ch, available width) |
| css-example-044 | wrong line height | yes | line-height is 1.7 x 16px = 27.2px |
| css-example-044 | not centred | yes | article is centred with equal side margins; article is horizontally centred on the page |
| css-example-050 | checked state never turns blue | yes | checked slider turns blue |
| css-example-050 | knob does not slide | yes | checked knob slides 22px right; the checked knob travels exactly the free space in the track |
| css-example-050 | knob slides too far | yes | checked knob slides 22px right; the checked knob travels exactly the free space in the track |
| css-example-051 | drop the mobile collapse | yes | narrow layout collapses to one column; narrow areas stack head/left/main/right/foot |
| css-example-051 | equal side columns instead of 3fr main | yes | main column is three times a sidebar (3fr) |
| css-example-051 | drop the named areas | yes | wide layout has three columns; wide layout declares head/left/main/right/foot areas |
| css-example-064 | toggle no longer reveals the menu | yes | narrow: clicking ☰ reveals the menu; narrow: revealed menu stacks its three items |
| css-example-064 | burger never shows on mobile | yes | threw: TimeoutError: locator.click: Timeout 6000ms exceeded. |
| css-example-064 | menu never becomes horizontal | yes | wide: menu is flex; wide: menu gap 16px |
| css-example-090 | variables never switch | yes | wide: --space switches to 16px; wide: --title switches to 24px |
| css-example-090 | variables switch at the wrong breakpoint | yes | narrow: --space is 8px; narrow: --title is 18px |
| css-example-090 | card ignores --space | yes | narrow: card padding follows --space (8px); wide: card padding follows --space (16px) |
