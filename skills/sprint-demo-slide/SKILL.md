---
name: sprint-demo-slide
description: Build a single-page HTML slide for a CDT (or other team) sprint demo, structured around James Hanson's spine (work, product outcome, incremental change, details) and rendered in Issei's visual style (navy + cyan, hero proof-moment, three evidence cards, forward strip). Use whenever Issei says 'make me a sprint demo slide', 'build the demo slide', 'draft a sprint slide', '1-slide for the demo', 'sprint demo slide', 'help me plan the demo slide', or mentions preparing a sprint demo. Input is a brief on what shipped, plus optional Confluence URLs, Jira tickets, and PRs - fetched in parallel before drafting. Asks four clarifying questions before authoring - dataset specifics, screenshot vs live demo, slot length, output filename. Output is a standalone 1600x900 HTML at the chosen path. Do NOT use for full slide decks (multi-slide), pitch slides explaining a future decision (that's a 4-section pitch shape, out of scope), or generic web design tasks.
user-invocable: true
---

# Sprint demo slide

The CDT demo cadence has a missing piece per James Hanson's steer: people share *what* they did and *details*, but skip *which part of the product* and *what changed since last sprint*. This skill bakes that spine into a one-slide visual so the framing is structural, not aspirational.

The slide is **evidence, not pitch.** A 3-minute demo slot needs one moment that proves the work is real - typically a screenshot of the new thing running. Everything else is supporting detail.

## The spine, James-shaped

Every slide produced by this skill must structurally hold these four beats:

1. **What I've been working on.** Plain-named. ("The CDT analytics serving layer.")
2. **Which part of the product it contributes to.** Name the surfaces. ("Standalone Chat, Brand Monitoring, the future read API.")
3. **Incremental change since last sprint.** The before-after. ("Last sprint: design on paper. This sprint: live in dev with real data.")
4. **Details.** The hero - one proof moment.

The slide layout maps these:

- **Header** carries (1) - the H1 names the work.
- **Hero** carries (4) - one proof moment, big and central.
- **Cards band** carries (3) - three evidence cards making the incremental change concrete.
- **Bottom strip** carries (2) - names the product surfaces and what comes next.

This ordering is deliberate. (1) is the title. (4) gets pride of place because evidence is what the room remembers. (3) builds the case for "real". (2) closes the loop to product outcome.

Bullets (2) and (3) are the missing pieces in current CDT demos - the slide structure forces them to be present.

## Read the inputs first

When Issei provides Confluence URLs, Jira tickets, and PRs in the brief, fetch them before drafting. In parallel where possible (one assistant message, multiple tool calls):

- **Confluence pages**: invoke the `intech-tools:confluence` skill - it runs the mandatory diagram-aware read protocol.
- **Jira tickets**: `mcp__04744edc-d21b-4d7d-94d6-61d44e598e10__getJiraIssue` with `responseContentFormat=markdown`. Use `curve-analytics.atlassian.net` as `cloudId`.
- **PRs**: `gh auth switch --user Issei-curve` first, then `gh pr view <num> --repo <owner>/<repo> --json title,body,state,files,commits,reviews,additions,deletions,changedFiles`.

Use the inputs to extract: what shipped, what the schema/contract looks like, what numbers are real, what the previous-sprint baseline was. Do NOT inline raw ticket/PR text into the slide - extract substance, render in Issei's voice.

## The four questions

Before authoring, ask via `AskUserQuestion` (skip any the user has volunteered in the brief):

1. **Live demo or screenshot panel?** Screenshot is safer - the slide carries the proof and nothing can break mid-demo. Live is more powerful when the service is reliable.
2. **What dataset / numbers?** Be precise. "Real client dataset" lands harder than "synthetic". Surface row counts, date ranges, percentages - whatever's real.
3. **Slot length?** 3 minutes is the default. 6+ allows more density on the slide.
4. **Output filename and folder?** Default: `<topic>-sprint-demo-slide.html` next to previous slides at `C:\Users\IsseiKuzuki\Claude\CDT\`.

## Visual structure

Dimensions: `1600x900`, scaled in a `.slide` element on `#e9ecf1` body. Flex-centred. Same shadow and radius as the canonical example.

### Header

- Eyebrow: small uppercase cyan text, 11px, letter-spacing 0.14em. Pattern: `CDT &middot; <Topic> &middot; Sprint update`.
- H1: 34px navy, line-height 1.1, letter-spacing -0.01em. Plain English statement of the headline change. Avoid jargon.
- Subtitle: 16px ink-soft. One sentence framing what the change is.
- Right side: a `.live-pill` if the status is "live in dev" or equivalent - green dot + uppercase label. Drop it if status doesn't fit.

### Hero

- Numbered section label (`1` in a navy circle) + uppercase cyan title naming the proof moment.
- Two-column grid, ~1.05fr / 0.95fr. Left = code or screenshot artefact; right = result or output.
- Left panel uses dark code styling (`#0e1b2d` bg, monospace, syntax-highlighted: keywords cyan, strings amber, functions soft-green, comments grey-italic). Add a tiny top-right `panel-label` like `query &middot; clickhouse dev`.
- Right panel: white card with head row (label + green timing chip), result table with right-aligned numerics, brand-name first column in navy-bold, italic footer making the rhetorical point (one short line - this is where the previous-deck callback lives).

### Evidence cards band

- Light green gradient background (`var(--live-bg)` to `#f5fbf7`).
- Section label (`2` navy circle + cyan title with `&middot; incremental since last sprint`).
- Exactly three cards. Each: small green ticker dot + uppercase label, h3 (15.5px navy), short body. One card can carry a small monospace tree/diagram (the schema-as-code card is the standard place for this) instead of prose.

Three is the rhythm. Two reads thin, four reads cluttered.

### Bottom strip

- Numbered section label (`3` navy circle).
- One sentence. Starts `**Next sprint &rarr;**`. Names the product surfaces explicitly by name (Brand Monitoring, Standalone Chat, future read API). Closes with the connection back to product outcome.

## Template

`references/template.html` ships with this skill. It is a complete working slide (the first invocation, ClickHouse / Water DDT) with inline `<!-- REPLACE: ... -->` comments at every swap point and `DO NOT MODIFY` markers around the visual system.

To author a new slide:

1. Copy `references/template.html` to the target output path (or read it and write the adapted version directly to that path).
2. Walk every `<!-- REPLACE: ... -->` block and swap in content from the brief. The existing content is a worked example - use it to calibrate tone, density, and structure.
3. Keep the `<style>` block, the `1600x900` dimensions, the class names, the section numbers, and the CSS variable names unchanged.
4. The result-foot italic line is where the rhetorical callback to the previous deck lives. Earn it; do not fabricate.

For the older 4-section pitch slide shape (one explaining a *future* decision rather than evidence of progress), that's out of scope for this skill. If the user asks for one, surface the mismatch - don't silently produce one. Historical examples of both shapes live at `C:\Users\IsseiKuzuki\Claude\CDT\` (`clickhouse-sprint-demo-slide.html` for this shape, `clickhouse-exec-demo-slide.html` for the pitch shape) if reference is useful.

## Colour palette

```css
--navy: #0f2d52;
--cyan: #00bfd8;
--ink: #0f1f33;
--ink-soft: #495b73;
--rule: #d9e2ec;
--dim-bg: #f7f9fc;
--live-green: #16a34a;
--live-bg: #ecfdf5;
--live-band-bg: #f5fbf7;
--code-bg: #0e1b2d;
--code-ink: #e6eef9;
--code-keyword: #79c8ff;   /* SQL keywords */
--code-string: #f0c674;    /* string literals */
--code-fn: #b7e2c0;        /* function names */
--code-comment: #6c7a8e;   /* SQL comments */
```

## Voice for slide prose

Same rules as `issei-voice`:

- Plain English. Short sentences. Active verbs. No corporate-speak.
- British English.
- No em-dashes - use ` - ` (space-hyphen-space) or restructure.
- No emoji. (Match the previous deck precedent.)
- One claim per card. Resist stuffing.
- No "we successfully" / "we worked on" - state what shipped.

The italic result-panel footer is where the rhetorical callback to the previous deck lives. For the ClickHouse one that was *"Filter and sum. No joins composed at query time. No semantic model in the loop."* - short, earned, tied to the previous slide's argument. Earn it; don't fabricate one.

## After authoring

End the response with three things, in this order:

1. The path the slide was written to.
2. What's baked in to match the James framing (specifically call out bullets 2 and 3 since those are the new pieces).
3. What Issei should swap before presenting - usually: the result table contents, the timing chip, dataset specifics on card 3, and any SQL that depends on schema not yet verified. List them as a punch list.

Optionally suggest one thing worth saying *out loud* during the demo that doesn't fit on the slide (a recent design realignment, a caveat, a forward-looking aside) - this gives the talk room for nuance without crowding the visual.

## Anti-patterns

- **Inlining ticket numbers as bullet points.** The slide is for the room, not Jira. Names of things, not keys. If a ticket key matters, parenthesise it after the substance.
- **Stuffing the hero with multiple queries or panels.** One moment that proves real. More than one and none of them land.
- **Forgetting bullet (2).** The bottom strip exists *because* this is the missing piece in current demos. Don't drop it for space.
- **Writing the title as a question.** "What's new this sprint?" is empty. State the change: "X is live in dev."
- **Generic progress language.** "Made progress on X" is content-free. Either name the shipped thing or omit.
- **Quoting PR or ticket descriptions verbatim.** Extract substance; render in voice. Source is allowed to be exhaustive; the slide isn't.
- **Adding a fourth or fifth evidence card.** Three. The visual rhythm depends on it.
- **Pitch-shaped content.** If the slide explains why a *future* decision is right, this is the wrong skill - that's the 4-section pitch shape. Sprint demos show what's *now real*.
- **Fabricated impressive numbers.** Either screenshot the actual query result and timing, or use plausible placeholders the user explicitly approves before the demo. Never invent numbers and present them as real.
- **Skipping the read step.** When the user gives URLs/tickets/PRs, fetching them first is non-negotiable - guessing at substance from titles produces a slide that doesn't match what shipped.
- **Asking all four questions when the user already answered some.** If the brief specifies the dataset and the slot length, only ask the missing ones. Don't make the user repeat themselves.
- **Em-dashes in the slide prose.** The voice rule applies to slide content, not just chat. Use ` - ` or restructure.
