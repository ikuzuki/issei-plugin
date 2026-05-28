"""Stage A / A.5 harvester for the knowledge-base bootstrap pass.

Reads:
  - ~/.claude/projects/**/*.jsonl  (Claude Code, VS Code extension, CLI)
  - ~/AppData/Roaming/Claude/local-agent-mode-sessions/**/audit.jsonl  (Desktop + Cowork)
    joined with sibling local_<uuid>.json for real cwd + title
  - harvest/_confluence_raw.json   (populated out-of-band via Atlassian MCP)
  - `gh` CLI for authored PRs + review comments (both logins)

Writes:
  - harvest/sources.parquet         unified Stage A rows
  - harvest/work_threads.parquet    chat-only post-A.5 grouping
  - harvest/archive/sources_pre_cutoff.parquet   cold archive
  - knowledge-vault/daily/YYYY-Www-activity.md   weekly rollups

Re-runnable. Skips already-extracted IDs tracked in sources.parquet.

See: knowledge-vault/projects/knowledge-base-harvest-plan.md
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

import pyarrow as pa
import pyarrow.parquet as pq

from kb_paths import resolve_kb_paths

# ---------------------------------------------------------------------------
# Paths

HOME = Path.home()
KB_ROOT, HARVEST, VAULT = resolve_kb_paths()
DAILY = VAULT / "daily"
# Stage A1.5 — full per-thread session content as readable markdown.
# Gitignored via knowledge-vault/.gitignore (`/reference/`).
REF_SESSIONS = VAULT / "reference" / "sessions"

CLAUDE_CODE_ROOT = HOME / ".claude" / "projects"
DESKTOP_ROOT = HOME / "AppData" / "Roaming" / "Claude" / "local-agent-mode-sessions"

CONFLUENCE_RAW = HARVEST / "_confluence_raw.json"

# A4 — local markdown roots (one-off dump into the distilled vault).
LOCAL_MD_ROOTS = [
    HOME / "intech-ai-plugin" / "docs",
    HOME / "intech-enrich" / "fodi_docs",
]

# ---------------------------------------------------------------------------
# Config

RECENCY_WEEKS = 12
GH_LOGINS = {"Issei-curve", "ikuzuki"}

# cwd allowlist fragments (case-insensitive). Matching is substring against
# canonicalised cwd (forward-slashed, lower-cased, worktree-stripped).
WORK_CWD_FRAGMENTS = [
    "/intech-api", "/intech-data", "/intech-enrich", "/intech-enrich-poc",
    "/intech-etl", "/intech-hub", "/intech-utils", "/intech-ai-plugin",
    "/intech-meta", "/intech-cicd", "/intech-infra",
    "/curve-daas", "/curve-hub", "/curve-hackathon",
    "/claude/claudemaxing", "/knowledge base",
    "/projects/intech", "/sandbox",
]
FPL_CWD_FRAGMENTS = ["/fpl-platform", "/fpl project"]

EXCLUDED_KEYWORDS = [
    r"\bsalary\b", r"\bcomp(ensation)?\b", r"\bhr\b",
    r"\bperformance review\b", r"\bterminat(ed|ion)\b",
    r"\bdisciplinary\b", r"\bmedical\b", r"\btherapist\b",
]
EXCLUDED_RE = re.compile("|".join(EXCLUDED_KEYWORDS), re.IGNORECASE)

WORKTREE_RE = re.compile(r"[\\/]\.claude[\\/]worktrees[\\/][^\\/]+", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Utilities


def canonicalise_cwd(cwd: str | None) -> str | None:
    if not cwd:
        return None
    c = cwd.replace("\\", "/").lower()
    c = WORKTREE_RE.sub("", c)
    c = c.rstrip("/")
    return c


def privacy_route(cwd_canon: str | None, first_messages: list[str]) -> tuple[str, str | None]:
    blob = "\n".join(m or "" for m in first_messages[:3])
    m = EXCLUDED_RE.search(blob)
    if m:
        return "excluded", m.group(0)
    if cwd_canon:
        if any(frag in cwd_canon for frag in WORK_CWD_FRAGMENTS):
            return "work", None
        if any(frag in cwd_canon for frag in FPL_CWD_FRAGMENTS):
            return "fpl", None
    return "personal", None


def to_utc(ts: Any) -> datetime | None:
    if ts is None or ts == "" or ts == "0001-01-01T00:00:00Z":
        return None
    if isinstance(ts, (int, float)):
        if ts <= 0:
            return None
        if ts > 1e12:  # ms epoch
            ts = ts / 1000.0
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    if isinstance(ts, str):
        try:
            s = ts.replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if dt.year < 1970:
                return None
            return dt.astimezone(timezone.utc)
        except ValueError:
            return None
    return None


def iso_week_label(dt: datetime) -> str:
    iso = dt.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def extract_text(content: Any) -> str:
    """Pull text from Claude-format message content (str | list[blocks])."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            t = block.get("type")
            if t == "text":
                parts.append(block.get("text", ""))
            elif t == "tool_use":
                name = block.get("name", "")
                parts.append(f"<tool_use:{name}>")
        return "\n".join(parts)
    return ""


def tool_name_from_event(ev: dict) -> str | None:
    msg = ev.get("message") or {}
    content = msg.get("content")
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                return block.get("name")
    return None


def compact_tool_sequence(tool_counts: Counter) -> str:
    return ",".join(f"{name}x{n}" for name, n in tool_counts.most_common(10))


