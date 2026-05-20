# Structural shapes

The biggest tell across Issei's existing drafts is structural uniformity: every post is hook, then three-or-five H2 sections, then synthesis paragraph. That symmetry is what makes them read as batch-generated, even where the content is original.

The fix is to pick a shape per post and commit to it. The five shapes below aren't exhaustive; they're the ones working senior-technical writers most often reach for. Some posts blend two (a war story with a short investigation block inside it, or an argument essay that opens as a confession). That's a deliberate choice and fine. What this skill exists to break is the default-symmetric shape.

## War story: narrative drives

Rachel Kroll, sometimes Aphyr. Length: typically 600 to 1,200 words.

No H2 headers, or maybe one. The post is a story. Technical detail emerges as the narrative reaches it; voice is wry, slightly resigned; the post ends when the point is made, with no synthesis.

When to use: a specific debugging session, a production incident, an evening lost to a single bug, "I tried X and it didn't work and here's what I did instead". This is what the **SSE-streaming-from-Lambda** draft wants to be. The current argument-essay structure with H2s for "What SigV4 needs", "What works instead", "The CloudFront cache behaviour, briefly" is fighting the material. The story is "I spent an evening on this and an ADR came out the other end". Narrate the evening, land the fix, stop.

Smell test: if you find yourself adding a "Generalising" section at the end (and the current draft has one), you're in argument-essay mode. War stories don't generalise; they end.

## Argument essay: one extended position

Dan Luu, Marc Brooker. Length: 1,500 to 4,000 words.

Light H2s for breathing room, used for pacing rather than as structural enforcement. One thesis, accumulating evidence, evidence does the work. Footnotes for tangents. Closes by refusing to oversell.

When to use: a contrarian claim, a "here's how I think about X" piece, a position the reader is meant to disagree with on the first paragraph and agree with by the last. The **LangGraph-vs-Pydantic-AI** draft is already this shape and works. The framing essay format suits the material. The **cost-engineering** draft also wants this shape, but is currently weighed down by the numbered "First lesson", "Second lesson", "Third lesson" framing, which is the symmetry this skill is trying to break. De-number the headers; let the dominating-cell argument be the spine; let the SSM and DynamoDB observations follow naturally as the spine reaches them.

The argument essay is the AI default. Ration it to roughly one post per quarter.

## Practical guide: comprehensive reference

Simon Willison, Eugene Yan, Lilian Weng. Length: 2,000 to 6,000 words.

TOC at the top, numbered or labelled sections, lots of inline links and code. The reader will scroll back to this. Voice is precise and a little dry; the post is closer to a reference document than to an essay.

When to use: "here's how I built X", "things I learned about Y in 2026", a write-up meant to save the next person the time you spent. This shape isn't currently in Issei's draft set, but a "what I'd tell someone setting up the AWS free tier for an LLM workload" post would want it. Some of the content currently scattered across `cost-engineering` and `fpl-pulse` would fit here cleanly.

## Confession: personal narrative becomes general principle

Julia Evans, Patrick McKenzie. Length: 800 to 1,800 words.

First-person throughout. The personal narrative is the spine; the general principle comes out at the end and only if it's load-bearing, often left implicit for the reader to draw. Voice is honest about uncertainty; the post can change direction halfway through if the writer changed their mind.

When to use: "I tried X, then deleted it" posts, mistakes-and-what-I-learned, role-shift reflections, "I used to think Y, now I think Z". The **vault-without-embeddings** draft is closest to this shape but currently leans too argument-essay. The "Three things happened in the same week" opener and the "What I'd tell someone considering RAG over a personal vault" closer with its three-questions framework both push it back toward symmetric essay. Lean further into the confession register. The first-person narrative is doing most of the work; let it.

## Investigation: claim, test, output, analysis

Aphyr's Jepsen reports, occasionally Brendan Gregg's perf write-ups. Length: 1,500 to 3,000 words, heavy on code blocks.

Tight loops: claim, then reproducible test, then output, then analysis, then the next claim. Code and output do argumentative work, not just illustration. Voice is formal; sometimes formal-with-literary-touches (the Jepsen "goddess of distributed systems" register).

When to use: benchmarks, "does X actually do Y" posts, anything where the evidence is reproducible and the post's job is to demonstrate. Not currently in Issei's draft set; would suit a future post comparing embedding stores, retry strategies, or model-cost behaviour under varying load.

## Picking the shape

For each draft, ask:

1. **What is the dominant thing this post is doing?** Telling a story (war story), arguing a position (essay), explaining how to do something (guide), reflecting on a personal experience (confession), measuring something (investigation).
2. **What's the natural length?** If the answer is "600 words", it's a war story or a short confession. If "5,000 words", it's an essay or a guide.
3. **What does the reader come away with?** A vivid scene (war story). A new mental model (essay). A working setup (guide). A sense of how the writer thinks (confession). A reproducible result (investigation).

If two shapes feel right, the post is probably trying to do two things and should be split. If no shape feels right, the post hasn't decided what it is yet.

## Apply to current drafts

Per-draft note for the existing portfolio drafts, so the rewrite has a clear target:

- **`langgraph-vs-pydantic-ai.md`** is an argument essay. Keep the current shape. Already the strongest draft.
- **`vault-without-embeddings.md`** is a confession. Lean further into first-person narrative; cut the three-questions framework closer.
- **`sse-streaming-from-lambda.md`** is a war story. Strip the H2 structure, narrate the evening end-to-end, cut the "Generalising" section.
- **`cost-engineering-llm-pipeline.md`** is an argument essay. De-number the "First / Second / Third / Fourth / Fifth lesson" headers; restructure around the dominating-cell argument as the spine.
- **`cursor-to-claude-code-migration.md`** is a confession with a thesis. Currently mid-symmetric-essay; would land better as "here's how my view of AI coding tools changed over a year". Verify the team-size claim before publishing either way.
