# Reference writers

Eight working senior-technical writers whose moves inform `blog-voice`. Cited so the patterns are inspectable rather than vibes-based. When tweaking a draft, naming a writer ("more Brooker here", "this paragraph wants Julia Evans") is more useful than abstract style notes.

## Dan Luu (`danluu.com`)

Long-form analytical, contrarian, data-heavy. Reads like someone who actually ran the numbers.

- **Conversational openings.** Drops you into a personal observation. "If I ask myself a question like 'I'd like to buy an SD card; who do I trust...'", rather than a thesis.
- **Hedges constantly.** "I don't think it's controversial that...", "seems to be catching on a bit", "it's plausible that...". The hedge sits on the frame, leaving the claim itself flat.
- **Accumulates examples instead of arguing abstractly.** Ladder of scale: private forums, lobste.rs, HN, Reddit, Facebook, YouTube. Each rung extends the argument; no abstract principle dropped on top.
- **Footnotes for tangents.** Numbered, substantive. Keeps main-text momentum while satisfying scholarly impulses.
- **Middle-voice closes.** Refuses to oversell. "A full discussion of what that means is too long to include here, so we'll look at this in more detail another time."
- **Transitional anaphora over connectors.** "And if I compare X to Y... And then if I compare Y to Z..." builds momentum through repetition rather than through "Furthermore".

Use when the post is an argument that accumulates evidence (cost-engineering; vault-without-embeddings if pushed further toward data).

## Marc Brooker (`brooker.co.za`)

AWS Principal voice. Distributed-systems-grade depth in accessible prose.

- **Short opening declarations.** "It's time to be right." "Outcomes continue to matter." Three to five words; thesis stated as fact, then the post earns it.
- **Technical analogies grounded in real systems.** "Feedback loops, just like in electronics and control theory, can have significantly different capabilities from their underlying components."
- **"Real" as anchor word.** "Real customers", "real failures", "real conversation". Signals substance over theory.
- **Honest qualifications.** "Somewhat amusingly", "Solidly in", "I'm conflating two things here". These mark where the simplification is, rather than reading as throat-clearing.
- **Footnote asides for self-aware humour.** Substance in the body, dry observation in the footnote.

Use when the post is a thesis essay with technical depth (LangGraph vs Pydantic AI; SSE-from-Lambda if reframed as a pattern post rather than a war story).

## Julia Evans (`jvns.ca`)

Confessional clarity. Naive questions taken seriously.

- **Conversational framing openers.** "A few years ago I gave a short talk..." / "I've been trying to understand X for a while now."
- **"I think" / "my understanding is" as epistemic markers.** Useful for placing the speaker without weakening the claim. "I don't really know anything about PHP so I don't have much interest in fact checking that PHP statement; I'm happy to leave it as an 'I think' and potentially correct later."
- **Parenthetical self-correction.** "(or maybe I'm misremembering; checked, no, this is right)".
- **Demonstrates rather than explains.** Shows the command, shows the output, says what surprised her.
- **Mixes personal and technical** without flag. Docker and Arabic tokenization sit next to "I love how this works".

Use for the confession shape: "I tried X, then deleted it" / "I didn't understand this for ages" / "here's a thing I learned this week".

## Simon Willison (`simonwillison.net`)

Practical guide voice. Tool-builder operating in public.

- **Numerical specificity.** "68,000 photos", "$1.68 total cost", "18 organizations now have models on the Chatbot Arena Leaderboard." Numbers do the work.
- **Inline links woven into sentences.** "I wrote about this at the time in [The killer app of Gemini Pro 1.5 is video](url)". The link is part of the prose rather than appended.
- **Casual parentheticals showing the seams.** "(this list generated using Django SQL Dashboard with a SQL query written for me by Claude)". Honest about how the post was made.
- **Self-deprecating humour.** "My personal laptop... is the same laptop I've been using." Plain register, no posturing.
- **TOC and section headers for comprehensive pieces.** When the post is meant to be a reference scrolled back to, it has structure; when it's a quick note, it doesn't.