# ---------------------------------------------------------------------------
# Stage A1 — chat sessions


def walk_chat_jsonls() -> Iterable[tuple[str, Path, str]]:
    """Yield (surface, path, session_key) for every chat-ish JSONL on disk.

    session_key is a stable identifier used to dedupe across re-runs; for
    Claude Code it's the filename stem (session uuid), for Desktop it's the
    session directory name (local_<uuid>).
    """
    if CLAUDE_CODE_ROOT.exists():
        for project_dir in CLAUDE_CODE_ROOT.iterdir():
            if not project_dir.is_dir():
                continue
            for jsonl in project_dir.glob("*.jsonl"):
                yield ("claude_code", jsonl, jsonl.stem)

    if DESKTOP_ROOT.exists():
        # Desktop layout: <agent_id>/<cli_session_id>/local_<uuid>/audit.jsonl
        for audit in DESKTOP_ROOT.glob("*/*/local_*/audit.jsonl"):
            yield ("claude_desktop", audit, audit.parent.name)


def parse_chat_session(surface: str, path: Path, session_key: str) -> dict | None:
    """Parse one JSONL into the unified Stage A row for a chat session."""
    try:
        size_bytes = path.stat().st_size
    except OSError:
        return None

    first_user: str | None = None
    last_user: str | None = None
    user_msgs: list[str] = []
    assistant_turns = 0
    tool_counts: Counter = Counter()
    files_touched: set[str] = set()
    commit_shas: set[str] = set()
    branch_names: set[str] = set()
    cwd_raw: str | None = None
    client_platform: str | None = None
    first_ts: datetime | None = None
    last_ts: datetime | None = None
    session_id: str | None = None
    title: str | None = None

    commit_re = re.compile(r"\b([0-9a-f]{7,40})\b")

    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = to_utc(ev.get("timestamp") or ev.get("_audit_timestamp"))
                if ts:
                    if first_ts is None or ts < first_ts:
                        first_ts = ts
                    if last_ts is None or ts > last_ts:
                        last_ts = ts
                if cwd_raw is None and ev.get("cwd"):
                    cwd_raw = ev.get("cwd")
                if client_platform is None and ev.get("client_platform"):
                    client_platform = ev.get("client_platform")
                if session_id is None and ev.get("session_id"):
                    session_id = ev.get("session_id")
                if title is None and ev.get("type") == "summary" and ev.get("summary"):
                    title = ev.get("summary")

                etype = ev.get("type")
                msg = ev.get("message") or {}
                role = msg.get("role") if isinstance(msg, dict) else None

                if etype == "user" or role == "user":
                    text = extract_text(msg.get("content"))
                    # Skip synthetic tool_result-only user turns
                    if text.strip() and not text.strip().startswith("<tool_use:"):
                        if first_user is None:
                            first_user = text
                        last_user = text
                        user_msgs.append(text)
                elif etype == "assistant" or role == "assistant":
                    assistant_turns += 1
                    tname = tool_name_from_event(ev)
                    if tname:
                        tool_counts[tname] += 1

                # files_touched / commit_shas / branch_names from tool_use inputs
                if isinstance(msg.get("content"), list):
                    for block in msg["content"]:
                        if not isinstance(block, dict):
                            continue
                        if block.get("type") == "tool_use":
                            inp = block.get("input") or {}
                            fp = inp.get("file_path") or inp.get("path")
                            if isinstance(fp, str):
                                files_touched.add(fp)
                            cmd = inp.get("command")
                            if isinstance(cmd, str):
                                if "git checkout -b" in cmd or "git switch -c" in cmd:
                                    m = re.search(r"(?:checkout -b|switch -c)\s+(\S+)", cmd)
                                    if m:
                                        branch_names.add(m.group(1))
                                for sha in commit_re.findall(cmd):
                                    if len(sha) >= 7:
                                        commit_shas.add(sha[:12])
    except OSError:
        return None

    if first_ts is None:
        return None

    duration_s = int((last_ts - first_ts).total_seconds()) if last_ts else 0

    # Desktop: join sibling metadata JSON for real cwd + title
    if surface == "claude_desktop":
        meta_path = path.parent.parent / f"{path.parent.name}.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                real_cwd = meta.get("cwd")
                # Only override if the real cwd is a user path, not the outputs sub-dir
                if real_cwd and "local-agent-mode-sessions" not in real_cwd:
                    cwd_raw = real_cwd
                if meta.get("title"):
                    title = meta["title"]
                if meta.get("createdAt"):
                    mt = to_utc(meta["createdAt"])
                    if mt and (first_ts is None or mt < first_ts):
                        first_ts = mt
                if meta.get("lastActivityAt"):
                    lt = to_utc(meta["lastActivityAt"])
                    if lt and (last_ts is None or lt > last_ts):
                        last_ts = lt
            except (OSError, json.JSONDecodeError):
                pass

    cwd_canon = canonicalise_cwd(cwd_raw)
    privacy, reason = privacy_route(cwd_canon, user_msgs)

    if not title:
        title = (first_user or "").strip().splitlines()[0][:80] if first_user else session_key

    return {
        "id": session_key,
        "source_type": "chat",
        "surface": client_platform or surface,
        "cwd": cwd_canon,
        "cwd_raw": cwd_raw,
        "repo": None,
        "space": None,
        "title": title,
        "started_at": first_ts,
        "ended_at": last_ts,
        "duration_s": duration_s,
        "first_user_message": (first_user or "")[:4000],
        "last_user_message": (last_user or "")[:4000],
        "user_message_count": len(user_msgs),
        "assistant_turn_count": assistant_turns,
        "tool_call_sequence": compact_tool_sequence(tool_counts),
        "files_touched": sorted(files_touched)[:50],
        "commit_shas": sorted(commit_shas)[:20],
        "branch_names": sorted(branch_names)[:10],
        "body": None,
        "diff_hunk": None,
        "labels": [],
        "url": None,
        "privacy_tag": privacy,
        "privacy_reason": reason,
        "size_bytes": size_bytes,
        "source_paths": [str(path)],
        "work_thread_id": None,
        "harvested_at": datetime.now(timezone.utc),
    }


