# harvest scripts

Raw-source extractors that produce intermediate parquet in `../` (the
parent `harvest/` directory). Rescued from `knowledge-mcp/scripts/`
when that repo was deleted on 2026-05-12 (see
`../../knowledge-vault/decisions/2026-05-12-vault-is-markdown-no-index.md`).

## Scripts

- `harvest.py` — walks `~/.claude/projects/**/*.jsonl`, Confluence
  pages, GitHub PRs/reviews. Produces `sources.parquet` and weekly
  rollup material for `daily/`.
- `stage_b.py` — summarises extracted sources via local LLM (Ollama).
  Produces `work_threads.parquet`.
- `stage_b_inline.py` — variant of `stage_b.py` for inline summarisation
  during harvest.
- `distil_pack.py` — bundles related sources into a single pack ready
  for the `distil-vault` skill to chew on.
- `sync_reference.py` — weekly sync of non-authored Confluence / GitHub
  content into the `reference/` mirror (gitignored). See
  `sync_reference.env.example` for required env vars.

## Stale-import audit — done 2026-05-12

`sync_reference.py` previously imported `from knowledge_mcp.config
import load_settings`. Replaced with an inline `_resolve_vault_path()`
that reads `KNOWLEDGE_VAULT_PATH` (or legacy `KNOWLEDGE_MCP_VAULT_PATH`)
env vars and falls back to `../../knowledge-vault` relative to the
script. Fails loud if the path doesn't exist.

`harvest.py`, `stage_b.py`, `stage_b_inline.py`, `distil_pack.py` —
audited, no `knowledge_mcp` / `lancedb` / `watchdog` imports. Only
stdlib + pyarrow.

## Things deliberately not rescued

- `themes.py` — HDBSCAN clustering on Ollama embeddings. Superseded by
  the LLM-driven `distil-vault` skill.
- `reindex.py` and `gc.py` — operated on the deleted FTS / LanceDB
  index. No vault index any more.

## Running

The scripts originally ran inside the `knowledge-mcp` Python venv.
With that gone, they need a venv of their own — open backlog item.
Until then, `uv run --with <deps> python harvest.py` will work for
ad-hoc runs once dependencies are inferred from the imports.
