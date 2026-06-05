"""Render a single Claude Code session .jsonl to readable markdown on stdout.

Reuses the harvest pipeline's event renderer (user + assistant text in full,
tool calls compacted to one-liners, system/meta noise dropped). Use this to
read the substance of a thread's constituent sessions identified by
extract_threads.py.

Usage:
    python render_one.py "<full-path-to-session.jsonl>"
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HARVEST_SCRIPTS = HERE.parent.parent / "harvest" / "scripts"
sys.path.insert(0, str(HARVEST_SCRIPTS))
os.environ.setdefault(
    "KNOWLEDGE_VAULT_PATH", str(Path.home() / "Knowledge Base" / "knowledge-vault")
)
os.environ.setdefault(
    "HARVEST_OUTPUT_PATH", str(Path.home() / "Knowledge Base" / "harvest")
)

import harvest as H  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python render_one.py <path-to-jsonl>", file=sys.stderr)
        return 2
    p = Path(sys.argv[1])
    if not p.exists():
        print(f"not found: {p}", file=sys.stderr)
        return 1
    for ev in H._read_session_events(p):
        chunk = H._render_event(ev)
        if chunk:
            sys.stdout.write(chunk + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