# ---------------------------------------------------------------------------
# Stage A2 — Confluence (from MCP-populated cache)


def load_confluence(path: Path) -> list[dict]:
    if not path.exists():
        print(f"[warn] {path} missing — skipping Confluence (A2)", file=sys.stderr)
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for page in data:
        created = to_utc(page.get("created_at"))
        updated = to_utc(page.get("updated_at")) or created
        body = page.get("body_markdown") or ""
        title = page.get("title") or ""
        rows.append({
            "id": f"confluence:{page['id']}",
            "source_type": "confluence_page",
            "surface": "confluence",
            "cwd": None,
            "cwd_raw": None,
            "repo": None,
            "space": page.get("space"),
            "title": title,
            "started_at": created,
            "ended_at": updated,
            "duration_s": 0,
            "first_user_message": title,
            "last_user_message": None,
            "user_message_count": 0,
            "assistant_turn_count": 0,
            "tool_call_sequence": "",
            "files_touched": [],
            "commit_shas": [],
            "branch_names": [],
            "body": body[:50000],
            "diff_hunk": None,
            "labels": page.get("labels") or [],
            "url": page.get("url"),
            "privacy_tag": "work",
            "privacy_reason": None,
            "size_bytes": len(body),
            "source_paths": [page.get("url") or ""],
            "work_thread_id": f"confluence:{page['id']}",
            "harvested_at": datetime.now(timezone.utc),
        })
    return rows


# ---------------------------------------------------------------------------
# Stage A4 — local markdown (one-off)


_HEADING_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def fetch_local_md(roots: list[Path]) -> list[dict]:
    rows: list[dict] = []
    now = datetime.now(timezone.utc)
    for root in roots:
        if not root.exists():
            print(f"[warn] A4 root missing: {root}", file=sys.stderr)
            continue
        for md in root.rglob("*.md"):
            try:
                text = md.read_text(encoding="utf-8", errors="replace")
            except OSError as e:
                print(f"[warn] A4 read failed {md}: {e}", file=sys.stderr)
                continue
            try:
                mtime = datetime.fromtimestamp(md.stat().st_mtime, tz=timezone.utc)
            except OSError:
                mtime = now
            m = _HEADING_RE.search(text)
            title = m.group(1).strip() if m else md.stem
            rows.append({
                "id": f"local_md:{md.as_posix()}",
                "source_type": "local_md",
                "surface": "local_md",
                "cwd": None,
                "cwd_raw": None,
                "repo": None,
                "space": None,
                "title": title[:200],
                "started_at": mtime,
                "ended_at": mtime,
                "duration_s": 0,
                "first_user_message": title,
                "last_user_message": None,
                "user_message_count": 0,
                "assistant_turn_count": 0,
                "tool_call_sequence": "",
                "files_touched": [],
                "commit_shas": [],
                "branch_names": [],
                "body": text[:50000],
                "diff_hunk": None,
                "labels": [],
                "url": md.resolve().as_uri(),
                "privacy_tag": "work",
                "privacy_reason": None,
                "size_bytes": len(text),
                "source_paths": [str(md)],
                "work_thread_id": f"local_md:{md.as_posix()}",
                "harvested_at": now,
            })
    return rows


# ---------------------------------------------------------------------------
# Stage A3 — GitHub (gh CLI + REST)


def gh_json(args: list[str]) -> Any:
    out = subprocess.run(
        ["gh", *args], capture_output=True, text=True, check=False,
        encoding="utf-8", errors="replace",
    )
    if out.returncode != 0:
        print(f"[warn] gh failed: {' '.join(args)}\n{(out.stderr or '')[:400]}", file=sys.stderr)
        return []
    if not (out.stdout or "").strip():
        return []
    return json.loads(out.stdout)


def fetch_github_prs(cutoff: datetime) -> list[dict]:
    iso = cutoff.strftime("%Y-%m-%d")
    fields = "url,title,body,createdAt,closedAt,repository,state,number"
    prs = gh_json([
        "search", "prs", "--author=@me",
        f"--created=>={iso}",
        "--limit", "500", "--json", fields,
    ])
    rows = []
    for pr in prs:
        created = to_utc(pr.get("createdAt"))
        closed = to_utc(pr.get("closedAt")) or created
        repo = pr.get("repository", {}).get("nameWithOwner")
        files: list[str] = []
        title = pr.get("title") or ""
        body = pr.get("body") or ""
        rows.append({
            "id": pr["url"],
            "source_type": "github_pr",
            "surface": "github",
            "cwd": None,
            "cwd_raw": None,
            "repo": repo,
            "space": None,
            "title": title,
            "started_at": created,
            "ended_at": closed,
            "duration_s": int((closed - created).total_seconds()) if (created and closed) else 0,
            "first_user_message": title,
            "last_user_message": None,
            "user_message_count": 0,
            "assistant_turn_count": 0,
            "tool_call_sequence": "",
            "files_touched": files[:50],
            "commit_shas": [],
            "branch_names": [],
            "body": body[:50000],
            "diff_hunk": None,
            "labels": [],
            "url": pr["url"],
            "privacy_tag": "work",
            "privacy_reason": None,
            "size_bytes": len(body),
            "source_paths": [pr["url"]],
            "work_thread_id": pr["url"],
            "harvested_at": datetime.now(timezone.utc),
        })
    return rows


