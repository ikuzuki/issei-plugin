"""List Issei's team work-threads from the sprint window, for review/retro prep.

Reuses the harvest pipeline's session parser (single source of truth for
team-vs-personal classification) rather than reimplementing it. Prints a
scannable per-thread summary including the source `.jsonl` paths so the
caller (or a mining subagent) can render full content with render_one.py.

Usage:
    python extract_threads.py --since 2026-05-25      # sprint start date
    python extract_threads.py --days 16               # fallback window

Only `privacy_tag == "work"` threads with >= MIN_MSGS substantive user
messages are printed. Scheduled-task autorun-only threads are flagged
([autorun?]) not dropped — long threads often merge an autorun session
with real dev work in the same cwd; let the reader judge the substance.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Resolve the co-located harvest module (same plugin, both in source tree
# and in the installed cache). Set KB env defaults before import — harvest
# resolves vault/harvest paths at module load.
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

MIN_MSGS = 5
AUTORUN_PREFIXES = (
    "<scheduled-task",
    "base directory for this skill:",
)
# First-message prefixes that mark a thread as pure wrapper noise (slash-command
# runs, plugin-update checks) with no real conversation - drop entirely.
NOISE_PREFIXES = (
    "<local-command-caveat",
    "<command-message",
)
# cwd fragments that match harvest's WORK list (via "/knowledge base") but are
# actually Issei's PERSONAL admin, not CDT team work - drop for a team review.
# `issei-plugin` is his personal plugin; vault maintenance is personal upkeep.
PERSONAL_ADMIN_FRAGMENTS = (
    "/issei-plugin",
    "/knowledge-vault",
)


def is_autorun(first_msg: str) -> bool:
    fm = (first_msg or "").strip().lower()
    return any(fm.startswith(p) for p in AUTORUN_PREFIXES)


def is_noise(first_msg: str) -> bool:
    fm = (first_msg or "").strip().lower()
    return not fm or any(fm.startswith(p) for p in NOISE_PREFIXES)


def is_personal_admin(cwd: str | None) -> bool:
    c = (cwd or "").lower()
    return any(frag in c for frag in PERSONAL_ADMIN_FRAGMENTS)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", help="window start, YYYY-MM-DD (preferred)")
    ap.add_argument("--days", type=int, default=16,
                    help="fallback window length in days (default 16)")
    args = ap.parse_args()

    if args.since:
        cutoff = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc)
    else:
        cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)

    rows, seen = [], set()
    for surface, path, key in H.walk_chat_jsonls():
        if key in seen:
            continue
        seen.add(key)
        r = H.parse_chat_session(surface, path, key)
        if not r or not r["ended_at"] or r["ended_at"] < cutoff:
            continue
        rows.append(r)

    threads = H.group_chat_threads(rows)
    threads = [t for t in threads if t.get("privacy_tag") == "work"]
    threads = [t for t in threads if (t.get("user_message_count") or 0) >= MIN_MSGS]
    threads = [t for t in threads if not is_noise(t.get("first_user_message"))]
    threads = [t for t in threads if not is_personal_admin(t.get("cwd"))]
    threads.sort(key=lambda t: t["ended_at"] or t["started_at"])

    print(f"# {len(threads)} team work-threads since {cutoff.date()}\n")
    for t in threads:
        started = t["started_at"].strftime("%Y-%m-%d %H:%M")
        ended = t["ended_at"].strftime("%m-%d %H:%M") if t["ended_at"] else "?"
        cwd = (t.get("cwd") or "").rsplit("/", 1)[-1]
        dur = round((t.get("duration_s") or 0) / 60)
        flag = " [autorun?]" if is_autorun(t.get("first_user_message")) else ""
        print(f"## {started}->{ended} [{cwd}] {dur}min "
              f"({t['user_message_count']}msg){flag}")
        print(f"   title: {(t.get('title') or '').splitlines()[0][:100]}")
        branches = t.get("branch_names") or []
        if branches:
            print(f"   branches: {branches}")
        fm = (t.get("first_user_message") or "").replace("\n", " ").strip()[:240]
        print(f"   first: {fm}")
        print(f"   tools: {t.get('tool_call_sequence')}")
        files = [f for f in (t.get("files_touched") or []) if "tool-results" not in f]
        if files:
            print(f"   files: {files[:10]}")
        print(f"   paths: {t.get('source_paths')}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
