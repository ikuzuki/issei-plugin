"""Stage B — lightweight one-line summariser via local Ollama llama3.2:3b.

Reads harvest/sources.parquet, emits harvest/sources_with_summary.parquet
with an added `summary_oneline` column. Re-runnable: skips rows that already
have a non-empty summary unless --force.

Also supports an eval mode that samples N representative rows and emits a
review markdown file so a human can hand-label gold summaries.

See: knowledge-vault/projects/knowledge-base-harvest-plan.md (Stage B)
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from kb_paths import resolve_kb_paths

KB_ROOT, HARVEST, _ = resolve_kb_paths()
SOURCES = HARVEST / "sources.parquet"
OUT = HARVEST / "sources_with_summary.parquet"
EVAL_MD = HARVEST / "_stage_b_eval.md"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

SYSTEM_PROMPT = (
    "Summarise the work unit below in ONE short sentence (max 18 words). "
    "Name the concrete artefact, repo, or concept. Do NOT begin with "
    "'This is', 'The user', 'Issei', 'The task'. Output only the sentence."
)


def _sample_assistant_turns(source_paths: list[str], n: int = 2) -> list[str]:
    """Walk the first JSONL in source_paths and return n mid-thread assistant turns."""
    if not source_paths:
        return []
    path = Path(source_paths[0])
    if not path.exists():
        return []
    turns: list[str] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = ev.get("message") or {}
                role = msg.get("role") if isinstance(msg, dict) else None
                if role != "assistant" and ev.get("type") != "assistant":
                    continue
                content = msg.get("content")
                parts: list[str] = []
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            parts.append(block.get("text", ""))
                elif isinstance(content, str):
                    parts.append(content)
                text = "\n".join(parts).strip()
                if text and len(text) > 30:
                    turns.append(text)
    except OSError:
        return []
    if not turns:
        return []
    if len(turns) <= n:
        return [t[:400] for t in turns]
    mid = len(turns) // (n + 1)
    picks = [turns[mid * (i + 1)] for i in range(n)]
    return [t[:400] for t in picks]


def build_input(row: dict, include_assistant_samples: bool = False) -> str:
    st = row["source_type"]
    title = (row.get("title") or "").strip()[:160]
    if st == "chat":
        fu = (row.get("first_user_message") or "")[:300]
        lu = (row.get("last_user_message") or "")[:200]
        tools = (row.get("tool_call_sequence") or "")[:120]
        files = ", ".join((row.get("files_touched") or [])[:4])
        mid_block = ""
        if include_assistant_samples:
            samples = _sample_assistant_turns(row.get("source_paths") or [], n=2)
            mid_block = "\n".join(
                f"mid-turn {i+1}: {s[:200]}" for i, s in enumerate(samples)
            )
        return (
            f"[chat session]\n"
            f"title: {title}\n"
            f"first user msg: {fu}\n"
            f"last user msg: {lu}\n"
            f"{mid_block}\n"
            f"tools: {tools}\n"
            f"files: {files}"
        )
    if st == "confluence_page":
        body = (row.get("body") or "")[:500]
        labels = ", ".join(row.get("labels") or [])
        return (
            f"[confluence page]\n"
            f"title: {title}\n"
            f"labels: {labels}\n"
            f"excerpt: {body}"
        )
    if st == "github_pr":
        body = (row.get("body") or "")[:500]
        return (
            f"[PR in {row.get('repo')}]\n"
            f"title: {title}\n"
            f"body: {body}"
        )
    if st == "github_review":
        return (
            f"[PR review in {row.get('repo')}]\n"
            f"diff: {(row.get('diff_hunk') or '')[:250]}\n"
            f"comment: {(row.get('body') or '')[:400]}"
        )
    if st == "local_md":
        body = (row.get("body") or "")[:500]
        return (
            f"[local markdown]\n"
            f"title: {title}\n"
            f"body: {body}"
        )
    return title


def ollama_generate(prompt: str, timeout: int = 180, keep_alive: str = "10m") -> str:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "keep_alive": keep_alive,
        "options": {"temperature": 0.2, "num_predict": 64, "num_ctx": 2048},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    resp_text = (body.get("response") or "").strip()
    return resp_text.splitlines()[0][:280] if resp_text else ""


def warmup() -> None:
    """Load model into memory so first call doesn't time out."""
    try:
        ollama_generate("warmup: reply with the word OK.", timeout=120)
    except Exception as e:  # noqa: BLE001
        print(f"[warn] warmup failed: {e}", file=sys.stderr)