def fetch_github_reviews(pr_rows: list[dict], cutoff: datetime) -> list[dict]:
    """Pull review comments per repo authored by known logins."""
    repos = sorted({r["repo"] for r in pr_rows if r.get("repo")})
    # Also pull from the broader repo list seen across all PRs (include older repos
    # that had reviews in-window even if we have no new PR there)
    extra_repos = [
        "curveanalytics/curve-daas", "curveanalytics/curve-hub",
        "curveanalytics/intech-api", "curveanalytics/intech-hub",
        "curveanalytics/intech-utils", "curveanalytics/intech-data",
        "curveanalytics/intech-enrich", "curveanalytics/intech-etl",
        "curveanalytics/intech-ai-plugin", "curveanalytics/intech-infra",
        "curveanalytics/intech-cicd", "curveanalytics/sandbox",
        "Issei-curve/intech-meta",
    ]
    repos = sorted(set(repos) | set(extra_repos))
    iso = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = []
    for repo in repos:
        out = subprocess.run(
            ["gh", "api", "--paginate",
             f"repos/{repo}/pulls/comments?per_page=100&since={iso}"],
            capture_output=True, text=True, check=False,
            encoding="utf-8", errors="replace",
        )
        if out.returncode != 0 or not (out.stdout or "").strip():
            continue
        # --paginate returns concatenated JSON arrays. Parse robustly.
        comments: list[dict] = []
        raw = out.stdout.strip()
        # Simple approach: split on "][" joins if multi-page
        try:
            comments = json.loads(raw)
        except json.JSONDecodeError:
            fixed = raw.replace("][", ",")
            try:
                comments = json.loads(fixed)
            except json.JSONDecodeError:
                continue
        for c in comments:
            user = (c.get("user") or {}).get("login")
            if user not in GH_LOGINS:
                continue
            created = to_utc(c.get("created_at"))
            if not created or created < cutoff:
                continue
            body = c.get("body") or ""
            rows.append({
                "id": c["html_url"],
                "source_type": "github_review",
                "surface": "github",
                "cwd": None,
                "cwd_raw": None,
                "repo": repo,
                "space": None,
                "title": f"review on PR #{c.get('pull_request_url','').rsplit('/',1)[-1]}",
                "started_at": created,
                "ended_at": created,
                "duration_s": 0,
                "first_user_message": (c.get("diff_hunk") or "")[:2000],
                "last_user_message": None,
                "user_message_count": 0,
                "assistant_turn_count": 0,
                "tool_call_sequence": "",
                "files_touched": [c["path"]] if c.get("path") else [],
                "commit_shas": [],
                "branch_names": [],
                "body": body[:10000],
                "diff_hunk": (c.get("diff_hunk") or "")[:2000],
                "labels": [],
                "url": c["html_url"],
                "privacy_tag": "work",
                "privacy_reason": None,
                "size_bytes": len(body),
                "source_paths": [c["html_url"]],
                "work_thread_id": c.get("pull_request_url") or c["html_url"],
                "harvested_at": datetime.now(timezone.utc),
            })
    return rows


# ---------------------------------------------------------------------------
# Stage A.5 — chat work-thread grouping


def group_chat_threads(chat_rows: list[dict]) -> list[dict]:
    """Collapse Claude Code sessions by (canonical cwd, 24h rolling window)."""
    buckets: dict[str, list[dict]] = defaultdict(list)
    for r in chat_rows:
        key = r.get("cwd") or f"__nocwd__:{r['id']}"
        buckets[key].append(r)

    threads = []
    for cwd, rows in buckets.items():
        rows.sort(key=lambda x: x["started_at"] or datetime.min.replace(tzinfo=timezone.utc))
        cluster: list[dict] = []
        for r in rows:
            if not cluster:
                cluster.append(r)
                continue
            prev_end = cluster[-1]["ended_at"] or cluster[-1]["started_at"]
            if r["started_at"] and prev_end and (r["started_at"] - prev_end) <= timedelta(hours=24):
                cluster.append(r)
            else:
                threads.append(_merge_cluster(cluster, cwd))
                cluster = [r]
        if cluster:
            threads.append(_merge_cluster(cluster, cwd))
    return threads


