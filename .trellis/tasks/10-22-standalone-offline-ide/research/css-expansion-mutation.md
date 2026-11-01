# Mutation test — do the expansion oracles detect broken lessons?

Mutations: 60. Detected: 60. Undetected: 0.

| id | mutation | detected | first failing checks |
| --- | --- | --- | --- |
| css-example-101 | color: #1a73e8 -> color: #ea4335 | yes | theme layer wins over the later base layer |
| css-example-102 | color: #202124 !important -> color: #5f6368 !important | yes | !important reverses layer order: reset wins |
| css-example-103 | color: #1a73e8 -> color: #ea4335 | yes | scoped paragraph is blue |
| css-example-104 | initial-value: #1a73e8 -> initial-value: #ea4335 | yes | --tone initial value is the blue; unset element falls back to initial-value |
| css-example-105 | color: #202124 -> color: #5f6368 | yes | :where() loses to a plain class selector; list item keeps the plain class colour |
| css-example-106 | background: #e8f0fe -> background: #ffffff | yes | filtered 3rd .pick gets the tint |
| css-example-107 | border-color: #1a73e8 -> border-color: #ea4335 | yes | checked card starts highlighted; clicking the radio moves the highlight |
| css-example-108 | border-color: #1a73e8 -> border-color: #34a853 | yes | :focus-within tints the group border |
| css-example-109 | border-color: #ea4335 -> border-color: #fbbc04 | yes | edited invalid value turns the border red |
| css-example-110 | border-color: #1a73e8 -> border-color: #34a853 | yes | targeted panel border is blue |
| css-example-111 | content: "暂无数据" -> content: "空" | yes | empty slot shows the placeholder text |
| css-example-112 | color: #1a73e8 -> color: #ea4335 | yes | marker colour is the theme blue |
| css-example-113 | background: #1a73e8 -> background: #34a853 | yes | file button background is the theme blue |
| css-example-114 | flex: 1 1 0 -> flex: 1 1 auto | yes | flex-basis:0 items declare a 0px basis; first equal item is 200px wide |
| css-example-115 | order: 3 -> order: 0 | yes | first DOM item declares order 3; visual order is two, three, one |
| css-example-116 | align-content: flex-start -> align-content: center | yes | container declares align-content flex-start; second row starts at 50px (40 + 10 gap) |
| css-example-117 | gap: 6px -> gap: 16px | yes | chip gap is 6px |
| css-example-118 | grid-template-columns: 120px 1fr 80px -> grid-template-columns: 200px 1fr 80px | yes | parent tracks are 120/376/80; name cell aligns to the 120px track |
| css-example-119 | minmax(150px, 1fr) -> minmax(80px, 1fr) | yes | auto-fill produces exactly 5 columns at 960px; each column is about 179.2px (1fr of the remainder) |
| css-example-120 | grid-auto-rows: 40px -> grid-auto-rows: 80px | yes | implicit rows are 40px; first row item is 40px tall |
| css-example-121 | place-content: end space-between -> place-content: start | yes | place-content resolves align-content to end; place-content resolves justify-content to space-between |
| css-example-122 | display: contents -> display: block | yes | wrapper generates no box; wrapper has zero size |
| css-example-123 | contain: layout paint -> contain: none | yes | containment is layout paint |
| css-example-124 | width: clamp(200px, 40vw, 320px) -> width: clamp(200px, 40vw, 420px) | yes | clamp hits its upper bound (320px); computed width exposes the resolved clamp value |
| css-example-125 | width: fit-content -> width: max-content | yes | fit-content shrinks to the available 120px |
| css-example-126 | inset-inline-start: 20px -> inset-inline-start: 60px | yes | inset-inline-start resolves to left: 20px; badge sits 20px from the stage inline start |
| css-example-127 | scroll-margin-top: 60px -> scroll-margin-top: 0px | yes | anchor reserves 60px of scroll margin; anchor jump lands 60px below the viewport top |
| css-example-128 | height: 50dvh -> height: 40dvh | yes | dvh block takes half the dynamic viewport; computed dvh height is the used pixel value |
| css-example-129 | font-size: 5cqi -> font-size: 9cqi | yes | title is 5cqi of a 400px container = 20px; title is 5cqi of a 200px container = 10px |
| css-example-130 | max-width: 60ch -> max-width: 30ch | yes | 60ch resolves to 480px in this monospace font; the article is capped by the measure |
| css-example-131 | overflow-clip-margin: 10px -> overflow-clip-margin: 30px | yes | clip margin is 10px |
| css-example-132 | oklch(0.6 0.17 255) -> oklch(0.8 0.17 255) | yes | swatch 3 keeps its oklch value |
| css-example-133 | #1a73e8 50%, #ffffff -> #1a73e8 90%, #ffffff | yes | 50/50 mix resolves in oklab with L = 0.7868 |
| css-example-134 | light-dark(#f1f3f4, #303134) -> light-dark(#e8f0fe, #303134) | yes | light theme card background is #f1f3f4 |
| css-example-135 | calc(r + 60) -> calc(r + 20) | yes | calc() raises each channel by 60/255 |
| css-example-136 | #ffffff 10px 20px -> #ffffff 10px 40px | yes | diagonal stripes keep both stops and the 20px period |
| css-example-137 | to right -> to left | yes | mask fades black to transparent to the right |
| css-example-138 | mask-composite: intersect -> mask-composite: add | yes | mask-composite resolves to intersect for both layers |
| css-example-139 | background-blend-mode: multiply -> background-blend-mode: normal | yes | blend mode multiply applies to both layers |
| css-example-140 | border: 8px solid transparent -> border: 4px solid transparent | yes | border width is 8px |
| css-example-141 | text-emphasis-color: #1a73e8 -> text-emphasis-color: #ea4335 | yes | emphasis colour is the theme blue |
| css-example-142 | -webkit-text-stroke: 2px #1a73e8 -> -webkit-text-stroke: 1px #1a73e8 | yes | stroke width is 2px |
| css-example-143 | text-wrap: balance -> text-wrap: wrap | yes | balanced heading declares text-wrap: balance; balanced heading keeps every line wide |
| css-example-144 | overflow-wrap: anywhere -> overflow-wrap: normal | yes | long word allows breaking anywhere; broken word stays inside the 120px box |
| css-example-145 | tabular-nums -> proportional-nums | yes | tabular-nums is applied to the first row |
| css-example-146 | text-underline-offset: 4px -> text-underline-offset: 12px | yes | underline offset is 4px on both |
| css-example-147 | box-decoration-break: clone -> box-decoration-break: slice | yes | box-decoration-break is clone |
| css-example-148 | text-box-trim: trim-both -> text-box-trim: none | yes | trimmed heading declares trim-both; trimmed heading box shrinks to 30.25px |
| css-example-149 | allow-discrete -> normal | yes | display transitions discretely |
| css-example-150 | forwards -> none | yes | fill mode is forwards; the final frame is kept at translateX(60px) |
| css-example-151 | cubic-bezier(0.2, 0.8, 0.2, 1) -> linear | yes | custom easing curve is parsed; at ~30% of the duration the dot has already moved past the linear position |
| css-example-152 | animation-timeline: scroll(root) -> animation-timeline: auto | yes | animation timeline is the root scroller; progress starts at zero |
| css-example-153 | animation: none -> animation: spin 1s linear infinite | yes | reduced motion turns the animation off; the spinner keeps its 32px size |
| css-example-154 | accumulate, accumulate -> replace, replace | yes | accumulate composition applies to both animations; accumulate ends at translateX(30px) |
| css-example-155 | scroll-snap-type: x mandatory -> scroll-snap-type: none | yes | rail snaps on the x axis mandatorily; the rail snaps to the 220px snap point |
| css-example-156 | scrollbar-gutter: stable -> scrollbar-gutter: auto | yes | stable gutter is declared; stable reserves 15px even without overflow |
| css-example-157 | overscroll-behavior: contain -> overscroll-behavior: auto | yes | outer scroller contains its overscroll; the page does not scroll when the inner one is at its end |
| css-example-158 | field-sizing: content -> field-sizing: fixed | yes | input declares field-sizing: content; textarea declares field-sizing: content |
| css-example-159 | appearance: none -> appearance: auto | yes | native appearance is removed |
| css-example-160 | position-area: bottom -> position-area: top | yes | tooltip area is below the anchor; tooltip top touches the anchor bottom (73px) |

