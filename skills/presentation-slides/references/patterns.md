# Layout patterns

The catalogue to pick from. Vary the shape between slides - repeating one pattern
across a deck is what makes it read as boxy. All classes exist in
`template.html`; nothing here needs new CSS.

---

## Journey lane

**Use for:** a sequence over time - a timeline, a process, stages of work.
**Avoid for:** things with no ordering.

Circles joined by connector bars, each with a heading and one short sentence. The
`.dim` variant (dashed, grey) marks a pause, a gap or a step that did not go well -
useful for being honest about a break in the middle of a timeline.

```html
<div class="lane">
  <div class="stg"><div class="dot"><!-- 32px svg, stroke #fff --></div>
    <h3>Stage</h3><p>One sentence.</p></div>
  <div class="conn"></div>
  <div class="stg dim">...</div>
</div>
```

Five stages is the practical maximum before the text squeezes.

## Resource chips

**Use for:** naming tools, sources or products in passing, under a lane or cluster.

Small horizontal chips - coloured icon square, name, and a short grey qualifier.
Use the vendor's brand colour on the icon tile. Lower visual weight than a full
tile, so it does not compete with the main content.

```html
<div class="reslane">
  <div class="lab">what I used</div>
  <div class="tchip"><div class="ic" style="background:#A435F0"><!-- svg --></div>
    <div><div class="nm">Name</div><div class="sub">what it is</div></div></div>
</div>
```

## Two clusters with a divider

**Use for:** contrast where the *volume* is the argument - small set versus large
set. The imbalance does the persuading, so let it be visibly lopsided.

Grid is `0.82fr auto 1.5fr` with a vertical "versus" between. Left column single,
right column `.two` for two-up. Green rows for the familiar side, blue for the
unfamiliar.

Prefer **concepts over instances** here. Naming specific products makes the big
side look merely twice as long; naming categories makes it look genuinely wider.

## Lens row

**Use for:** a set of framings or criteria that need to be seen together, briefly.

Borderless columns separated by left rules. Text only, no boxes, no explanation -
they are there to be pointed at while he talks. Keep every entry to two or three
words and style them identically; an odd one out reads as a mistake rather than
emphasis.

## Question box with staged reveal

**Use for:** working an example with the room. The most interactive pattern here.

Beats, in DOM order (fragments reveal in document order):

1. Plain question and all options visible, nothing marked
2. Highlight the deciding detail - `<span class="hl frag">`
3. Highlight the qualifier - `<span class="hl blue frag">`
4. The correct option lights green - `<div class="opt hl frag">`
5. The twist - `<div class="flip frag">` - change one detail, the answer moves
6. The takeaway callout

`.hl` overrides the fragment opacity fade and transitions a background colour
instead, so text stays readable and only the emphasis appears.

Write distractors that are all defensible. If three options are obviously silly
there is no thinking to do and the pattern is wasted.

## Three-block flow (the axe)

**Use for:** a spectrum, a progression, or a before/middle/after.

`.axeblock plain` → arrow → `.axeblock cyan` → arrow → `.axeblock navy`. The
darkening carries the direction without needing a caption underneath - an explicit
"less X ... more X" band was tried and cut as redundant.

Each block: title, one bold defining line, icon row, pros and cons, then the tell.

```html
<div class="axeblock cyan frag">
  <div class="t">Title</div>
  <div class="def">One bold sentence defining it.</div>
  <div class="svcrow"><!-- .svc tiles --></div>
  <div class="pc"><div class="pro">Upside</div><div class="con">Downside</div></div>
  <div class="trig">The tell.</div>
</div>
```

**Define the terms.** If a block's label is jargon - "managed", "serverless" - the
`.def` line must say what it actually means in plain terms. Do not assume the room
shares the vocabulary.

**Give every block cons.** A spectrum with pros only reads as advocacy. Real
trade-offs make it a decision aid.

Make each block its own fragment so he can talk one at a time.

## Service tiles

**Use for:** naming products visually inside a block.

```html
<div class="svc"><div class="ic"><!-- official 64x64 svg --></div>
  <div class="nm">Name</div></div>
```

`.ic` is a rounded clip with no background of its own - the official icon supplies
its own full-bleed colour. For AWS, the pack at
`aws.amazon.com/architecture/icons` gives `Arch_<Service>_48.svg` files with the
category colour already in them; strip the XML declaration and `<title>`, then
inline the `<svg>` element.

## Callout

**Use for:** the one line per slide worth landing.

Left cyan border, tinted background, no full box. Lower weight than a bordered
panel and it never reads as a card. One per slide at most. Make it a rule he can
apply, not a remark.
