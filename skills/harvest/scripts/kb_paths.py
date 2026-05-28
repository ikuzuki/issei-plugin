"""Shared Knowledge Base path resolution for harvest pipeline scripts.

All scripts in this folder resolve their working paths via the helpers
here. Order of preference:

1. ``KNOWLEDGE_VAULT_PATH`` + ``HARVEST_OUTPUT_PATH`` env vars (set by
   the harvest skill, or by the user manually).
2. Walk up from the script looking for a ``knowledge-vault/`` sibling
   (works in the Knowledge Base source tree).
3. SystemExit with a clear message.

When the scripts run inside an installed plugin (e.g.
``~/.claude/plugins/cache/issei-plugin/.../skills/harvest/scripts/``),
the walk-up fallback won't find the vault — env vars are required. The
harvest skill always sets them before invoking a script, so the normal
path works without surprises.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def resolve_kb_paths() -> tuple[Path, Path, Path]:
    """Return ``(kb_root, harvest_dir, vault_dir)`` for harvest scripts.

    Use this when a script needs both the harvest output dir (for
    parquet I/O) and the vault dir (for daily/ and reference/ writes).
    """
    vault_env = os.environ.get("KNOWLEDGE_VAULT_PATH")
    harvest_env = os.environ.get("HARVEST_OUTPUT_PATH")
    if vault_env and harvest_env:
        vault = Path(vault_env).resolve()
        harvest = Path(harvest_env).resolve()
        return harvest.parent, harvest, vault

    for parent in Path(__file__).resolve().parents:
        if (parent / "knowledge-vault").is_dir():
            return parent, parent / "harvest", parent / "knowledge-vault"

    sys.exit(
        "kb_paths: KNOWLEDGE_VAULT_PATH and HARVEST_OUTPUT_PATH env vars "
        "not set, and no knowledge-vault/ sibling found via walk-up. Set "
        "both env vars."
    )


def resolve_vault_only() -> Path:
    """Return just the vault dir. For scripts that only touch the vault."""
    vault_env = os.environ.get("KNOWLEDGE_VAULT_PATH") or os.environ.get(
        "KNOWLEDGE_MCP_VAULT_PATH"
    )
    if vault_env:
        path = Path(vault_env).resolve()
        if not path.is_dir():
            sys.exit(f"kb_paths: vault path does not exist: {path}")
        return path

    for parent in Path(__file__).resolve().parents:
        candidate = parent / "knowledge-vault"
        if candidate.is_dir():
            return candidate

    sys.exit(
        "kb_paths: KNOWLEDGE_VAULT_PATH not set and no knowledge-vault/ "
        "sibling found via walk-up."
    )
