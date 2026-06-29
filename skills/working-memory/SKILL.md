---
name: working-memory
description: Recall or save Issei's per-task working state — the short-horizon Tier-2 memory between Claude Code sessions, keyed by repo+branch. Use when Issei says "carry on the X work", "resume CDT-393", "where was I on the data plane", "what am I in the middle of", "pull up my state on Y", "save my state", or "enrich my state on Z". Distinct from the durable vault (search-vault): this is in-flight task context, not durable knowledge. The automatic SessionStart hook already injects the CURRENT branch's state; this skill is for recalling ANOTHER task by name/topic, listing what's in flight, or producing the richer enriched narrative.
---

# Working memory

Per-task notes live under
`C:\Users\IsseiKuzuki\Claude\project-autopilot\working-state\<repo>__<branch>.md`,
written deterministically by the SessionEnd hook (no model) from each session's
recent prompts, files touched, tool mix, and last TODO list. The SessionStart hook
auto-injects the current repo+branch note. This skill is the on-demand path.

The orchestration scripts live in the `project-autopilot` repo (stable path, since
the SessionStart/SessionEnd hooks reference them directly); this skill calls them.

## What to do

Run from `C:\Users\IsseiKuzuki\Claude\project-autopilot\scripts\`:

- "what am I in the middle of" / "what's in flight" → `python recall.py list`
- "carry on the X work" / "resume CDT-393" / "where was I on Y" →
  `python recall.py show <query>` (fuzzy-matches repo / branch / topic; prints the
  best note and offers other matches). Continue from what it surfaces; don't
  re-derive context already in the note.
- "enrich my state on Z" / when a note reads thin →
  `python enrich.py <query>` (adds a Where-this-is / Next / Blockers / Dead-ends
  narrative via the local `claude` CLI, i.e. Issei's subscription, on a cheap
  model). On-demand only, never in the hook.
- "save my state now" (before the SessionEnd hook fires) →
  `python handoff.py --transcript <this session's .jsonl>`, or just let the hook
  fire at close.

## Boundaries

Read/seed only; never edits work repos. Short-horizon — when something becomes a
reusable pattern, promote it to the durable vault via `distil-vault` rather than
letting working-state accrete durable knowledge. Only work sessions get a note
(harvest's personal/work privacy filter); personal repos and agent worktrees are
skipped.