def sample_eval_rows(rows: list[dict], n: int = 20, seed: int = 7) -> list[dict]:
    """Stratified sample across source_types and privacy tags."""
    rnd = random.Random(seed)
    in_scope = [r for r in rows if r.get("privacy_tag") != "excluded"]
    buckets: dict[str, list[dict]] = {}
    for r in in_scope:
        buckets.setdefault(r["source_type"], []).append(r)

    # Target mix: 8 chat, 4 confluence_page, 2 github_pr, 6 github_review
    quotas = {"chat": 8, "confluence_page": 4, "github_pr": 2, "github_review": 6}
    out = []
    for st, q in quotas.items():
        pool = buckets.get(st, [])
        rnd.shuffle(pool)
        out.extend(pool[:q])

    # Top up to n from any remaining in-scope rows
    if len(out) < n:
        taken = {r["id"] for r in out}
        rest = [r for r in in_scope if r["id"] not in taken]
        rnd.shuffle(rest)
        out.extend(rest[: n - len(out)])
    return out[:n]


def write_eval_markdown(rows: list[dict], summaries: dict[str, str], path: Path) -> None:
    lines = [
        "# Stage B eval gate — 20-row hand-label sheet",
        "",
        ("Instructions: for each row, replace the `gold:` line with your own "
         "one-sentence summary of what the work actually was. Leave blank to "
         "skip. The agreement check compares your gold against the generated "
         "summary via cosine similarity on nomic embeddings."),
        "",
    ]
    for i, r in enumerate(rows, 1):
        st = r["source_type"]
        title = (r.get("title") or "").replace("\n", " ")[:120]
        fu = (r.get("first_user_message") or "").replace("\n", " ")[:200]
        body = (r.get("body") or "").replace("\n", " ")[:200]
        lines.extend([
            f"## {i}. [{st}] {title}",
            f"- id: `{r['id']}`",
            f"- cwd/repo/space: `{r.get('cwd') or r.get('repo') or r.get('space') or ''}`",
            f"- first_user/body: {fu or body}",
            f"- generated: **{summaries.get(r['id'], '(no summary)')}**",
            "- gold: _(fill in)_",
            "",
        ])
    path.write_text("\n".join(lines), encoding="utf-8")


