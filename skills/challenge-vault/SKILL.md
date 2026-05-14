---
name: challenge-vault
description: Argue against a position or proposal using evidence drawn from Issei's personal knowledge vault. Read-only devil's advocate — surfaces prior decisions, patterns, and recorded thinking that contradict, complicate, or counter the position. Use this skill when the user says "challenge this", "argue against this", "play devil's advocate", "what would I have said against this", "stress-test this proposal", "what am I missing", "poke holes in this", or before signing off on a Confluence doc / ADR / tech decision. Output is a structured set of counter-arguments grounded in specific vault notes. Never writes to the vault.
---

# Argue against the position using the vault as evidence

The pattern from the obsidian-second-brain crowd: use the accumulated
record of your own prior thinking to argue against a current position.
Particularly valuable before:

- Signing off on an ADR or Confluence doc
- Making a tech-stack call
- Proposing a new pattern or process
- Agreeing to a scope expansion
- Adopting an external framework or library

The skill is read-only by design. It surfaces evidence; the user
decides what to do with it.

## What "challenge" means here

Not contradiction for its own sake. Not pretending to disagree. The
skill looks for *real* tensions between the stated position and the
recorded vault — places where Issei's prior decisions, patterns, or
stance suggest the position has a cost, a counter-example, or an
unstated assumption that would have been flagged.

Three failure modes the skill avoids:

- **Strawman challenges.** Inventing weak counter-arguments not
  grounded in the vault. If nothing in the vault counters the
  position, say so — that's a valid finding.
- **Devil's-advocate theatre.** Manufacturing tension where none
  exists. If the vault genuinely agrees with the position,
  acknowledge it and stop.
- **Restating the position with caveats.** "Yes but be careful" isn't
  a challenge. The skill should find substantive disagreement or
  step aside.

## Process

1. **Read the schema if you haven't this session.** Open
   `knowledge-vault/CLAUDE.md` for folder taxonomy.

2. **Get the position precisely.** The user states a position,
   proposal, or claim. Restate it back in one sentence so it's
   unambiguous what's being challenged. If the position has multiple
   sub-claims, name them — each may need separate vault evidence.

3. **Scan the vault for relevant prior thinking.**
   - Glob `knowledge-vault/**/*.md` excluding `reference/`.
   - Grep for the topic, the entities involved, adjacent concepts.
   - Read every `decisions/` note that touches the topic — those are
     the strongest evidence base.
   - Read patterns and playbooks that constrain the space.
   - Read project hubs (`projects/<x>.md`) for the recorded stance.

   Be generous; the vault is small enough that broad scanning is
   cheap.

4. **Find the genuine tensions.** For each piece of vault evidence,
   ask: does this counter the position, complicate it, or expose an
   unstated assumption? Three categories worth distinguishing:

   - **Direct contradiction.** A prior decision says the opposite.
     Highest-confidence challenge — the user has already considered
     this and decided the other way.
   - **Cost or trade-off the position ignores.** The vault records
     a constraint or principle the position would violate. Often the
     interesting class — the position isn't wrong, but it has costs
     the proposer hasn't named.
   - **Unstated assumption.** The position rests on something the
     vault has previously called into question. Surface the
     assumption and the prior doubt; let the user decide if the
     assumption is now safe.

5. **Discard weak findings.** A note tangentially related to the
   topic isn't a challenge. Be ruthless about pruning — better to
   surface three solid challenges than ten weak ones. Quality over
   coverage.

6. **Structure the response.** Each challenge gets:
   - One-line statement of the tension
   - The vault evidence: `path/to/note.md` with a brief quote or
     summary of what that note says
   - One sentence on why this counters / complicates / exposes the
     position

   Group by category (direct contradiction first, then trade-off,
   then unstated assumption). Within each group, strongest evidence
   first.

   ```
   ## Direct contradictions

   1. **The position assumes X, but you decided against X in April.**
      `decisions/2026-04-XX-foo.md`: "<quote or summary>". The
      reasoning was <Y>; that reasoning is still in force unless
      something changed.

   ## Costs the position ignores

   2. **<one-line statement>.** `patterns/bar.md`: "<quote>". This
      pattern says <Z>, which the position would violate.

   ## Unstated assumptions

   3. **<one-line statement>.** `projects/baz.md` flagged <W> as an
      open question; the position assumes it's resolved.
   ```

7. **State the residual.** After all challenges, say plainly:
   - If the vault counters the position significantly: "These are
     the strongest challenges. The position may still be right, but
     it needs to address [N] of them explicitly."
   - If the vault mildly complicates it: "Some friction worth
     naming, but no fundamental contradiction in the vault."
   - If the vault agrees: "I couldn't find substantive
     counter-evidence in the vault. The position aligns with your
     recorded thinking. (That doesn't mean it's right — external
     counter-arguments may exist — but the vault isn't where they'd
     come from.)"

   Honesty here is more valuable than the theatre of pushback.

8. **Don't propose what to do.** The skill surfaces evidence. The
   user decides whether the challenges land, what to address, what
   to ignore. Don't editorialise "you should reconsider" — let the
   evidence speak.

## Anti-patterns

- **Fabricating tensions.** If the vault doesn't counter the
  position, say so. Made-up devil's-advocacy is worse than none.
- **Quoting notes out of context.** If a decision was superseded,
  the superseding note is what counts. Check `Status:` lines.
- **Editorialising.** "I think you're wrong because..." isn't this
  skill's job. Surface evidence; let it speak.
- **Restating the position as the challenge.** "You said X — but
  what if X?" is not a challenge.
- **Writing to the vault.** Read-only, always. If the challenge
  surfaces something worth recording, that's a separate
  `distil-vault` call the user initiates.
- **Over-reaching to find counter-arguments.** Three solid ones
  beat ten weak ones every time.

## When to use vs other skills

- Use `challenge-vault` when the user has a position and wants
  pushback.
- Use `search-vault` when the user just wants to know what the vault
  says (no position, just retrieval).
- Use `research-vault` when the user wants a balanced
  internal+external view, not specifically pushback.

## Tactics for harder positions

- **Position is well-specified.** Best case — scan for direct
  contradictions in decisions, then trade-offs in patterns.
- **Position is vague.** Ask the user to sharpen it before
  challenging. A vague position invites strawman challenges.
- **Position is meta (e.g. "we should be more X").** Look for prior
  stance on X in strategy/ and playbooks/. Often the meta-position
  has costs that are recorded as principles in those folders.
- **Position is brand-new to the vault.** If nothing relevant
  exists, say so. The vault can't challenge what it doesn't have
  context on; recommend external research via `research-vault`.
- **Position the user has clearly already committed to.** Still
  worth running — surfaces what they'd need to address publicly to
  defend the call.
