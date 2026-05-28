"""Stage D — distillation pack builder.

Given a list of source ids (from a Stage C cluster), emit a compact text bundle
mixing per-source metadata + sampled assistant turns + first/last user turns
suitable for in-session synthesis by Claude.

Filters per Stage D plan:
  - user/assistant text only (no tool_result bodies)
  - drop blocks longer than 200 tokens (~800 chars) for tool_result-like content
  - drop system-reminders

Usage:
    python distil_pack.py --ids id1,id2,id3 --out pack.txt
    python distil_pack.py --cluster C1#0 --pass C1 --out pack.txt
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pyarrow.parquet as pq

from kb_paths import resolve_kb_paths

KB, HARVEST, _ = resolve_kb_paths()
SOURCES = HARVEST / "sources_with_summary.parquet"
THEMES = HARVEST / "themes_raw.json"

MAX_TURNS_PER_SESSION = 8
MAX_TURN_CHARS = 800


def _extract_blocks(content) -> list[str]:
    if content is None:
        return []
    if isinstance(content, str):
        return [content]
    out = []
    if isinstance(content, list):
        for b in content:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "text":
                out.append(b.get("text", ""))
    return out


def harvest_chat(path: Path) -> list[tuple[str, str]]:
    """Return [(role, text)] from a JSONL session, dropping tool_result + reminders."""
    if not path.exists():
        return []
    out: list[tuple[str, str]] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = ev.get("message") or {}
                role = msg.get("role") if isinstance(msg, dict) else None
                if role not in ("user", "assistant"):
                    continue
                texts = _extract_blocks(msg.get("content"))
                joined = "\n".join(t for t in texts if t).strip()
                if not joined:
                    continue
                # drop system-reminder bodies
                if "<system-reminder>" in joined or joined.startswith("[Request interrupted"):
                    continue
                # drop pure IDE event wrappers
                if joined.startswith("<ide_") and len(joined) < 400:
                    continue
                if len(joined) > MAX_TURN_CHARS:
                    joined = joined[:MAX_TURN_CHARS].rstrip() + "..."
                out.append((role, joined))
    except OSError:
        return []
    if not out:
        return []
    # Take first 3, last 3, and a sample from the middle
    if len(out) <= MAX_TURNS_PER_SESSION:
        return out
    head = out[:3]
    tail = out[-3:]
    mid_idx = len(out) // 2
    mid = out[mid_idx - 1 : mid_idx + 2]
    return head + mid + tail


def render_row(r: dict) -> str:
    """Render one source's distillation pack."""
    st = r["source_type"]
    sid = r["id"]
    summary = r.get("summary_oneline") or ""
    title = (r.get("title") or "").strip()
    lines = [f"### [{st}] {title or sid}", f"id: {sid}", f"summary: {summary}"]
    if st == "chat":
        lines.append(f"cwd: {r.get('cwd')}")
        lines.append(f"tools: {(r.get('tool_call_sequence') or '')[:200]}")
        files = (r.get("files_touched") or [])[:6]
        if files:
            lines.append(f"files: {', '.join(files)}")
        # Pull turns from JSONL
        for path_str in (r.get("source_paths") or [])[:1]:
            turns = harvest_chat(Path(path_str))
            for role, text in turns:
                lines.append(f"[{role}] {text}")
    elif st == "confluence_page":
        body = (r.get("body") or "").strip()
        lines.append(f"url: {r.get('url')}")
        lines.append(f"body_len: {len(body)}")
        lines.append(f"body:")
        lines.append(body[:3000] if body else "(title-only — lazy-fetch needed)")
    elif st in ("github_pr", "github_review"):
        lines.append(f"repo: {r.get('repo')}")
        lines.append(f"url: {r.get('url')}")
        body = (r.get("body") or "").strip()
        diff = (r.get("diff_hunk") or "").strip()
        if diff:
            lines.append(f"diff: {diff[:600]}")
        if body:
            lines.append(f"body: {body[:1500]}")
    elif st == "local_md":
        body = (r.get("body") or "").strip()
        lines.append(f"path: {(r.get('source_paths') or [''])[0]}")
        lines.append(f"body:")
        lines.append(body[:3000])
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", help="comma-separated id list")
    ap.add_argument("--cluster", help="cluster id like 'C1#0' or 'C2#3'")
    ap.add_argument("--out", required=True, help="output path for the pack")
    ap.add_argument("--max-rows", type=int, default=20)
    args = ap.parse_args()

    rows = {r["id"]: r for r in pq.read_table(SOURCES).to_pylist()}

    ids: list[str] = []
    if args.ids:
        ids = [s.strip() for s in args.ids.split(",") if s.strip()]
    elif args.cluster:
        themes = json.loads(THEMES.read_text(encoding="utf-8"))
        m = re.match(r"C([12])#(\d+)", args.cluster)
        if not m:
            print("[err] cluster format: C1#N or C2#N", file=sys.stderr)
            return 1
        pass_key = "C1_topic" if m.group(1) == "1" else "C2_meta"
        cid = int(m.group(2))
        for c in themes[pass_key]:
            if c["cluster_id"] == cid:
                ids = [m["id"] for m in c["members"]]
                break
        if not ids:
            print(f"[err] cluster {args.cluster} not found", file=sys.stderr)
            return 1
    else:
        print("[err] --ids or --cluster required", file=sys.stderr)
        return 1

    ids = ids[: args.max_rows]
    blocks = []
    for sid in ids:
        if sid not in rows:
            blocks.append(f"### MISSING id={sid}")
            continue
        blocks.append(render_row(rows[sid]))

    out_path = Path(args.out)
    out_path.write_text("\n\n---\n\n".join(blocks), encoding="utf-8")
    print(f"[pack] wrote {len(blocks)} sources to {out_path}")
    print(f"[pack] size {out_path.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