def embed_cosine(a: str, b: str) -> float | None:
    """Cosine similarity via nomic-embed-text for agreement scoring."""
    if not a or not b:
        return None
    try:
        def _emb(text: str) -> list[float]:
            req = urllib.request.Request(
                "http://localhost:11434/api/embeddings",
                data=json.dumps({"model": "nomic-embed-text:v1.5", "prompt": text}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))["embedding"]

        va, vb = _emb(a), _emb(b)
        dot = sum(x * y for x, y in zip(va, vb))
        na = sum(x * x for x in va) ** 0.5
        nb = sum(x * x for x in vb) ** 0.5
        return dot / (na * nb) if na and nb else None
    except Exception as e:  # noqa: BLE001
        print(f"[warn] embed failed: {e}", file=sys.stderr)
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval", action="store_true",
                    help="sample 20 rows, generate summaries, emit review markdown, stop")
    ap.add_argument("--eval-score", action="store_true",
                    help="re-read _stage_b_eval.md and compute agreement against gold labels")
    ap.add_argument("--force", action="store_true",
                    help="overwrite existing summaries")
    ap.add_argument("--limit", type=int, default=None,
                    help="cap rows summarised (for testing)")
    ap.add_argument("--only", default=None,
                    help="filter by source_type (chat|confluence_page|github_pr|github_review|local_md)")
    ap.add_argument("--workers", type=int, default=1,
                    help="concurrent Ollama requests (default 1; CPU inference rarely gains)")
    ap.add_argument("--assistant-samples", action="store_true",
                    help="include 2 sampled mid-thread assistant turns in chat input (slower)")
    args = ap.parse_args()

    if not SOURCES.exists():
        print(f"[err] {SOURCES} missing — run harvest.py first", file=sys.stderr)
        return 1

    src_tbl = pq.read_table(SOURCES)
    rows = src_tbl.to_pylist()
    print(f"[B] loaded {len(rows)} rows from {SOURCES.name}")

    # Start from any existing summaries parquet to preserve prior work
    existing_summaries: dict[str, str] = {}
    if OUT.exists() and not args.force:
        for r in pq.read_table(OUT, columns=["id", "summary_oneline"]).to_pylist():
            if r.get("summary_oneline"):
                existing_summaries[r["id"]] = r["summary_oneline"]
        print(f"[B] reusing {len(existing_summaries)} existing summaries")

    if args.eval:
        sample = sample_eval_rows(rows, n=20)
        print(f"[B-eval] warming model...")
        warmup()
        print(f"[B-eval] sampled {len(sample)} rows; summarising with {MODEL}")
        gen = {}
        for i, r in enumerate(sample, 1):
            if r["id"] in existing_summaries and not args.force:
                gen[r["id"]] = existing_summaries[r["id"]]
            else:
                try:
                    s = ollama_generate(build_input(r))
                    gen[r["id"]] = s
                except Exception as e:  # noqa: BLE001
                    print(f"  {i}/{len(sample)} ERROR: {e}")
                    gen[r["id"]] = "(generation failed)"
            print(f"  {i}/{len(sample)} [{r['source_type']}] {gen[r['id']][:100]}")
        write_eval_markdown(sample, gen, EVAL_MD)
        print(f"[B-eval] wrote {EVAL_MD}")
        return 0

    if args.eval_score:
        return _score_eval(rows)

    # Full Stage B run (gated behind explicit invocation — not the default)
    targets = rows
    if args.only:
        targets = [r for r in targets if r["source_type"] == args.only]
    if args.limit:
        targets = targets[: args.limit]
    targets = [r for r in targets if r.get("privacy_tag") != "excluded"]

    produced = dict(existing_summaries)
    to_do = [r for r in targets if r["id"] not in produced or args.force]
    print(f"[B] to summarise: {len(to_do)} (already cached: {len(targets) - len(to_do)})")

    def _one(r: dict) -> tuple[str, str, str | None]:
        try:
            return r["id"], ollama_generate(build_input(r, args.assistant_samples)), None
        except Exception as e:  # noqa: BLE001
            # Fallback to title-based synthetic summary on timeout/failure so
            # downstream clustering still has *something*.
            fallback = (r.get("title") or "")[:200].strip()
            if fallback:
                fallback = f"[title-only fallback] {fallback}"
            return r["id"], fallback, str(e)

    n_new = 0
    n_err = 0
    n_fallback = 0
    workers = max(1, args.workers)
    # Incremental parquet writes every CHECKPOINT rows so a long run can resume
    CHECKPOINT = 25

    def _flush():
        new_schema_col = pa.array(
            [produced.get(r["id"], "") for r in rows], type=pa.string()
        )
        # remove existing column if re-writing
        out_tbl = src_tbl
        if "summary_oneline" in out_tbl.schema.names:
            out_tbl = out_tbl.drop(["summary_oneline"])
        out_tbl = out_tbl.append_column("summary_oneline", new_schema_col)
        pq.write_table(out_tbl, OUT)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_one, r): r for r in to_do}
        for i, fut in enumerate(as_completed(futures), 1):
            rid, summary, err = fut.result()
            if err:
                n_err += 1
                if summary:
                    n_fallback += 1
                    produced[rid] = summary
                if n_err <= 30:
                    print(f"  [{i}/{len(to_do)}] ERROR {rid[:50]}: {err}", file=sys.stderr, flush=True)
            else:
                n_new += 1
                produced[rid] = summary
            if i % 5 == 0 or i == len(to_do):
                print(f"  [{i}/{len(to_do)}] new={n_new} fallback={n_fallback} err={n_err}",
                      flush=True)
            if i % CHECKPOINT == 0:
                _flush()
                print(f"  [checkpoint] wrote partial parquet at {i}", flush=True)
    _flush()

    print(f"[B] wrote {OUT} rows={src_tbl.num_rows} new={n_new} fallback={n_fallback} err={n_err}")
    return 0


def _score_eval(rows: list[dict]) -> int:
    if not EVAL_MD.exists():
        print(f"[err] {EVAL_MD} missing — run with --eval first", file=sys.stderr)
        return 1
    text = EVAL_MD.read_text(encoding="utf-8")
    # Parse generated + gold per row
    import re
    pairs = []
    blocks = re.split(r"\n## \d+\. ", text)[1:]
    for blk in blocks:
        id_m = re.search(r"- id: `([^`]+)`", blk)
        gen_m = re.search(r"- generated: \*\*([^*]+)\*\*", blk)
        gold_m = re.search(r"- gold: (.+)", blk)
        if not (id_m and gen_m and gold_m):
            continue
        gid = id_m.group(1).strip()
        gen = gen_m.group(1).strip()
        gold = gold_m.group(1).strip()
        if gold.startswith("_(") or not gold:
            continue
        pairs.append((gid, gen, gold))
    print(f"[B-score] {len(pairs)} labelled rows")
    sims = []
    for gid, gen, gold in pairs:
        s = embed_cosine(gen, gold)
        if s is not None:
            sims.append(s)
            print(f"  {s:.3f}  [{gid[:40]}] gen={gen[:60]} // gold={gold[:60]}")
    if sims:
        sims.sort()
        mean = sum(sims) / len(sims)
        pct_above = sum(1 for s in sims if s >= 0.70) / len(sims)
        print(f"[B-score] mean cosine={mean:.3f}  pct>=0.70={pct_above:.0%}  "
              f"p25={sims[len(sims)//4]:.3f}  p50={sims[len(sims)//2]:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