def _merge_cluster(cluster: list[dict], cwd: str) -> dict:
    if len(cluster) == 1:
        c = dict(cluster[0])
        c["work_thread_id"] = c["id"]
        return c

    first = cluster[0]
    last = cluster[-1]
    tid = f"thread:{cwd}:{first['started_at'].isoformat()}"
    merged_tools: Counter = Counter()
    for r in cluster:
        for pair in (r["tool_call_sequence"] or "").split(","):
            if "x" in pair:
                name, n = pair.rsplit("x", 1)
                try:
                    merged_tools[name] += int(n)
                except ValueError:
                    pass
    files = sorted({f for r in cluster for f in (r["files_touched"] or [])})[:80]
    paths = [p for r in cluster for p in (r["source_paths"] or [])]
    return {
        **first,
        "id": tid,
        "work_thread_id": tid,
        "ended_at": last["ended_at"],
        "duration_s": int(sum(r["duration_s"] or 0 for r in cluster)),
        "last_user_message": last["last_user_message"],
        "user_message_count": sum(r["user_message_count"] for r in cluster),
        "assistant_turn_count": sum(r["assistant_turn_count"] for r in cluster),
        "tool_call_sequence": compact_tool_sequence(merged_tools),
        "files_touched": files,
        "commit_shas": sorted({s for r in cluster for s in (r["commit_shas"] or [])})[:20],
        "branch_names": sorted({b for r in cluster for b in (r["branch_names"] or [])})[:10],
        "size_bytes": sum(r["size_bytes"] or 0 for r in cluster),
        "source_paths": paths,
        "title": first["title"],
        "harvested_at": datetime.now(timezone.utc),
    }


# ---------------------------------------------------------------------------
# Parquet I/O


SCHEMA = pa.schema([
    ("id", pa.string()),
    ("source_type", pa.string()),
    ("surface", pa.string()),
    ("cwd", pa.string()),
    ("cwd_raw", pa.string()),
    ("repo", pa.string()),
    ("space", pa.string()),
    ("title", pa.string()),
    ("started_at", pa.timestamp("us")),
    ("ended_at", pa.timestamp("us")),
    ("duration_s", pa.int64()),
    ("first_user_message", pa.string()),
    ("last_user_message", pa.string()),
    ("user_message_count", pa.int64()),
    ("assistant_turn_count", pa.int64()),
    ("tool_call_sequence", pa.string()),
    ("files_touched", pa.list_(pa.string())),
    ("commit_shas", pa.list_(pa.string())),
    ("branch_names", pa.list_(pa.string())),
    ("body", pa.string()),
    ("diff_hunk", pa.string()),
    ("labels", pa.list_(pa.string())),
    ("url", pa.string()),
    ("privacy_tag", pa.string()),
    ("privacy_reason", pa.string()),
    ("size_bytes", pa.int64()),
    ("source_paths", pa.list_(pa.string())),
    ("work_thread_id", pa.string()),
    ("harvested_at", pa.timestamp("us")),
])


_TIMESTAMP_FIELDS = {"started_at", "ended_at", "harvested_at"}


# ---------------------------------------------------------------------------
# Stage A1.5 — per-thread full session content as markdown
#
# Writes each in-scope work-thread's conversational content to
# ``knowledge-vault/reference/sessions/YYYY-Www/<slug>.md`` so the
# ``search-vault`` skill can Grep + Read substance, not just the
# one-line pointers in ``daily/``. Gitignored.
#
# Privacy: rows with ``privacy_tag == "excluded"`` are never written.
# Content filtering: user/assistant text in full; tool calls as one-liners;
# tool results / system reminders / synthetic tool_result-only user turns
# skipped. Always overwrites — disk is cheap, output is gitignored.


_SLUG_RE = re.compile(r"[^a-z0-9]+")
_TOOL_INPUT_PREVIEW = 240
_BODY_TURN_LIMIT = 4000     # per turn, chars
_TOTAL_FILE_LIMIT = 200_000  # per file, chars; hard cap to keep files readable


def _slugify(s: str, limit: int = 40) -> str:
    s = _SLUG_RE.sub("-", (s or "").lower()).strip("-")
    return s[:limit] or "untitled"


def _thread_slug(thread: dict) -> str:
    """Build a sortable, scannable, unique filename stem for a work-thread."""
    started = thread.get("started_at")
    if isinstance(started, datetime):
        date_part = started.strftime("%Y-%m-%d")
    else:
        date_part = "0000-00-00"
    cwd = thread.get("cwd") or ""
    cwd_tail = cwd.rsplit("/", 1)[-1] if cwd else "session"
    cwd_slug = _slugify(cwd_tail, limit=30)
    tid = (thread.get("work_thread_id") or thread.get("id") or "")
    # Short stable suffix from the thread id so multiple threads in the same
    # cwd on the same day don't collide.
    suffix = _slugify(tid.rsplit(":", 1)[-1], limit=12) or "x"
    return f"{date_part}--{cwd_slug}--{suffix}"


