---
name: research-vault
description: Answer research-shaped questions by scanning Issei's personal knowledge vault first, identifying what's already known and what's genuinely missing, then filling only the gaps with external sources where needed. Use this skill when the user asks "research X for me", "what's the latest on Y", "look into Z", "I need to know about W", "compare X and Y", or when a question needs both prior thinking AND fresh external context. Distinguishes internal-vs-external provenance explicitly in the answer. Differs from search-vault — search-vault is pure retrieval against the vault; research-vault is retrieval plus gap-filling external lookup with clear attribution.
---

# Research the vault first, then fill gaps externally

The pattern Karpathy and the wider LLM-wiki community converged on:
when a research-shaped question comes in, the vault is the *first* place
to look, not an afterthought. The failure mode this skill prevents is
me running external searches for things Issei already wrote about — and
then producing answers that ignore his prior thinking.

The shape: vault scan → gap analysis → external lookup *only on the
gaps* → synthesis with internal-vs-external provenance clearly marked.

## When to use this vs search-vault

`search-vault` answers "what do I have on X" — pure retrieval. It
returns notes and stops.

`research-vault` answers "tell me about X" or "research X for me" — it
returns a synthesis that combines vault content with external context
where the vault genuinely doesn't have the answer.

If the user's question is plainly about their own prior thinking, use
`search-vault`. If the question is exploratory or needs fresh external
context, use `research-vault`. When in doubt, default to
`research-vault` — the vault-first scan is cheap and the answer is
better.

## Process

1. **Read the schema if you haven't this session.** Open
   `knowledge-vault/CLAUDE.md` once to know the folder taxonomy. Don't
   re-read it every call.

2. **Frame the question precisely.** Restate to yourself (not to the
   user) what's actually being asked. Three components:
   - **What does Issei probably already know?** — the vault is likely
     to have prior context on the topic, his stance on it, related
     decisions.
   - **What's the genuinely new thing?** — what wouldn't be in the
     vault yet (recent news, fresh library versions, a topic he
     hasn't touched, a specific external fact).
   - **What's the form of answer he wants?** — a comparison, a
     status update, a decision input, a synthesis.

   Don't surface this framing to the user; it's your own
   prep.

3. **Scan the vault.** Same approach as `search-vault`:
   - Glob `knowledge-vault/**/*.md` excluding `knowledge-vault/reference/**`.
   - Grep for the topic keywords, key entities, synonyms.
   - Read 3–5 top hits in full.
   - Follow links from the hub pages where the topic plausibly lives.
   - Pull related decisions, patterns, projects that touch the
     question even tangentially.

   Be generous in this step. Reading more vault is cheap; missing
   relevant prior thinking is expensive.

4. **Map vault coverage to question components.** For each component
   of the question, decide:
   - **Fully covered** — the vault has the answer, no external lookup
     needed.
   - **Partially covered** — the vault has context but not the
     specific fact / recent development / external comparison.
   - **Not covered** — purely external; vault has nothing relevant.

   Be honest about this. If the vault covers it, don't pretend you
   need external sources to be thorough. If the vault doesn't cover
   it, don't paraphrase a thin gesture as if it did.

5. **Fill gaps externally — only the gaps.** For each "partially" or
   "not covered" component:
   - Use `WebSearch` for current developments, versions, recent news.
   - Use `WebFetch` when there's a specific URL to read.
   - Use the Atlassian MCP for live Confluence / Jira content.
   - Use `gh` via Bash for live GitHub state.
   - Use the Context7 MCP for library docs (already wired by the team
     plugin).

   Don't search externally for things the vault already covers — that
   wastes context and produces blended-source noise.

6. **Synthesise with provenance.** The answer has two clearly marked
   sections:

   ```
   ## From the vault

   - `<path>` — <one sentence on what it contributed>
   - `<path>` — <one sentence>

   <synthesis of what the vault says>

   ## From external sources

   - <Source name with link> — <one sentence>
   - <Source name with link> — <one sentence>

   <synthesis of the external context>

   ## Together

   <integrated answer — explicitly noting where vault and external
   align, where they disagree, where one fills the other's gap>
   ```

   The provenance split is load-bearing. The user needs to know which
   parts of the answer came from his own prior thinking and which came
   from outside, so he can trust them differently.

7. **Flag distil candidates.** If the external research turned up
   something that's genuinely worth keeping — a new pattern, a
   resolved open question, a comparison that informs a decision —
   flag it at the end:

   `Worth distilling: <one-line description>. Suggested path:
   <folder>/<slug>.md.`

   Do not auto-write. Distillation is a deliberate
   `distil-vault` call. This skill stops at "research delivered" plus
   "here's what's worth promoting".

## Anti-patterns

- **Skipping the vault scan because the question "feels external".**
  Almost every research question Issei asks intersects with prior
  thinking. Scan first, always.
- **Blending vault and external sources without marking provenance.**
  Defeats the whole point. He needs to see which is which.
- **Doing exhaustive external research when the vault already
  answered.** If the vault has it, stop. Don't pad with external
  sources to look thorough.
- **Auto-writing the synthesis back to the vault.** That's
  `distil-vault`'s job, with human-in-the-loop. This skill only
  *flags* candidates.
- **Citing vault notes that don't exist or weren't actually read.**
  Quote real paths, real content. Same rule as `search-vault`.
- **Using web search for things the Atlassian MCP, Context7, or gh
  CLI would answer better.** Match the source to the question.

## Tactics for harder queries

- **"Compare X and Y" questions.** Vault scan for both X and Y
  independently; the comparison usually lives across multiple notes.
  External fills in current-state details (latest version, recent
  benchmark) the vault won't have.
- **"Should I X" questions.** Vault scan for prior decisions on
  adjacent topics; external for the technical specifics. The vault
  carries the stance; external carries the facts.
- **"What's the latest on X" questions.** Vault for "what's Issei's
  recent context on this"; external for actual latest. Don't skip
  the vault even though "latest" sounds external — his prior
  context shapes how you read the latest.
- **"Help me think about X" questions.** Vault-heavy. External is
  mostly there to challenge or extend, not to inform from scratch.

## When NOT to use

- When the question is plainly retrieval-only ("what do I have on
  X"). Use `search-vault` instead.
- When the question is about live external state with no plausible
  vault context (server status, market price, current time). Use the
  external tool directly without the vault scan overhead.
- When the question is task-execution ("write a Confluence page",
  "draft a Slack message"). Different skills.
- When the user explicitly says "don't check the vault" or "fresh
  perspective". Respect that; skip the scan and use external only.
