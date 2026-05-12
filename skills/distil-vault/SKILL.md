---
name: distil-vault
description: Promote raw material (Cowork transcripts, Claude Code session dumps, harvest pipeline outputs, inbox notes, ad-hoc text) into Issei's personal knowledge vault as a properly-structured markdown note, and update neighbouring pages with backlinks and refreshed summaries. Use this skill whenever the user says "distil this", "add this to the vault", "capture this in my knowledge base", "promote this", "turn this into a vault note", "save this to the vault", or shares a transcript / session / chunk of text and asks where it should live. Also fire on "process the inbox" or "promote the harvest outputs". Do NOT use for writes to ephemeral folders (working-docs, inbox itself) — only for promotions into knowledge-vault/.
---

# Distil into the vault

Take raw material and produce a properly-structured markdown note in the
right vault folder, plus updates to 5–15 neighbouring pages. This is the
"compile at write time" step that keeps the vault navigable. Skipping the
neighbour updates is not an option — it's what the skill exists to do.

## Inputs

The user may give you:
- A path to a file (transcript, session JSONL, harvest parquet, inbox file)
- An inline chunk of text
- A reference like "the latest harvest" or "yesterday's Cowork session"
- A vague gesture: "distil what we just talked about"

Resolve to actual content before drafting. If ambiguous, ask one clarifying
question — never guess at the source.

## Process

1. **Read the vault schema.** Open `knowledge-vault/CLAUDE.md` and confirm
   the folder taxonomy, frontmatter schema, and linking conventions.
   Don't rely on memory; the schema is the contract.

2. **Read the source material.** All of it, not a sample. If it's a path,
   Read it. If it's a parquet from `harvest/`, ask Issei to point at the
   relevant row(s) — don't try to parse parquet blindly.

3. **Decide the target folder.** From the taxonomy in
   `knowledge-vault/CLAUDE.md`:
   - `strategy/` — long-running thinking on programmes, adoption, frameworks
   - `patterns/` — reusable technical patterns and designs
   - `playbooks/` — how-I-do-X
   - `decisions/` — ADR-lite, immutable, only for real decisions with
     optionality. Don't promote chat notes into `decisions/` — those go to
     `patterns/` or `projects/`. Decisions are deliberate.
   - `projects/` — stable hubs (CDT, FPL, etc.)
   - `people/` — only with caution; sensitive folder
   - `references/` — external pointers
   - `voice/` — voice samples
   - `team-enablement-notes/` — tooling / meta-Claude
   - `daily/` — never write here directly; harvest pipeline owns it

   If it fits two folders, write two linked notes. If nothing fits, flag
   it — do not invent a new folder.

4. **Search for existing notes this should extend.** Run Glob + Grep
   against `knowledge-vault/` for the topic, key entities, and any acronyms
   in the source. Read the top 3–5 hits. If a close match exists, propose
   updating that note (additively) rather than creating a duplicate.

5. **Draft the note.** Schema per `knowledge-vault/CLAUDE.md`:
   - YAML frontmatter: `title`, `created` (today's date), `tags`, `links`
   - H1 matching `title`
   - 1–2 sentence lede on what this is and why it's here
   - Body in prose where possible. Bullets only when the content is
     genuinely a list. Match Issei's voice — see the `issei-voice` skill
     for patterns; in particular: British English, no em-dashes (use
     ` - `), no corporate-speak, no meta-framing labels like "Zooming
     out:" or "Bottom line:", opinions framed with "in my view" / "I
     think", not stated as objective fact.
   - Strip transcript / session artefacts (timestamps, speaker tags,
     Cowork chrome) unless they materially carry meaning.

6. **Identify 5–15 neighbouring pages to update.** This is the compile
   step. Look for:
   - The hub page for any project the note relates to
     (`projects/<name>.md`) — add a link in the relevant section
   - Adjacent patterns / decisions that the new note references or
     contradicts
   - Any note that the new one should link back to via `links`
     frontmatter — those targets need their own `links` updated too
     (reciprocal backlinks)
   - Hub summaries that are now stale because of the new content — refresh
     a sentence or two, not a rewrite

   If the new note has zero plausible neighbours, that's a signal it
   doesn't belong in the vault. Push back rather than writing an orphan.

7. **Show the draft and the neighbour-update list.** Before any writes:
   - Proposed path of the new note
   - Full draft body
   - List of neighbour files with the specific edit planned for each
     (one-liner per file)

   Wait for confirmation. Issei may push back on folder choice, tone,
   or specific neighbour edits. Don't proceed until he's said go.

8. **Write.** Use the Write tool for the new note. Use Edit for each
   neighbour file. Do them all in one pass — partial compile leaves the
   vault in a worse state than before.

9. **If the source was in `inbox/`, move it.** `inbox/<file>` →
   `inbox/processed/YYYY-MM/<file>`. The audit trail matters; don't
   delete sources.

10. **Report.** One short message: path of the new note, count of
    neighbours updated, anything you punted on or noticed in passing.

## Anti-patterns

- Writing the note without updating neighbours. Defeats the whole point.
- Inventing a new folder because nothing fits. Flag instead.
- Promoting to `decisions/` because the source mentioned a decision.
  Decisions are written deliberately, not extracted from chat.
- Auto-running on the whole `inbox/` without confirming each promotion.
  Distillation is human-in-the-loop; the volume of `inbox/` is small
  enough to walk one by one.
- Direct writes to `daily/`. Owned by the harvest pipeline.
- Faking the source. If you can't read the parquet or the JSONL, say so.
  Never paraphrase from imagined content.
- Glossy summaries that strip the actual signal. The vault is "useful in
  six months", not "looks neat today". Preserve specifics, names,
  numbers, links.

## When to push back

- The source isn't durable signal — it's a project status update, a
  one-off question, a transient frustration. Suggest leaving it in inbox
  or dropping it. The vault is small and hand-curated; junk erodes it.
- The user wants to dump a whole transcript verbatim. Distillation
  means extracting signal, not transcription. Offer to extract or ask
  them to point at the specific bits worth keeping.
- The proposed note would duplicate an existing note. Propose an edit
  to the existing note instead.
