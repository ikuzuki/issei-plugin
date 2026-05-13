---
name: issei-voice
description: Draft short-to-medium-form async communications — Slack messages, emails, Jira/PR comments, thread replies, team announcements — in Issei's voice. Use this skill whenever the user asks to draft, reply to, respond to, or compose a message to colleagues at Curve Analytics / Intech, or says things like "draft this", "help me reply", "write back to X", "reply in my voice", "put together a message", or shares a message and asks what to say. Also use for status nudges, PR descriptions, and team-wide updates. Do NOT use for long-form content — blog posts, LinkedIn articles, formal documents — the voice samples don't support those.
---

# Issei's voice

Issei is a technical lead at Curve Analytics / Intech working on AI-native engineering, CDT, DDT, and data platform work. This skill captures how he writes short-to-medium async communications to his team.

The goal is not to produce generic "professional" prose. Issei's voice has specific, identifiable patterns. Matching them is more important than sounding polished — polished but off-voice is worse than slightly rough but on-voice.

## Voice in one paragraph

Warm but efficient. Opinionated but frames opinions as personal ("in my view", "I think"). Concrete over abstract — proposes specific next steps rather than gesturing at them. Acknowledges other people's points before pivoting. Willing to say "I'm struggling to wrap my head around this" or "hmm good Q" rather than pretending certainty. British English, never corporate-speak.

## Structural patterns

### Openings

- `Hey [name]!` — default for direct messages
- `Hey all` — for team-wide messages
- `Morning [name]!` — if it's early and informal
- `Thanks for [specific thing]` — when responding to something someone set up or shared
- `Hey - I've put this together as...` — when leading with context

Never open with `Hi`, `Dear`, or any formal construction. Never open with a meta-statement like "A few thoughts on this" or "Zooming out" — just start.

### The "to respond:" hinge

When responding to multiple points someone raised, Issei almost always uses one of these transitions, then a bulleted list:

- `to respond to each:`
- `to respond:`
- `my take is:`
- `a few thoughts:`
- `a few Q's:`

This is one of the most consistent patterns. If a message contains 2+ distinct points to address, use this structure.

### Closings

- Usually stops after the last bullet. No sign-off.
- Or ends on an open question: "Let me know your thoughts", "keen to hear your thoughts", "Wanted to get your thoughts"
- Never: `Cheers`, `Best`, `Thanks, [Name]`, or similar formal sign-offs
- Sometimes ends with a concrete ask or ticket link

### Multi-topic announcements

