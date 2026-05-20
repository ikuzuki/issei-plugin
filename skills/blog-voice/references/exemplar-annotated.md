# Annotated exemplar: before and after

A before-and-after lifted from Issei's existing drafts, annotated so the patterns are visible in his own material rather than as abstract rules. Read this before drafting or editing.

The "before" is the current state of `cost-engineering-llm-pipeline.md`, lines 9 to 17 (the opening). The "after" is a rewrite applying the patterns from `SKILL.md`. Both are roughly the same length; the lift is in voice and structure rather than in cutting.

---

## Before: the existing opening

> The cost of running my FPL enrichment pipeline is single-digit pounds a month, and most of that is the Claude API. The AWS side — Lambda, Step Functions, S3, CloudFront, DynamoDB, SSM — combined is rounding error. I deliberately engineered for that, and I want to write down what the cost shape actually looks like, because most "serverless cost" advice online is calibrated for the wrong workload.
>
> Three things upfront.
>
> First, "free tier" is doing a lot of work in this post. AWS free tier covers far more than people assume — 1M Lambda requests/month, 400K GB-seconds of Lambda compute, 5GB of S3 standard storage, 1TB of CloudFront egress, the first 4,000 Step Function transitions/month, 25GB-months of DynamoDB on-demand. For a personal-scale LLM workload running weekly, this is a generous envelope.
>
> Second, this isn't a general "save money on AWS" post. It's specifically about workloads where LLM API calls dominate spend by orders of magnitude. The advice is different from a high-throughput data pipeline.
>
> Third, the goal of cost engineering at this scale isn't to spend zero. It's to keep cost predictable and proportional to value, so you can make changes without flinching. That's a different objective from minimisation.

### What's wrong with it

- **"Three things upfront."** Textbook AI scaffolding. Numbered framing before the points have happened. (`SKILL.md` anti-pattern: numbered framing devices.)
- **"First, ... Second, ... Third, ..."** as parallel paragraph openers. AI symmetry. (`SKILL.md` anti-pattern: "rule of three everywhere".)
- **Three em-dashes in the opening 80 words alone.** (`SKILL.md` anti-pattern: em-dashes; zero allowed.)
- **"This isn't a general 'save money on AWS' post. It's specifically about workloads where LLM API calls dominate spend."** Classic dramatic two-sentence pivot. (`SKILL.md` anti-pattern: "X isn't Y. It's Z." dramatic pivot.)
- **"The goal of cost engineering at this scale isn't to spend zero. It's to keep cost predictable..."** Second instance of the same negation-pivot move. (`SKILL.md` anti-pattern.)
- **Paragraphs are all roughly the same length** (3 to 5 sentences). No rhythmic variety. (`SKILL.md` anti-pattern: equal paragraph lengths.)
- **No specific number for "single-digit pounds"** when one is available (£1.50 to £3.00).
- **Implicit thesis arrives in the third sentence of paragraph one**, then is restated in different words across the three numbered paragraphs. The argument is muddled across the framing.

The passage passes a line-by-line read. It fails the structural read. The AI cadence sits between the sentences, in the symmetry and the rhythm, rather than in any individual bad sentence.

---

## After: rewrite applying the patterns

> Running my FPL enrichment pipeline costs roughly £1.50 to £3.00 a week. Nearly all of that is the Claude API. The AWS side (Lambda, Step Functions, S3, CloudFront, DynamoDB, SSM) combines into a few pennies, and most months it's literally zero.
>
> I engineered for that deliberately. It's worth writing down what the cost shape actually looks like, because most "serverless cost" advice online is calibrated for workloads where the compute dominates. On an LLM-heavy pipeline the compute doesn't dominate, so almost nothing about the standard advice applies.
>
> A note on the free tier before going further. AWS's is unusually generous if you read it carefully: 1M Lambda invocations and 400K GB-seconds of compute per month, 5GB of S3, 1TB of CloudFront egress, 4,000 Step Function transitions, 25GB-months of DynamoDB on-demand. For a personal-scale weekly pipeline, that's a wide envelope. Most "I built this on AWS for $0" posts aren't lying; they're operating inside it.
>
> The goal is to keep the cost predictable and proportional to the value, so I can make changes without flinching. Minimisation is a different target, and the difference matters once you start tuning.

### What changed and why

**Opening line replaced the abstract with the specific.** "Running my FPL enrichment pipeline costs roughly £1.50 to £3.00 a week" replaces "single-digit pounds a month". Specific number, specific cadence ("a week" rather than "a month"), specific named project. (`SKILL.md` pattern: specific numbers over generic adjectives.)

**"Three things upfront" deleted entirely.** The three points still get made; they just aren't announced. (`SKILL.md` anti-pattern: numbered framing devices.)

**Em-dashes deleted entirely.** The original had three in the opening 80 words. The rewrite has zero. The AWS service list now sits inside real parentheses; the parenthetical asides become independent clauses or commas. (`SKILL.md` anti-pattern: em-dashes.)

**The two "X isn't Y. It's Z." pivots removed.** "This isn't a general 'save money on AWS' post. It's specifically about..." becomes "most 'serverless cost' advice online is calibrated for workloads where the compute dominates" (flat statement of what most advice does, audience-hedged). "The goal of cost engineering at this scale isn't to spend zero. It's to keep cost predictable..." becomes "The goal is to keep the cost predictable... Minimisation is a different target" (flat statement of the goal, separate clause acknowledging the alternative). (`SKILL.md` anti-pattern: "X isn't Y. It's Z." dramatic pivot.)

**The three points are now of different lengths.** First (1 short paragraph). Second (1 medium paragraph). Third (1 short paragraph). The middle one expands; the bookends don't. (`SKILL.md` pattern: vary sentence length deliberately; anti-pattern: equal paragraph lengths.)

**Sentence variety inside paragraphs.** Paragraph 2 contains a 17-word sentence, a 28-word one, and an 8-word one ("Almost nothing about the standard advice applies."). The short one lands because the others are longer. (`SKILL.md` pattern: vary sentence length deliberately.)

**Conversational openers replaced "First / Second / Third".** "A note on the free tier before going further" is in the register of someone talking. "First, second, third" is in the register of a slide deck. (`SKILL.md` pattern: open conversationally.)

**Hedging via frame rather than weakening.** "Most 'serverless cost' advice online is calibrated for workloads where the compute dominates" is flat. The hedge sits on the audience ("most") rather than on the claim. (`SKILL.md` pattern: hedge by framing.)

**One small show-of-seams.** "Most 'I built this on AWS for $0' posts aren't lying; they're operating inside it." Quiet credit to the people doing the same thing, with acknowledgment that the writer isn't the first. (`SKILL.md` pattern: show the seams.)

---

## How to use this

1. When editing an existing draft, do a structural read first. Look at paragraph lengths, opener cadence, em-dash count, framing labels, and the dramatic-pivot count. Most of the AI-cadence problem lives at the structural level rather than in any individual sentence.
2. Rewrite the opening first. If the opening still smells of AI, the rest will fight you.
3. Read paragraphs aloud. The rhythm-check is the single most reliable test.
4. After rewriting, run the self-check in `SKILL.md`.

The before is a working draft; the after applies the patterns. Neither is perfect. The point is the *delta*: same content, same length, different cadence and structural rhythm, zero em-dashes, zero dramatic pivots, zero numbered framing. That's what every Issei blog post should look like, on every read.
