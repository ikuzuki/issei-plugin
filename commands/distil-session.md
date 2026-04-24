---
description: Distil a Cowork transcript or conversation into a vault-ready markdown note.
---

Take the input (a transcript, conversation dump, or session id/path the user names) and produce a single markdown note suitable for the personal knowledge vault.

Process:

1. Read the source. If it's a path, read it. If it's inline, use the text directly.
2. Decide which vault subfolder it belongs in:
   - `strategy/` — long-running thinking on programmes, adoption, frameworks
   - `patterns/` — reusable technical patterns and designs
   - `references/` — external pointers (people, docs, links)
   - `team-enablement-notes/` — tooling and meta-Claude threads
   - `daily/` — brief log entries
   Pick one; if genuinely ambiguous, ask.
3. Search the existing vault first with `mcp__knowledge__search` (hybrid, limit 5) to check for an existing note this should extend rather than duplicate. If a close match exists, propose updating it instead of creating a new one.
4. Draft the note:
   - Title as H1 — concrete noun phrase, not a sentence
   - Short lede (1-2 sentences) on what this is and why it's here
   - Body in prose where possible, bullets only when the content genuinely is a list
   - British spellings, no em-dashes, no corporate-speak, no meta-framing labels
   - Strip Cowork/transcript artefacts (timestamps, speaker tags) unless they matter
5. Show the draft. Confirm path before writing.
6. On confirmation, create via `mcp__knowledge__create_document` (or update via `mcp__knowledge__update_document`).

Input: $ARGUMENTS