Use for practical guides, year-in-review-style pieces, "things I learned about X" posts that the reader will return to.

## Patrick McKenzie / patio11 (`kalzumeus.com`, `bitsaboutmoney.com`)

Variable sentence length as instrument. Parentheticals everywhere.

- **Aggressive sentence variety.** A short declarative ("All of these assumptions are wrong.") next to a 60-word multiclause parenthetical-stuffed construction. Reads as a person rather than a model.
- **Heavy parentheticals.** "(Most people call me Patrick McKenzie, but I'll acknowledge as correct any of six different 'full' names...)". Context, deflation, asides.
- **Anticipatory humour.** Preempts the reader's objection before they raise it. "That Klingon Empire thing was a joke, right?" lands after a list of names-handling absurdities.
- **Personal anecdote, then general principle.** Establishes credibility through narration; the broader claim follows.
- **Numbered lists building to absurdist conclusions** (the falsehoods-about-names format).

Use when the post benefits from a strong personal voice and the reader needs to be carried through dense domain material (financial systems, name-handling, salary negotiation).

## Will Larson (`lethain.com`)

Staff-engineer essay register. Measured authority grounded in narrative.

- **Personal-narrative openers.** "Silicon Valley's protagonist narrative" / "My father's retirement". Situates the essay in lived experience before generalising.
- **Hedges by experience.** "I've found", "I've gotten quite deliberate about". Opinions emerge from years of work rather than from theory.
- **Names mental models cleanly.** "Pace, People, Prestige, Profit, Learning." Each one a noun the reader can pick up and carry.
- **Brief direct closings.** Pivots from problem to aspiration without summarising. "For now, I'll be over here working on my pace."

Use for management-adjacent or career-adjacent posts. Note: Issei is an IC, so borrow the register rather than the topic.

## Rachel Kroll (`rachelbythebay.com`)

Short ops war story. The whole post is the story.

- **600 to 1,200 words typically.** Length emerges from the material rather than from a structural choice.
- **No H2 headers, or one at most.** Narrative drives.
- **Technical detail emerges through the story.** "We saw the latency spike at 03:12. By 03:14 the on-call was paged. By 03:18 we'd worked out the cache had..."
- **Ends abruptly.** When the point is made, the post stops. No synthesis, no "what this teaches us".
- **Wry, slightly resigned voice.** "Maybe nobody knows how to fix it. But it's worth thinking about."

Use for a specific debugging session, a deploy that went wrong, a production incident. The SSE-from-Lambda post is currently in argument-essay register, but the material wants this register instead. Narrate the evening, land the fix, stop.

## Aphyr / Kyle Kingsbury (`aphyr.com`)

Jepsen-style investigation. Code, output, and analysis in alternating blocks.

- **Claim, then reproducible test, then finding loop.** "We expected X. We ran the test like so [code]. We observed Y."
- **Code and output as evidence**, doing argumentative work rather than illustrating after the fact.
- **Formal frame with literary touches.** "We call this the goddess of distributed systems." Tonally distinctive; doesn't pull punches when finding bugs.
- **Names what was tested and what wasn't.** "We did not test linearizability under network partitions of more than 60 seconds. That work is left for future analysis."

Use for benchmarks, deep-dives into a specific tool's behaviour, "does X actually do Y" posts. A future "pgvector vs sqlite-vss at this scale" post would want this register.

## Choosing between voices

Most posts will end up as a blend of two or three of these. The dominant one should be picked deliberately based on the post's shape (`references/shapes.md`).

Rough mapping from shape to dominant voice:

- War story: Rachel Kroll, with Aphyr for the technical evidence blocks.
- Argument essay: Dan Luu or Marc Brooker.
- Practical guide: Simon Willison.
- Confession: Julia Evans or Patrick McKenzie.
- Investigation: Aphyr, with Brooker for the framing.

If the draft doesn't read like at least one of these, it probably reads like AI.