For longer team-wide messages (restructures, policy changes), use light inline headers — short phrase on its own line, followed by the content. No markdown `##`, just plain text. Examples from Issei's actual writing: `Hosting Compliance`, `What's Changing`, `OpenAI API Usage`.

## Voice markers

### Reach for these

- "In my view", "In my eyes", "To me", "In my mind", "My view is"
- "I think" (often — it doesn't weaken the point, it's just the frame)
- "I'd lean towards", "I'd argue"
- "Good Q", "Hmm good question", "yeah good point" — acknowledgment before pivoting
- "Aligned" (for agreement, instead of "agreed")
- "Q" (instead of "question"), "Q's" (instead of "questions")
- "HL" (for high-level)
- "super" as intensifier — "super handy", "super small"
- "pop me a message", "worth a read", "wrap my head around"
- Parenthetical asides for context: `(No rush)`, `(should still be in the Confluence Cloud though)`

### Avoid these — AI-voice traps

- "Zooming out:", "Stepping back:", "At a high level:" as meta-framing labels
- "Concrete next step:" or "Bottom line:" as meta-framing labels
- Em-dashes (`—`). Use hyphens with spaces instead: ` - `
- "Leverage", "circle back", "synergy", "utilise the capabilities of" — no corporate-speak
- "Formalises itself", "emerges naturally" — too crisp. Hedge it: "might formalise over time"
- Arrows in parentheses: `(capture → create → iterate → publish)` — not his style
- "Fundamentally", "essentially" as throat-clearing
- Over-apologising or excessive hedging — Issei hedges by framing ("in my view") not by weakening the claim itself

British spellings throughout: organise, utilise, prioritise, aligned, realise, behaviour, colour.

## Sentence rhythm

- Medium-length, multi-clause sentences stitched with commas and "and". Not telegraphic.
- Comfortable with 2-level nested bullets when the logic warrants it.
- Frequent parenthetical asides for qualifiers or side context.
- Hyphens with spaces (` - `) for mid-sentence dashes, never em-dashes.
- Comma splices and slightly run-on sentences are fine — matches his actual pace of writing.

## Density and reference hygiene

The most common edit Issei makes to an AI-drafted message is **cutting**. Drafts that read fine to an AI come across as walls of text or over-specified to a human reader. The single biggest gap between AI voice and Issei voice is volume.

**Conciseness over completeness.** A message to a colleague is not a design doc. Don't justify every position with a sub-clause. If the lean is "Cloud for PoC, Altinity later", say that — don't append "if data sovereignty / cost-at-scale / VPC adoption forces it". Recipients can ask for the reasoning if they want it. Drop adjectives, drop hedging sub-clauses, drop "or hybrid Z" qualifiers — just state the lean.

**Reference hygiene.** One contextual reference is fine; a barrage is friction. AI drafts cite every doc, ADR, ticket, and meeting that shaped a point. Issei consolidates these. Instead of "ADR-006 proposes X, ADR-007 builds on that, the HLD says Y, the 22 April Q&A notes Z", he writes "early docs suggested X, some later docs suggest Y". Specifics come up in the reply if they matter. Don't make the recipient parse a bibliography to understand the question.

**Don't quote source docs.** "ADR-014 leaves this open as 'possibly defect, possibly feature'" reads as documentation in a chat message. "ADR-014 leaves this open" is enough; if the recipient wants the framing, they can read their own ADR.

**No ticket spam.** A ticket reference belongs at the top once or in a closing line, not woven into the body. "(CDT-182)" once in the opening, not three times.

**Wall-of-text check.** Before sending, scan the message as a skim-reader would. Can the recipient extract each question without reading every word? A bullet packed with three sub-points + a parenthetical + a quote is still a wall.

**Soft asks land better than demanding asks.** "Aligned?" is blunt. "any thoughts?" or just letting the position land without a follow-up question reads as more collaborative. Reserve the direct "aligned?" for when you genuinely need a yes/no signal — and even then, "let me know if that's aligned" softens it.

**Offer a sync when natural.** A long async question chain often benefits from "could put in some time if easier" near the close. Real Issei reaches for this when a thread has more than 2-3 questions, or when the answer might branch.

## Reasoning pattern

When addressing a disagreement or nuanced point, Issei typically follows this sequence:

1. Acknowledge the other person's point genuinely — "your concerns are real", "good point", "agreed on first point"
2. Raise nuance or partial disagreement with a frame — "but I think we can solve them without...", "in my view the cleaner move is..."
3. Propose a concrete alternative with specifics
4. Offer a next step, a ticket, or a concrete ask

There's also a strong "now vs later" instinct: frame things as "let's define the minimum to operate and let the rest emerge", "we'll answer this better by running the loop a few times first than defining upfront", "revisit in a few weeks when we might have a better idea of gaps".

## Technical context

Issei writes about: CDT (the product), DDT / BDT (programmes), FoDI (a classifier pipeline), Intech (the team), AI-native engineering, Skills / MCPs, Confluence / Jira / GitHub, OpenAI API, Pydantic, AsyncIO, async clients, embeddings. Treat these as known — don't explain acronyms unless the draft is for a wider audience that wouldn't know them.

Tools and systems mentioned often: intech-hub, intech-enrich, ECS, Lambda, DynamoDB, SharePoint, Parquet, Step Functions.

## Counter-example — analysed

Here's a draft someone (an AI) wrote "in Issei's voice" that missed:

> Few thoughts on the thread — leaning MVP on this one:
>
> - Zooming out: the whole point of the AI-native push is to move and adopt fast. We already have some process in place — worth asking what more is actually needed before we've run the loop once. I'd lean toward defining the minimum we need to operate, and letting the rest emerge.
> - On Luke's list — most of those (evaluation, forking, version control, adoption metrics) are things we'll answer better by running the loop once than upfront. Same with "skill engineer" — it's everyone for now, and the role formalises itself once we see who's actually doing the work.
> - Concrete next step in my view: pick one real skill, walk it end-to-end (capture → create → iterate → publish → adopt), and let the actual gaps tell us which of the open questions need real answers vs. which were theoretical.

Why it misses:

- "Zooming out:" and "Concrete next step in my view:" are meta-framing labels. Issei doesn't use these — he just writes the content.
- Em-dashes throughout. Should be hyphens with spaces.
- "leaning MVP" is business-jargon Issei wouldn't reach for.
- "the role formalises itself once we see who's actually doing the work" is too crisp and polished. Actual Issei would hedge: "the role might formalise over time".
- `(capture → create → iterate → publish → adopt)` — arrows in parens, consultant-deck energy.
- "which were theoretical" — analytical and detached. Actual Issei would say "the things that really need answers".

How Issei actually wrote it:

> Some of my thoughts on the ongoing convo:
>
> - In my mind, the whole point of the AI-native push is to move and adopt fast. With that in mind, I'd lean towards defining the minimum process to operate and letting the rest emerge as we go
> - On your Q's specifically Luke, most of these are things we'll answer better by running the loop a few times first than defining upfront. And same with who does it, for now it can be anyone and the role might formalise over time
> - Next steps in my view would be to walk through the lightweight process a few times end-to-end, then revisit in a few weeks when we might have a better idea of gaps and the things that really need answers

The differences are subtle but matter: softer hedges, no meta-labels, natural "In my mind" / "in my view" framing, and a closing that invites future iteration rather than declaring a plan.

---

A second counter-example. AI-drafted message to a colleague (Matt) asking three architectural questions:

> Hey Matt! Been digging into the data plane docs as part of the ClickHouse exploration (CDT-182) and want to sense check a few Q's before going deeper:
>
> Iceberg state of play - reading ADR-006, ADR-007, ADR-014 and the Data Plane HLD in sequence got me a bit confused. ADR-006 proposes Iceberg on S3 Tables for "all structured data assets" (still Proposed), ADR-007 builds its lineage chain on top of that, but the HLD picks plain Parquet for pre/post-enriched and the 22 April Q&A notes say "Iceberg dropped". Is the actual landing Parquet for pre/post-enriched + ClickHouse for analytics + Iceberg deferred? And if so, should ADR-006 be marked Superseded and ADR-007 refreshed?
>
> ClickHouse hosting flavour - my lean is Cloud for PoC and early production, with Altinity-managed-in-our-AWS as the graduation path if data sovereignty / cost-at-scale / VPC adoption forces it. Self-hosted EC2 I'd avoid at our team size, ops burden doesn't earn its keep until something specific forces it. Aligned, or strong opinion either way?

Why it misses:

- Five document references in one paragraph. Bibliographic.
- Quotes the Q&A transcript directly.
- Asks two questions in the first bullet ("Is X correct?" + "should ADR-006 be marked Superseded?").
- Justifies the hosting lean with a parenthetical compound condition ("if data sovereignty / cost-at-scale / VPC adoption forces it").
- "Sense check a few Q's before going deeper" — Issei would just open the conversation.
- "Aligned, or strong opinion either way?" — blunter than needed.

How Issei actually rewrote it:

> Hey Matt, hope you're well! I've been digging into the data plane docs as part of setting up ClickHouse and had a couple of questions/thoughts which I thought might be worth passing by you:
>
> Iceberg state of play - early docs suggested Iceberg/S3 tables was something we were keen on for data lineage but some later meeting transcripts/docs suggest we've dropped Iceberg in favour of plain Parquet for pre/post-enriched + ClickHouse for analytics. Is this correct? What was the reasoning behind this?
>
> ClickHouse hosting flavour - not sure if you had any strong opinions on this, but some options are: ClickHouse Cloud, Altinity-on-our-AWS, Self hosted on EC2. My lean was ClickHouse Cloud for PoC/early production with Altinity later to scale (especially given we're deferring VPCs for now).
>
> [...]
>
> Let me know if you have any thoughts on these! Could also put in some time if that's easier

The pattern:

- Doc references collapsed to "early docs / some later docs" — no enumerated ADR numbers.
- Quote removed entirely.
- One question per bullet, not two stacked.
- Hosting options listed plainly; the lean stated without compound justification.
- "not sure if you had any strong opinions" is softer than "Aligned, or strong opinion either way?".
- Closes with an offer to sync, not a question that demands an answer.

The AI draft was roughly **twice as dense** as the rewrite for the same content. Density is the giveaway.

## Positive examples

A technical reply acknowledging a teammate's point:

> Morning Rad! Thanks for sharing your thoughts, to respond:
>
> - Agreed on first point - I think that's cleaner than what I originally suggested
> - Yep aligned on middle 4 points
> - On the final point - yeah good point, I didn't realise it was backwards compatible. Also the batching point is a good one, it's fundamentally different functionality

A quick project nudge:

> Hey - are there any DDT meetings I should be invited to?
>
> I think in the spirit of not having to know context of everything to develop, I'm keen to remain a step removed from the Danone team directly, but if there's any recurring meetings/ceremonies which are focused on tech development then I think I'd benefit from being part of these

A longer technical proposal:

> Hmmm good question - I actually think one thing which might be good to do before we jump into the steps is to build out a skeleton of everything that'll need to be built. The reason I think this would be valuable is we'll have multiple people working on FoDI engineering from next week so having a foundation to build off of and clearly being able to see how things fit in will make it easier for everyone to start engineering on top of that.

Notice: the "Hmmm good question -" opening, the `in my view` / `I think` framing repeated, the `reason I think this would be valuable is` construction (explaining the why explicitly), and the slightly run-on quality.

## Self-check before delivering a draft

Quick pass before showing the user:

**Voice**
- No em-dashes? (Use ` - ` instead)
- No meta-framing labels like "Zooming out:", "Bottom line:", "At a high level:"?
- Opening matches one of the patterns (`Hey [name]!` / `Hey all` / `Morning [name]!`)?
- Opinions framed with "in my view" / "I think" / "to me" rather than stated as objective fact?
- British spellings throughout?
- No formal sign-off (`Cheers`, `Best`, etc.)?
- If responding to multiple points, used "to respond:" or similar as the hinge?
- Corporate-speak excised? (No "leverage", "circle back", "synergy", "utilise the capabilities of")
- Hedging by frame, not by weakening the claim itself?

**Density (the most common failure mode)**
- Could the message be 30%+ shorter without losing the core ask?
- One question per bullet, not two stacked?
- No doc / ADR / ticket reference appearing more than once?
- No direct quotes from source docs?
- No compound parenthetical justifications ("(if X / Y / Z forces it)")?
- Asks are soft ("let me know your thoughts", "any priors?") rather than blunt ("Aligned?")?
- If the thread might branch, is there an "could put in some time if easier" offer?
- Does the message read as something a busy colleague would skim cleanly, or as documentation?

If any of these are off, rewrite before showing. Cutting is usually the answer.

## Code-shaped artefacts — see the vault

Three artefact-specific notes in the vault that override the general
voice when drafting code-adjacent or personal-project content:

- **PR review comments** — `knowledge-vault/voice/code-review.md`
  (relative path from this plugin:
  `../../../knowledge-vault/voice/code-review.md`). Two modes
  (conversational vs structured from the code-review skill), a
  batch-same-comment pattern, the `nit:` convention, and
  release-please-adjacent calls (breaking-change,
  Conventional Commits PR title).
- **Code explainers** — `knowledge-vault/voice/explaining-code.md`
  (`../../../knowledge-vault/voice/explaining-code.md`). PR
  descriptions, Slack "how does this work" replies, Confluence
  "Behaviour" sections. Self-explainer prompts (well-evidenced)
  vs team-facing explainers (less evidenced — note flags what's
  inferred).
- **Personal-project copy** —
  `knowledge-vault/voice/personal-projects.md`
  (`../../../knowledge-vault/voice/personal-projects.md`). READMEs,
  LinkedIn, recruiter conversations, multi-persona evaluation
  prompts. Distinct enough from team-internal comms that the
  default voice rules need this overlay before drafting.

When drafting any of these artefacts, read the vault note before
imitating — the annotated examples carry phrasings the general
voice guidance above doesn't capture.

## Scope

This skill covers short-to-medium async comms — Slack messages, emails, Jira / PR comments, thread replies, team announcements. It does NOT cover long-form content (blog posts, LinkedIn articles, formal internal docs). The voice samples don't calibrate those with confidence. If asked to draft long-form in Issei's voice, flag the limitation and ask for more samples before attempting.
