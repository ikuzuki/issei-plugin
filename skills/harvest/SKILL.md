---
name: harvest
description: Run the weekly knowledge-base harvest pipeline. Extracts last week's Claude Code chat sessions, Confluence pages, and GitHub PRs/reviews into harvest/sources.parquet; writes the weekly rollup to knowledge-vault/daily/YYYY-Www-activity.md; commits the vault. Use when the user says "run harvest", "run the weekly harvest", "harvest now", or when the weekly-knowledge-harvest scheduled task fires this skill.
---

# Run the weekly knowledge-base harvest

You are the harvest agent. Run the Python harvest pipeline (co-located in `${CLAUDE_PLUGIN_ROOT}/skills/harvest/scripts/`) and commit the new weekly rollup to the vault.

## Context

This skill automates the "now" cadence of Issei's personal knowledge base. The vault lives at `~/Knowledge Base/knowledge-vault/`; harvest output lands at `~/Knowledge Base/harvest/` (parquet files, gitignored). The skill is fired by the `weekly-knowledge-harvest` scheduled task every Monday at 08:06 AM, or manually on demand.

Scripts resolve their Knowledge Base paths via env vars (`KNOWLEDGE_VAULT_PATH`, `HARVEST_OUTPUT_PATH`) - set these before running. The shared `kb_paths.py` helper handles resolution.

Decision rationale: `knowledge-vault/decisions/2026-05-12-vault-is-markdown-no-index.md` (vault is markdown only; harvest scripts remain mechanical).

## Process

1. **Set environment variables.**
   ```bash
   export KNOWLEDGE_VAULT_PATH="$HOME/Knowledge Base/knowledge-vault"
   export HARVEST_OUTPUT_PATH="$HOME/Knowledge Base/harvest"
   ```

2. **Run the harvest script.**
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/harvest/scripts/harvest.py"
   ```
   The script walks new Claude Code sessions, authored Confluence pages, and authored GitHub PRs/reviews since last run. Uses upsert-by-id so long-running sessions get refreshed `ended_at` and content. Writes parquet to `$HARVEST_OUTPUT_PATH/`, produces `daily/2026-Www-activity.md`, and writes per-thread reference content to `reference/sessions/2026-Www/` bucketed by `ended_at` (sessions that span week boundaries land in the week of last activity; old-location copies get cleaned up).

3. **Run the activity rollup script.**
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/harvest/scripts/activity_rollup.py" --week 2026-Www
   ```
   Pass last week's label (e.g. `--week 2026-W20` on the Monday of W21). Appends `## Jira tickets touched` and `## Confluence pages edited` to the daily rollup using `ATLASSIAN_*` env vars. Section upsert is idempotent. If either Atlassian endpoint fails, log and continue — don't block the run.

4. **Verify the new rollup landed.** Check `$KNOWLEDGE_VAULT_PATH/daily/` for a new file matching the prior week. The file should have four sections: Chat threads, PRs & reviews, Jira tickets touched, Confluence pages edited. If no new file appeared, investigate — do not commit a vault with no new content.

5. **Commit to the vault.**
   ```bash
   git -C "$KNOWLEDGE_VAULT_PATH" add daily/ && \
   git -C "$KNOWLEDGE_VAULT_PATH" commit -m "chore: weekly harvest rollup 2026-Www"
   ```
   Stage only the new daily file plus any modifications to existing daily files. If the diff looks reasonable, commit. Replace `Www` with the actual week.

6. **Report.** One line:
   ```
   harvest 2026-Www: <N> chat threads, <N> confluence pages, <N> PRs/reviews, <N> jira tickets, <N> confluence pages edited. committed <sha>.
   ```
   If anything failed (script error, no new content, commit conflict), report the failure plainly with the error. Do not silently move on.

## Constraints

- Do NOT run distillation. Promoting harvest material into curated vault folders (`patterns/`, `decisions/`, `projects/`, `voice/`, etc.) is deliberately manual — Issei runs the `distil-vault` skill himself.
- Do NOT run `sync_reference.py` as part of this skill. The reference corpus mirror is a separate concern, not part of the weekly cadence.
- Do NOT touch `BACKLOG.md`, `README.md`, or other top-level Knowledge Base files.
- Do NOT push. Commits accumulate locally between runs; Issei pushes when state should leave the machine.
- If the harvest script reports an Ollama or Confluence auth failure, log it but don't block the run — the chat-only path produces useful rollups even if other sources fail.

## Other scripts in the pipeline

Co-located in `${CLAUDE_PLUGIN_ROOT}/skills/harvest/scripts/`. Available for manual / on-demand use, not called by the weekly cadence:

- `stage_b.py` — adds `summary_oneline` column to `sources.parquet` via local Ollama (`llama3.2:3b`).
- `stage_b_inline.py` — Claude-in-session variant of Stage B (no Ollama required).
- `distil_pack.py` — produces text packs from harvested content (input to `distil-vault`).
- `sync_reference.py` — mirrors Confluence + GitHub into `knowledge-vault/reference/` (gitignored auto-mirror).

All use the shared `kb_paths.py` helper for path resolution. Set the same `KNOWLEDGE_VAULT_PATH` and `HARVEST_OUTPUT_PATH` env vars before running.

## Style

Inherit Issei's global preferences from `~/.claude/CLAUDE.md` — terse, prose over lists in narrative, British English, no preamble. Final report is one line plus optional error detail.