def _render_event(ev: dict) -> str | None:
    """Render one JSONL event as a markdown chunk, or None to skip."""
    msg = ev.get("message") or {}
    if not isinstance(msg, dict):
        return None
    if ev.get("isMeta") is True:
        return None

    etype = ev.get("type")
    role = msg.get("role")
    content = msg.get("content")

    # User turns — skip the synthetic tool_result-only ones.
    if etype == "user" or role == "user":
        text = extract_text(content).strip()
        if not text or text.startswith("<tool_use:"):
            return None
        # Drop user messages that are pure tool_result blocks (no text content).
        if isinstance(content, list):
            has_text = any(
                isinstance(b, dict) and b.get("type") == "text" and (b.get("text") or "").strip()
                for b in content
            )
            if not has_text:
                return None
        return f"## User\n\n{text[:_BODY_TURN_LIMIT]}\n"

    # Assistant turns — text blocks plus one-liner tool-call summaries.
    if etype == "assistant" or role == "assistant":
        parts: list[str] = []
        text_parts: list[str] = []
        tool_lines: list[str] = []
        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                bt = block.get("type")
                if bt == "text":
                    t = (block.get("text") or "").strip()
                    if t:
                        text_parts.append(t)
                elif bt == "tool_use":
                    name = block.get("name", "?")
                    inp = block.get("input") or {}
                    preview = ""
                    # Heuristics for the most-used tools.
                    if isinstance(inp, dict):
                        for key in ("file_path", "path", "pattern", "command", "url",
                                    "old_string", "query", "prompt", "description"):
                            if key in inp and isinstance(inp[key], str):
                                preview = f"{key}={inp[key][:_TOOL_INPUT_PREVIEW]}"
                                break
                    tool_lines.append(f"- {name}: {preview}".rstrip(": ").rstrip())
        elif isinstance(content, str):
            text_parts.append(content.strip())

        if text_parts:
            joined = "\n\n".join(text_parts)[:_BODY_TURN_LIMIT]
            parts.append(f"## Assistant\n\n{joined}")
        if tool_lines:
            parts.append("### Tools\n\n" + "\n".join(tool_lines[:20]))
        if not parts:
            return None
        return "\n\n".join(parts) + "\n"

    # System / summary events — skip; metadata is in the parquet.
    return None


def _read_session_events(jsonl_path: Path) -> Iterable[dict]:
    try:
        with jsonl_path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    except OSError:
        return


def write_session_reference(thread: dict, reference_root: Path) -> Path | None:
    """Render one work-thread's full content to a markdown file.

    Returns the written path, or None if skipped (excluded, no content,
    or no source paths).
    """
    if thread.get("privacy_tag") == "excluded":
        return None
    paths = [Path(p) for p in (thread.get("source_paths") or []) if p]
    if not paths:
        return None
    started = thread.get("started_at")
    if not isinstance(started, datetime):
        return None
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    ended = thread.get("ended_at") or started
    if not isinstance(ended, datetime):
        ended = started
    if ended.tzinfo is None:
        ended = ended.replace(tzinfo=timezone.utc)

    # Bucket by ended_at so the file lives in the week of last activity,
    # matching how daily/ rollups bucket. Sessions that span week
    # boundaries (compact + continue) land in the week they actually
    # finished in, not the week they started.
    week = iso_week_label(ended)
    out_dir = reference_root / week
    out_dir.mkdir(parents=True, exist_ok=True)
    slug_file = f"{_thread_slug(thread)}.md"
    out_path = out_dir / slug_file

    # Clean up stale copies in past weeks - as a session grows across
    # weeks (compact + continue), its file needs to migrate forward.
    # Slug is unique per thread, so any same-named file in another week
    # folder is this session's previous home and should be removed.
    for weeks_back in range(1, RECENCY_WEEKS + 1):
        other_dt = ended - timedelta(weeks=weeks_back)
        other_week = iso_week_label(other_dt)
        if other_week == week:
            continue
        stale = reference_root / other_week / slug_file
        if stale.exists():
            stale.unlink()

    # Header / frontmatter — minimal, since these aren't curated notes.
    title = (thread.get("title") or "untitled").strip().splitlines()[0][:120]
    ended = thread.get("ended_at")
    if isinstance(ended, datetime) and ended.tzinfo is None:
        ended = ended.replace(tzinfo=timezone.utc)
    duration_min = round((thread.get("duration_s") or 0) / 60)
    files = thread.get("files_touched") or []
    surface = thread.get("surface") or ""
    cwd = thread.get("cwd") or ""

    lines: list[str] = [
        "---",
        f"title: {json.dumps(title)}",
        f"thread_id: {json.dumps(thread.get('work_thread_id') or thread.get('id') or '')}",
        f"started_at: {started.isoformat()}",
        f"ended_at: {ended.isoformat() if isinstance(ended, datetime) else ''}",
        f"duration_min: {duration_min}",
        f"cwd: {json.dumps(cwd)}",
        f"surface: {json.dumps(surface)}",
        f"privacy_tag: {thread.get('privacy_tag') or ''}",
        f"source_paths: {json.dumps([str(p) for p in paths])}",
        f"files_touched: {json.dumps(files[:30])}",
        "---",
        "",
        f"# {title}",
        "",
        f"*Auto-generated by `harvest/scripts/harvest.py` Stage A1.5. "
        f"Gitignored. Curated notes live elsewhere — see "
        f"[`knowledge-vault/CLAUDE.md`](../../CLAUDE.md).*",
        "",
    ]

    # Walk events across all constituent sessions, oldest first.
    rendered_chunks: list[str] = []
    chars = sum(len(s) for s in lines)
    truncated = False
    for path in paths:
        rendered_chunks.append(f"\n---\n\n*From `{path.name}`*\n")
        for ev in _read_session_events(path):
            chunk = _render_event(ev)
            if not chunk:
                continue
            if chars + len(chunk) > _TOTAL_FILE_LIMIT:
                truncated = True
                break
            rendered_chunks.append(chunk)
            chars += len(chunk)
        if truncated:
            rendered_chunks.append(
                "\n*[truncated — file exceeded 200k chars; full source in "
                "`source_paths` frontmatter]*\n"
            )
            break

    body = "\n".join(lines) + "\n".join(rendered_chunks)
    out_path.write_text(body, encoding="utf-8")
    return out_path


