---
name: blog-voice
description: Draft and edit long-form technical blog posts in Issei's voice. For the portfolio site (issei.dev / personal domain), substantial PR descriptions, ADRs published externally, and long-form LinkedIn or Substack pieces. Use whenever the user asks to "draft a blog post", "write up X", "turn this ADR into a blog post", "review my draft", "edit this post", "rewrite this in my voice", "make this less AI", "fix the AI cadence", or shares a draft of long-form technical content and asks for feedback. Do NOT use for short async comms (Slack, email, Jira); use issei-voice for those. Composes with issei-voice on framing, British-English conventions, and the no-em-dash rule.
---

# Blog voice

Long-form technical writing for an external audience: FAANG-level engineers, AI-lab researchers, senior practitioners in data, platform, cloud, and applied AI. The bar is higher than internal Confluence and different from Slack. The audience reads a lot, distrusts marketing prose, and recognises AI-generated cadence within two paragraphs.

The goal is to read as something the author actually thought about, in language the author actually uses, with the rhythm of someone who has written more than a few of these.

## Read first

Before drafting or editing, read in this order:

1. **`references/exemplar-annotated.md`** for one before-and-after passage from Issei's own drafts, annotated for how the patterns land. This is the highest-signal calibration in the skill.
2. **Two or three of Issei's existing drafts** at `C:\Users\IsseiKuzuki\website\src\content\blog\` and `C:\Users\IsseiKuzuki\website\src\pages\projects\`. These are works-in-progress, so read them for *register*, not as templates. The drafts have the AI cadence (the symmetry, the "three things upfront", the em-dashes, the dramatic "X isn't Y. It's Z." pivots) that this skill exists to fix.
3. **`references/writers.md`** when you need a richer reference for any of the eight named voices, or to argue from a specific writer's move.
4. **`references/shapes.md`** when picking the structural shape for the post.

If those paths are empty or the user is drafting on a different machine, ask for sample drafts before starting.

## Voice in one paragraph

Plain, specific, opinionated. Concrete numbers and named tools over generic adjectives. Hedge by framing ("in my view", "I've found"), not by weakening the claim itself ("might perhaps potentially"). Vary sentence length deliberately. A short sentence after three long ones lands. Open conversationally, never with a hook. Close by stopping, never with "the takeaway is". Comfortable with parenthetical asides (in real parentheses) for context, self-correction, or dry humour. British English. No em-dashes; the typographic em-dash (`—`, U+2014) is one of the strongest AI tells in 2026.

## Patterns to reach for

### Open conversationally, not with a hook

Senior writers open with an observation, a small piece of context, or a quiet declaration, rather than a thesis or a rhetorical question. "In March I wrote an ADR rejecting LangGraph..." lands. "Choosing a framework is one of the highest-leverage decisions an engineer makes" does not.

### Hedge by framing, not by weakening

The single biggest tell. State the claim flatly, then put the epistemic status on the *frame*. "In my view, Lambda memory is the wrong place to look for cost savings" beats "Lambda memory might potentially not be the right place to look for cost savings." Reach for "in my view", "in my eyes", "to my mind", "I've found", "I think", "as far as I can tell". Avoid "might", "could potentially", "may be worth considering".

### Vary sentence length deliberately

AI writes uniform sentences. Senior writers vary aggressively. A short sentence after three long ones is the most reliable rhythmic move in English prose. Read paragraphs aloud; if every sentence is 15 to 25 words, rewrite one to be five and one to be thirty.

### Parenthetical asides as thinking-aloud

Use them freely, for context, qualifier, self-correction, or dry humour. Use real parentheses, not em-dashes. Patrick McKenzie writes parentheticals on every paragraph; Marc Brooker uses them for honest qualifications ("I'm conflating two things here"). This is already part of Issei's chat voice ("(No rush)", "(should still be in Confluence Cloud)"); same instinct on a longer surface.

### Specific numbers over generic adjectives

"The pipeline is cheap" is AI prose. "The pipeline costs £1.50 to £3.00 per gameweek, of which 95% is the Anthropic API" is senior prose. When you reach for "significant", "substantial", "very", or "extremely", stop and find the number.

