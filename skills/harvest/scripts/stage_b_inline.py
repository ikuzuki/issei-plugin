"""Inline Stage B helper for in-session summarisation.

Used when Claude (the agent) generates summaries directly rather than via the
local Ollama path in stage_b.py. Two modes:

    # Show batch N (20 rows of in-scope, un-summarised items) as compact input blobs.
    python stage_b_inline.py show --batch 0

    # Persist a batch of {id: summary} pairs to sources_with_summary.parquet.
    python stage_b_inline.py write --json '{"id1":"summary 1","id2":"summary 2"}'

    # One-shot remaining-count report.
    python stage_b_inline.py status
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from kb_paths import resolve_kb_paths

KB, HARVEST, _ = resolve_kb_paths()
SOURCES = HARVEST / "sources.parquet"
OUT = HARVEST / "sources_with_summary.parquet"

BATCH_SIZE = 20


def _sample_assistant_turns(source_paths: list[str], n: int = 2) -> list[str]:
    if not source_paths:
        return []
    p = Path(source_paths[0])
    if not p.exists():
        return []
    turns: list[str] = []
    try:
        with p.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = ev.get("message") or {}
                role = msg.get("role") if isinstance(msg, dict) else None
                if role != "assistant" and ev.get("type") != "assistant":
                    continue
                c = msg.get("content")
                parts: list[str] = []
                if isinstance(c, list):
                    for b in c:
                        if isinstance(b, dict) and b.get("type") == "text":
                            parts.append(b.get("text", ""))
                elif isinstance(c, str):
                    parts.append(c)
                t = "\n".join(parts).strip()
                if len(t) > 30:
                    turns.append(t)
    except OSError:
        return []
    if not turns:
        return []
    if len(turns) <= n:
        return [t[:400] for t in turns]
    mid = len(turns) // (n + 1)
    return [turns[mid * (i + 1)][:400] for i in range(n)]


def build_input(row: dict) -> str:
    st = row["source_type"]
    title = (row.get("title") or "").strip()[:160]
    if st == "chat":
        fu = (row.get("first_user_message") or "")[:400]
        lu = (row.get("last_user_message") or "")[:300]
        tools = (row.get("tool_call_sequence") or "")[:150]
        files = ", ".join((row.get("files_touched") or [])[:5])
        samples = _sample_assistant_turns(row.get("source_paths") or [], n=2)
        mid = "\n".join(f"  mid-turn {i+1}: {s[:300]}" for i, s in enumerate(samples))
        return (
            f"[chat session]\n"
            f"title: {title}\n"
            f"first user: {fu}\n"
            f"last user: {lu}\n"
            f"{mid}\n"
            f"tools: {tools}\n"
            f"files: {files}"
        ).strip()
    if st == "confluence_page":
        body = (row.get("body") or "")[:900]
        labels = ", ".join(row.get("labels") or [])
        return f"[confluence page]\ntitle: {title}\nlabels: {labels}\nbody: {body}"
    if st == "github_pr":
        body = (row.get("body") or "")[:900]
        return f"[PR in {row.get('repo')}]\ntitle: {title}\nbody: {body}"
    if st == "github_review":
        diff = (row.get("diff_hunk") or "")[:400]
        cmt = (row.get("body") or "")[:600]
        return f"[PR review in {row.get('repo')}]\ndiff: {diff}\ncomment: {cmt}"
    if st == "local_md":
        body = (row.get("body") or "")[:900]
        return f"[local markdown]\ntitle: {title}\nbody: {body}"
    return title


def _load_rows() -> tuple[pa.Table, list[dict], dict[str, str]]:
    src = pq.read_table(SOURCES)
    rows = src.to_pylist()
    existing: dict[str, str] = {}
    if OUT.exists():
        tbl = pq.read_table(OUT, columns=["id", "summary_oneline"])
        for r in tbl.to_pylist():
            if r.get("summary_oneline"):
                existing[r["id"]] = r["summary_oneline"]
    return src, rows, existing


def _pending(rows: list[dict], existing: dict[str, str]) -> list[dict]:
    """Rows that still need a summary. Excludes privacy_tag=excluded."""
    return [
        r for r in rows
        if r.get("privacy_tag") != "excluded" and r["id"] not in existing
    ]


def cmd_status() -> int:
    src, rows, existing = _load_rows()
    pending = _pending(rows, existing)
    from collections import Counter
    by_type = Counter(r["source_type"] for r in pending)
    print(f"total={len(rows)} summarised={len(existing)} pending={len(pending)}")
    print(f"pending by source_type: {dict(by_type)}")
    return 0


def cmd_show(batch_idx: int, size: int) -> int:
    src, rows, existing = _load_rows()
    pending = _pending(rows, existing)
    start = batch_idx * size
    batch = pending[start : start + size]
    if not batch:
        print(f"[empty batch — {len(pending)} rows pending, batch_idx too high]")
        return 0
    print(f"# Batch {batch_idx}  rows {start}..{start + len(batch) - 1}  "
          f"of {len(pending)} pending", flush=True)
    for r in batch:
        print("=== BEGIN ROW ===")
        print(f"id: {r['id']}")
        print(f"source_type: {r['source_type']}")
        print(build_input(r))
        print("=== END ROW ===\n")
    return 0


def cmd_write(json_str: str) -> int:
    data = json.loads(json_str)
    if not isinstance(data, dict):
        print("[err] write expects JSON object {id: summary}", file=sys.stderr)
        return 1
    src, rows, existing = _load_rows()
    # Merge
    merged = dict(existing)
    merged.update({k: (v or "").strip() for k, v in data.items() if v})
    col = pa.array([merged.get(r["id"], "") for r in rows], type=pa.string())
    tbl = src
    if "summary_oneline" in tbl.schema.names:
        tbl = tbl.drop(["summary_oneline"])
    tbl = tbl.append_column("summary_oneline", col)
    pq.write_table(tbl, OUT)
    new_this_write = sum(1 for k in data if k not in existing and data[k])
    print(f"[write] merged={len(merged)} total (new this write: {new_this_write}) -> {OUT}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("show")
    s.add_argument("--batch", type=int, required=True)
    s.add_argument("--size", type=int, default=BATCH_SIZE)

    w = sub.add_parser("write")
    w.add_argument("--json", required=False)
    w.add_argument("--json-file", required=False)

    sub.add_parser("status")

    args = ap.parse_args()

    if args.cmd == "status":
        return cmd_status()
    if args.cmd == "show":
        return cmd_show(args.batch, args.size)
    if args.cmd == "write":
        if args.json_file:
            js = Path(args.json_file).read_text(encoding="utf-8")
        else:
            js = args.json or ""
        return cmd_write(js)
    return 1


if __name__ == "__main__":
    sys.exit(main())