def write_all_session_references(threads: list[dict], reference_root: Path) -> tuple[int, int]:
    """Write all in-scope (non-excluded) work-threads. Returns (written, skipped)."""
    written = 0
    skipped = 0
    for t in threads:
        if write_session_reference(t, reference_root) is None:
            skipped += 1
        else:
            written += 1
    return written, skipped


def _naive_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def rows_to_table(rows: list[dict]) -> pa.Table:
    if not rows:
        return SCHEMA.empty_table()
    cols: dict[str, list] = {name: [] for name in SCHEMA.names}
    for r in rows:
        for name in SCHEMA.names:
            v = r.get(name)
            if name in _TIMESTAMP_FIELDS and isinstance(v, datetime):
                v = _naive_utc(v)
            cols[name].append(v)
    arrays = []
    for name in SCHEMA.names:
        field = SCHEMA.field(name)
        arrays.append(pa.array(cols[name], type=field.type))
    return pa.Table.from_arrays(arrays, schema=SCHEMA)


def load_existing_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        tbl = pq.read_table(path, columns=["id"])
        return set(tbl.column("id").to_pylist())
    except Exception as e:  # noqa: BLE001
        print(f"[warn] could not read {path}: {e}", file=sys.stderr)
        return set()


# ---------------------------------------------------------------------------
# Weekly rollups


def emit_rollups(rows: list[dict], daily_dir: Path) -> list[Path]:
    daily_dir.mkdir(parents=True, exist_ok=True)
    by_week: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        bucket_ts = r.get("ended_at") or r.get("started_at")
        if not bucket_ts:
            continue
        if r["privacy_tag"] == "excluded":
            continue
        # Drop title-only Confluence stubs from rollups — they're navigation
        # pages with no rolled-up signal. The themes review (Phase 3) treats
        # them similarly. Threshold mirrors the body_is_excerpt/body<60 rule.
        if r["source_type"] == "confluence_page":
            body_len = len((r.get("body") or "").strip())
            if body_len < 60:
                continue
        label = iso_week_label(bucket_ts)
        by_week[label].append(r)

    written = []
    for label, items in sorted(by_week.items()):
        items.sort(key=lambda x: x.get("ended_at") or x["started_at"])
        fp = daily_dir / f"{label}-activity.md"
        lines = [f"# Activity — {label}", ""]

        def _section(heading: str, types: set[str]):
            chunk = [r for r in items if r["source_type"] in types]
            if not chunk:
                return
            lines.append(f"## {heading}")
            lines.append("")
            for r in chunk:
                ts = r.get("ended_at") or r["started_at"]
                date = ts.strftime("%Y-%m-%d")
                ident = _short_ident(r)
                title = (r["title"] or "").replace("\n", " ").strip()[:120]
                tag = f" _({r['privacy_tag']})_" if r["privacy_tag"] != "work" else ""
                lines.append(f"- {date} · {ident} · {title}{tag}")
            lines.append("")

        _section("Chat threads", {"chat"})
        _section("Confluence pages", {"confluence_page"})
        _section("Local markdown", {"local_md"})
        _section("PRs & reviews", {"github_pr", "github_review"})
        fp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        written.append(fp)
    return written


def _short_ident(r: dict) -> str:
    st = r["source_type"]
    if st == "chat":
        cwd = r.get("cwd") or ""
        short = cwd.rsplit("/", 1)[-1] if cwd else r["surface"]
        return f"chat `{short}`"
    if st == "local_md":
        parts = (r.get("source_paths") or [""])[0].replace("\\", "/").split("/")
        return f"md `{'/'.join(parts[-3:])}`"
    if st == "confluence_page":
        return f"conf [{r.get('space','?')}]"
    if st == "github_pr":
        url = r.get("url") or ""
        return f"PR {url.split('/')[-3]+'#'+url.split('/')[-1] if url else ''}".strip()
    if st == "github_review":
        url = r.get("url") or ""
        try:
            parts = url.split("/")
            return f"review {parts[-3]}#{parts[-1].split('#')[0]}"
        except Exception:  # noqa: BLE001
            return "review"
    return st