### Footnotes for tangents

Dan Luu and Marc Brooker use footnotes to hold context that would derail the main flow. AI uses parentheticals for everything (because it can't be bothered to organise a sidebar) and bibliographies at the end (which interrupt). Real numbered footnotes (`<sup>1</sup>` with a section at the bottom of the post) read as careful. Reach for them at the third tangent in a paragraph, not the first.

### Embed links inline

"I wrote about this in [The killer app of Gemini Pro 1.5 is video](url)". The link is part of the prose rather than a citation appended at the end. AI tends to append; senior writers weave.

### Anticipate the obvious objection

The reader is about to think "but what about X". Preempt it in one short paragraph, then move on. Signals you've thought about it without letting the post become defensive. Issei's LangGraph post already does this for "you could write this in plain asyncio", which is the right register.

### Close by stopping

The hardest one. Cut "the takeaway is", "in summary", "to recap", "the lesson is". Let the second-to-last paragraph carry the post. Will Larson's "For now, I'll be over here working on my pace" is the model: a small image, no synthesis.

### Show the seams

Admit uncertainty in surprising places. "I don't know why this works, but it does." "I changed my mind on this after three months." "I'm not sure how to fix it. Maybe nobody is." Those sentences are credibility. AI smooths every seam.

## Pick a shape, don't default

The biggest tell across Issei's existing drafts is structural uniformity: every post is hook, then three-or-five H2 sections, then synthesis paragraph. That symmetry is what makes the drafts read as batch-generated even when the content is original. Force structural variety. Pick a shape per post, deliberately.

See **`references/shapes.md`** for the five shapes worth rotating between (war story, argument essay, practical guide, confession, investigation), with notes on which existing draft wants which shape. The rough rule: the default should be war story or confession; the argument essay is the AI default and should be rationed.

## Anti-patterns: the AI tells

Each one breaks a senior-writer pattern. Fix on sight.

**Em-dashes.** Zero. The typographic em-dash (`—`, U+2014) reads as AI regardless of placement, and the en-dash (`–`, U+2013) reads almost as badly. Replace with commas, semicolons, parentheses, or sentence breaks. Hyphen-with-spaces (` - `) is allowed sparingly, at most once per 500 words, in line with the `issei-voice` rule for chat. For number ranges, prefer "£1.50 to £3.00" over "£1.50–£3.00".

**"X isn't Y. It's Z." dramatic pivot.** The short two-sentence rhetorical move that creates artificial profundity. "This isn't about cost. It's about discipline." / "The question isn't whether to do X. It's how." / "Less X. More Y." / "Not X. Y." These read as LinkedIn-influencer cadence even when the content is real. Rewrite as a single flat sentence stating Z, or a longer multiclause sentence that includes the contrast inline ("Z, rather than X"). The single-sentence "rather than" form is fine in moderation; the dramatic two-sentence pivot is not.

**"Three things upfront." / "Two things, in order."** Numbered framing devices used to chunk an introduction. Real senior writers don't number their points before the points have happened.

**"The interesting bit is..." / "The lesson is..." / "The takeaway is..."** Pivot phrases that tell the reader what to think next. Show, don't pivot.

**"Stepping back" / "Zooming out" / "At a high level"**. Meta-framing labels. Already forbidden in `issei-voice`; same rule here.

**Symmetric structure.** Hook (3 sentences), H2 (4 paragraphs), H2 (4 paragraphs), H2 (4 paragraphs), close (3 sentences). If your post diagrams like this, it reads as AI even when the content is real. Vary aggressively.

**Equal paragraph lengths.** Some paragraphs should be one sentence, some should be twelve lines. Uniformity is the tell.

**The "rule of three" everywhere.** Three lessons, three bullets, three sections. Reach for two, four, or seven when those are honest.

**Closing synthesis paragraph.** Cut. Let the post end on its last real point.

**"It's worth noting that..." / "It bears mentioning that..."** Throat-clearing. If it's worth noting, note it.

**Universal applicability claims.** "More generally...", "This pattern applies broadly to...". Stay in the specific story.

**Corporate-speak.** "Leverage", "circle back", "synergy", "best-in-class". Already forbidden in `issei-voice`.

## Issei overlays

The Issei-specific layer on top of the patterns above.

- **British English throughout.** Optimise, behaviour, colour, realise, prioritise. Sweep before publish; AI defaults slip in.
- **Framing words.** "In my view", "in my eyes", "to my mind", "I think", "I've found", "I'd lean towards". Avoid "I posit", "I contend", "I would argue", which are too formal-essay.
- **Run-ons and comma splices are fine.** Real Issei stitches with commas and "and"s. The instinct works in long-form when not used on every sentence.
- **No em-dashes (same as `issei-voice`).** Blog voice was previously a deliberate divergence allowing em-dashes; that's been retracted. Use commas, semicolons, parentheses, or sentence breaks. Hyphen-with-spaces (` - `) follows the `issei-voice` rule, sparingly.
- **Acronyms unexplained where the audience would know them.** S3, Lambda, Step Functions, LLM, RAG, SigV4, OAC, ADR, pgvector are assumed known. ECS, FoDI, CDT need explanation on first mention for external audiences.
- **Specific tools and versions.** `claude-haiku-4-5-20251001`, `nomic-embed-text:v1.5`, `Aurora DSQL`. Generic ("the embedding model") reads as AI.
- **Cross-link to ADRs and to other posts.** "I rejected this approach in [ADR-009](url)" lands harder than restating the rejection inline.
- **Dates and seasons.** "In March I..." / "Six weeks later..." / "After two months of running this..." Time-stamps the post in a way that resists the dateless AI register.

## Self-check before delivering a draft

Run this once. Fix anything that fails.

**Structure**
- Picked a shape from `references/shapes.md` and named it (war story / argument / guide / confession / investigation).
- Paragraph lengths vary; at least one one-sentence paragraph, at least one paragraph over six lines.
- No closing synthesis paragraph.
- If 1,500+ words, has at least one footnote.
- H2 sections are not numbered ("First lesson", "Second lesson") or otherwise symmetric.

**Voice**
- Opening is conversational, not a hook.
- 2+ "in my view" / "I've found" framings; zero "might potentially" / "could perhaps" weakening hedges.
- Sentence variety: at least one short declarative under 8 words per ~300 words.
- 1 to 3 parenthetical asides per 300 words, written with real parentheses.
- "Significant", "substantial", "very" replaced with numbers where possible.
- Links inline, not appended.
- British English swept.
- **Zero em-dashes** (`—`, U+2014) and zero en-dashes (`–`, U+2013). Hyphen-with-spaces (` - `) at most once per 500 words.
- **Zero "X isn't Y. It's Z." two-sentence pivots.** Single-sentence "rather than" forms are fine in moderation.
- Zero "stepping back", "zooming out", "the interesting bit is", "the takeaway is", "it's worth noting".
- Zero corporate-speak.
- Anticipates at least one obvious objection.

**Senior-signal**
- 1+ specific named tool / version / file / line number.
- 1+ date-stamp or time-locator.
- 1+ cross-link to an ADR, repo, or prior post.
- 1+ place where uncertainty or a changed-mind is admitted.
- Closes by stopping, not summarising.

If 3+ checks fail, rewrite before showing. The most common failure mode is closing-paragraph synthesis; worth a hard look on every post.

## Composition

- **`issei-voice`** is the sister skill for short-form chat. Same person, different surface. British English, framing-not-weakening, and no-em-dash rules are shared.
- **`knowledge-vault/voice/personal-projects.md`** covers READMEs and LinkedIn long-form. Read in addition for project landing pages.
- **`knowledge-vault/voice/explaining-code.md`** covers PR descriptions and Confluence Behaviour sections. Some blog posts are dressed-up PR descriptions; read both if so.

## Scope

Long-form technical writing for external audiences: blog posts (portfolio site, Substack, dev.to), substantial PR descriptions meant to be read externally, ADRs published outside the team, LinkedIn long-form. Not for short async comms (use `issei-voice`), internal Confluence (use `intech-tools` doc-hygiene), code comments (use the repo's coding-standards skill), or marketing/sales copy (out of scope).

If asked to draft in someone else's voice or a publication's house style, flag the limitation and ask for samples before attempting.
