---
name: exec-summary
description: Turn a saturated working doc, completed spike or PoC, research dump, or sprawling notes into a tight, outcome-focused artefact a human digests in ~5 minutes - exec-summary-led, diagram doing the heavy lifting, ruthlessly concise, explicitly NOT AI slop. Use this skill whenever the user asks to "write this up", "turn this into a doc / design doc / ADR / summary", "synthesise this", "condense this", "make this digestible / readable", "clean this up into a doc", "exec summary", "component design from this", or shares a long or saturated doc and wants the durable outcome version. Also use when producing a Confluence-bound design, decision, or findings doc from messy source material, or when an AI-written doc has become an indigestible wall of text and needs cutting down. Do NOT use for short async messages (use issei-voice), long-form blog posts (use blog-voice), or when the user genuinely wants exhaustive reference detail rather than a digest.
user-invocable: true
---

# Exec-summary docs

AI's default failure mode on docs is to write, and write, and write - correct but indigestible, so no human actually reads it. This skill is the antidote: produce the *outcome* version of a doc - the load-bearing 20%, shaped so a reader gets the whole picture in ~5 minutes and finds detail only where it earns its place.

The source material - a spike, a PoC, a saturated working doc, a research thread - is allowed to be exhaustive. That is its job. The outcome artefact is not. Your job is to extract, not transcribe. The instinct to be "complete" is exactly the instinct that produces slop here.

## The shape: pyramid

Lead with the conclusion, supporting decisions next, evidence at the base. Assume the reader stops after the first screen.

- Open with a short exec summary - what this is plus the headline decisions, in a few sentences. A reader who reads only this should still come away with the whole picture.
- Then the key decisions or design, each stated as an outcome.
- Evidence and data sit at the bottom, or in a separate doc (see the pair pattern below).

This is the Curve Confluence house style (pyramid, concise, durable, decision-grade), so docs produced this way drop straight into Confluence.

## Outcome, not process

State the decision and the design as they *are*. Don't narrate the journey to them.

- Not: "we tried a query-time view, found it 10x too slow, so we switched to a materialised table."
- Yes: "the serving table is materialised (10-83x faster than a query-time view - see evidence)."

Process context earns a place only when it is genuinely load-bearing: a counterintuitive result a reader would otherwise re-litigate, or a rejected option that's the obvious-but-wrong default worth pre-empting. Everything else is noise the source doc can keep.

## The detail budget

This is the judgment that makes or breaks the doc, and it's the part only you can do. Default to one-line, outcome-only statements. Spend words on detail *only* where one of these holds:

- It's non-obvious or counterintuitive - a reader would be surprised or get it wrong without the why.
- It's a binding contract someone must honour - e.g. "consumers must pin the version per request, or reads tear." Get these exactly right; they are the load-bearing constraints.
- The why is what stops a future engineer from silently undoing it.

Everything else is a one-liner. The source over-explains by nature - resist mirroring it. If you're explaining something a reader could derive from the code, you're over-spending: link instead.

## Don't restate what lives elsewhere

Schemas, DDL, API signatures, function bodies live in the codebase - link to them, don't paste them. The doc captures the *why* and a *high-level what*. A design doc that inlines a 60-line `CREATE TABLE` has already lost. Link to wherever the canonical version actually lives: repo-relative paths for code and in-repo docs, the Confluence or Jira URL for anything that lives there. (This also matches the Confluence house rule: the code is the source of truth, the doc is the rationale.)

## Diagrams do the heavy lifting

A clean diagram replaces paragraphs. If a relationship, flow, or structure can be shown, show it - then prose only adds what the diagram can't. Use the team plugin's `drawio-diagram` skill, or d2 (`--layout elk` gives clean orthogonal edges). Render it and actually *look* at it before shipping - a diagram you haven't viewed is not done.

## Write it standalone

The artefact reads as though nothing preceded it. No "as decided previously", no "following on from the spike". Reference other systems and components by NAME - the experience layer, the data-service, the analytics contract - never by author or owner ("Luke's service", "the thing Matt owns"). Names are durable; attributions rot and read as gossip. Referencing a canonical artefact by its ID is the good kind of name - ADR-032, the analytics data contract, CDT-229 - link them where useful; the rule is only against attributing work to people.

## Often a pair, not one doc

A clean split that recurs:

- a **design / decision doc** - the exec summary, the decisions, the diagram, the high-level shape. The durable thing implementers and stakeholders read.
- a **lightweight evidence doc** it links to - measured numbers, benchmark tables, conditions. The "prove it" base.

Splitting stops the design doc re-saturating with data tables, and lets each be read at its own depth. Use judgment - a small writeup needs only one doc; don't manufacture a pair.

## Composes with

- `issei-voice` for the prose itself - British English, no em-dashes (use ` - `), no corporate-speak, hedge by framing not by weakening the claim.
- the Curve Confluence house style for anything Confluence-bound (this skill already aligns with it).
- `drawio-diagram` or d2 for the diagram.

## A quick before / after

Slop (source-faithful, indigestible):

> In order to determine the optimal serving architecture, we evaluated several approaches. Initially we considered a query-time view, which involves joining the attributes and dimension tables at read time. However, benchmarking revealed that this approach was significantly slower, with latencies ranging from 1.4s to 6.5s depending on the query shape. We therefore pivoted to a materialised approach. It is worth noting that the materialised table is denormalised...

Outcome (what this skill produces):

> The serving table is materialised, not a query-time view - 10-83x faster (evidence). It carries every dimension a dashboard filters on, so every read is a single-relation filtered scan.

Same information that matters, a quarter of the words, no journey, no throat-clearing.

## Self-check before delivering

Scan it as a skim-reader would:

- Does the exec summary *alone* convey the whole picture?
- Is every section longer than a line earning it (non-obvious / binding / load-bearing why)? If not, cut to a one-liner.
- Any process narrative that isn't load-bearing? Remove it.
- Any schema, DDL, or code pasted that should be a link? Link it.
- Any component referenced by author rather than by name? Fix it.
- No preamble ("in this document we will"), no closing recap, no bold sprinkled mid-prose, no filler ("it's worth noting", "it's important to", "essentially")?
- Could a busy reader get the answer in ~5 minutes?

If any are off, rewrite before showing. Cutting is almost always the fix.
