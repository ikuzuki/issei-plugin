---
name: presentation-slides
description: Build a self-contained HTML slide deck in Issei's visual house style - 1600x900 slides, Curve navy/cyan palette, keyboard navigation, click-to-reveal fragments and a fullscreen toggle. Use whenever Issei asks for slides, a deck, a talk, a presentation, a demo slide, a classroom or forum session, "a few slides on X", or points at an existing deck and says "same format as that". Covers everything from a single slide to a ten-slide talk. The output is one portable .html file with all CSS, JS and images inlined. Do NOT use for PowerPoint (.pptx) deliverables, long-form written documents, or dashboards - those have their own skills.
user-invocable: true
---

# Presentation slides

Issei presents from a browser, full screen, talking over the slides. The deck is
scaffolding for a spoken argument - it is not the argument, and it is never the
handout. Almost every correction he makes to a draft deck is *cut this*.

The single most common failure is **density**. A deck that reads fine as a document
is already too dense to present from. If in doubt, halve the words and double the
type size.

## The philosophy

**He talks, the slides support.** Anything he can say out loud should not be written
down. Personal detail especially - scores, timings, anecdotes, the texture of an
experience - belongs in his mouth, not on the screen. When he says "I can talk over
this", delete it rather than shrinking it.

**Show, don't enumerate.** When the point is scale or contrast, a list of specific
items undersells it - fourteen service names read as "roughly double what I already
know". Concepts and categories convey breadth far better than instances do. Pick the
level of abstraction that makes the point land, not the level that is most complete.

**Logos over text, and only real ones.** Product marks drawn from memory look wrong
immediately and cheapen the whole deck. Either source the official asset pack (AWS
Architecture Icons, brand SVGs from the vendor) and inline the real files, or use
plainly generic glyphs that are obviously not trying to be logos. Never approximate
a brand mark.

**Reveal an argument, don't display it.** If a slide makes a multi-step case, use
fragments so each beat lands as he says it. A question slide should show the plain
question first, then highlight the deciding detail, then reveal the answer - the
pause is where the room does the thinking.

**One actionable line beats one clever line.** Closing callouts should be usable
rules ("move as far right as the requirements allow"), not observations ("there is
probably a service for this").

## What "boxy" means, and why he rejects it

A grid of equal, evenly-bordered panels reads as machine-generated. It is the
default an LLM reaches for and he will call it robotic. Avoid:

- Rows of identical bordered cards, all the same size, evenly spaced
- Full borders on everything
- Big-number stat tiles as a slide's main content - he dislikes these
- Uniform two- or three-column grids repeated on every slide

Reach instead for the patterns in `references/patterns.md`: journey lanes with
connectors, left-border callouts, icon clusters split by a vertical divider,
asymmetric grids, and the three-block flow with arrows between. Vary the shape
slide to slide.

## Process

**1. Ask for a reference deck.** He usually has one. Read it before writing anything
and lift its structural idiom - the patterns, the spacing, the way it handles icons.
Matching an existing deck is far more reliable than inventing a look.

**2. Agree the structure before building.** Typically context first, then N pointers
or beats, one per slide. Four slides is a common shape. Confirm the count and the
spine rather than assuming.

**3. Draft, then cut hard.** Expect the first draft to be too dense - his feedback
will be "too much detail and text", and the fix is always cutting, never
rearranging. Budget for two passes.

**4. Verify it renders.** Screenshot it or ask him to look. Layout bugs are common
and invisible in source.

## House style

Reuse `references/template.html` - it carries the working chrome and needs no
rebuilding. Key facts about it:

- Fixed **1600x900** canvas, scaled to fit the viewport via a CSS transform
- Curve palette in `:root` - navy `#000D45`, primary `#0022B3`, cyan `#00C0FF`,
  tint `#F0F4FF`, plus green/yellow/pink accents
- Century Gothic / Urbanist / Segoe UI stack
- Arrow keys, space and PageUp/PageDown navigate; fragments advance before slides
- **F** or the top-right button toggles fullscreen; the nav dots hide in fullscreen
- Everything inlined - no external files, no CDN, so it works offline in a meeting

Typography floor: **body text no smaller than 15px, headings 22px+**. If content
will not fit at those sizes, the content is wrong, not the type.

Voice rules carry from `issei-voice`: British English, hyphens with spaces rather
than em-dashes, no corporate register, sentence-case headings.

## Technical traps

These have all bitten in practice.

**Inline SVGs must be told to scale.** An SVG with hard-coded `width="54"` inside a
46px container with `overflow:hidden` gets *cropped*, not resized. Always add
`.ic svg { width:100%; height:100%; display:block; }`.

**Do not write CSS `content` escapes through a script.** `content:"\2713"` gets
mangled by shell and Python escaping layers into a control character. Write the
literal character - `content:"✓"` - into a UTF-8 file.

**Never regex-surgery nested HTML.** Rewriting a block with a pattern that spans
`</div>` boundaries silently eats a closing tag and collapses the layout. Rebuild
the whole section instead, and afterwards assert that `<div` and `</div>` counts
match before declaring success.

**Heredocs choke on this content.** HTML full of quotes, apostrophes and backticks
breaks bash heredocs. Use the Write tool for whole files and a Python script file
for surgical edits.

## Self-check before showing him

- Could he say any of this out loud instead? Then it should not be written.
- Any personal metric, score or number he would rather narrate?
- Does any slide use the same layout shape as the one before it?
- Is anything a grid of equal bordered boxes?
- Are all logos real, or plainly generic?
- Any body text under 15px, or a block that will overflow 900px?
- Do the fragments match the order he would speak in?
- Do `<div` and `</div>` counts balance?
- Does the closing line give a rule he can act on?