# ---------------------------------------------------------------------------
# Main


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weeks", type=int, default=RECENCY_WEEKS,
                    help="recency cutoff in weeks (default 12)")
    ap.add_argument("--skip-chat", action="store_true")
    ap.add_argument("--skip-confluence", action="store_true")
    ap.add_argument("--skip-github", action="store_true")
    ap.add_argument("--skip-local-md", action="store_true")
    ap.add_argument("--no-rollups", action="store_true")
    ap.add_argument("--no-session-refs", action="store_true",
                    help="skip Stage A1.5 — per-thread session content to "
                         "reference/sessions/")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    HARVEST.mkdir(parents=True, exist_ok=True)
    (HARVEST / "archive").mkdir(exist_ok=True)
    cutoff = datetime.now(timezone.utc) - timedelta(weeks=args.weeks)

    sources_path = HARVEST / "sources.parquet"
    archive_path = HARVEST / "archive" / "sources_pre_cutoff.parquet"
    existing_ids = load_existing_ids(sources_path)

    all_rows: list[dict] = []
    archive_rows: list[dict] = []

    # ----- A1: chat -----
    chat_in_scope: list[dict] = []
    if not args.skip_chat:
        seen: set[str] = set()
        for surface, path, key in walk_chat_jsonls():
            if key in seen:
                continue
            seen.add(key)
            row = parse_chat_session(surface, path, key)
            if not row:
                continue
            if row["ended_at"] and row["ended_at"] < cutoff:
                archive_rows.append(row)
                continue
            chat_in_scope.append(row)
        print(f"[A1] chat in-scope={len(chat_in_scope)} archived={len(archive_rows)}")

    # ----- A.5: group chat -----
    if chat_in_scope:
        grouped = group_chat_threads(chat_in_scope)
        print(f"[A.5] {len(chat_in_scope)} sessions -> {len(grouped)} work threads")
        all_rows.extend(grouped)

    # ----- A2: confluence -----
    if not args.skip_confluence:
        conf_rows = load_confluence(CONFLUENCE_RAW)
        conf_rows = [r for r in conf_rows if r["ended_at"] and r["ended_at"] >= cutoff]
        print(f"[A2] confluence pages in-scope={len(conf_rows)}")
        all_rows.extend(conf_rows)

    # ----- A4: local markdown one-off -----
    if not args.skip_local_md:
        md_rows = fetch_local_md(LOCAL_MD_ROOTS)
        print(f"[A4] local markdown files in-scope={len(md_rows)}")
        all_rows.extend(md_rows)

    # ----- A3: github -----
    if not args.skip_github:
        pr_rows = fetch_github_prs(cutoff)
        print(f"[A3] github PRs in-scope={len(pr_rows)}")
        all_rows.extend(pr_rows)
        review_rows = fetch_github_reviews(pr_rows, cutoff)
        print(f"[A3] github review comments in-scope={len(review_rows)}")
        all_rows.extend(review_rows)

    # ----- privacy gate for downstream filter (kept in parquet but flagged) -----
    excluded = [r for r in all_rows if r["privacy_tag"] == "excluded"]
    if excluded:
        print(f"[privacy] {len(excluded)} rows tagged excluded (reasons: "
              f"{Counter(r['privacy_reason'] for r in excluded).most_common(5)})")

    # ----- count new vs updates against existing parquet -----
    new_count = sum(1 for r in all_rows if r["id"] not in existing_ids)
    update_count = len(all_rows) - new_count
    print(f"[upsert] new={new_count} updates={update_count}")

    if args.dry_run:
        print("[dry-run] skipping writes")
        return 0

    # ----- write (upsert by id so long-running sessions get their
    # ended_at and content refreshed in the parquet — otherwise daily
    # rollups stay frozen at first-harvest state) -----
    if all_rows or not sources_path.exists():
        if sources_path.exists():
            existing = pq.read_table(sources_path).to_pylist()
            batch_ids = {r["id"] for r in all_rows}
            kept = [r for r in existing if r["id"] not in batch_ids]
            pq.write_table(rows_to_table(kept + all_rows), sources_path)
        else:
            pq.write_table(rows_to_table(all_rows), sources_path)
    print(f"[write] {sources_path} total_rows={pq.read_metadata(sources_path).num_rows}")

    # chat-only work_threads parquet (full rewrite, cheap)
    chat_rows = [r for r in pq.read_table(sources_path).to_pylist()
                 if r["source_type"] == "chat"]
    wt_path = HARVEST / "work_threads.parquet"
    pq.write_table(rows_to_table(chat_rows), wt_path)
    print(f"[write] {wt_path} rows={len(chat_rows)}")

    if archive_rows:
        if archive_path.exists():
            existing = pq.read_table(archive_path)
            combined = pa.concat_tables([existing, rows_to_table(archive_rows)])
            pq.write_table(combined, archive_path)
        else:
            pq.write_table(rows_to_table(archive_rows), archive_path)
        print(f"[write] {archive_path} appended={len(archive_rows)}")

    # ----- rollups -----
    if not args.no_rollups:
        all_current = pq.read_table(sources_path).to_pylist()
        for r in all_current:
            for k in ("started_at", "ended_at", "harvested_at"):
                v = r.get(k)
                if isinstance(v, datetime) and v.tzinfo is None:
                    r[k] = v.replace(tzinfo=timezone.utc)
        written = emit_rollups(all_current, DAILY)
        print(f"[rollups] wrote {len(written)} weekly files to {DAILY}")

    # ----- A1.5: per-thread full session content to reference/sessions/ -----
    # Gitignored. Privacy-filtered. Always overwrites in-scope threads —
    # output is mechanical, not curated.
    if not args.no_session_refs and chat_in_scope:
        # Reuse the grouped work-threads from A.5 above. We need datetime
        # objects, not parquet-roundtripped ones, so use ``grouped`` rather
        # than re-reading the parquet.
        threads_for_refs = [g for g in grouped if g.get("source_type") == "chat"]
        for t in threads_for_refs:
            for k in ("started_at", "ended_at"):
                v = t.get(k)
                if isinstance(v, datetime) and v.tzinfo is None:
                    t[k] = v.replace(tzinfo=timezone.utc)
        REF_SESSIONS.mkdir(parents=True, exist_ok=True)
        wrote, skipped_refs = write_all_session_references(threads_for_refs, REF_SESSIONS)
        print(f"[A1.5] session-refs wrote={wrote} skipped={skipped_refs} "
              f"(under {REF_SESSIONS})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
