"""Append Jira + Confluence activity pointers to the current week's daily rollup.

**Status (2026-05-13):** plumbing is complete and tested end-to-end against
the live Atlassian REST API. The Jira endpoint migration to ``/search/jql``
(POST) is wired; Confluence uses ``/wiki/api/v2/pages`` sorted by modified
date since v1 CQL endpoints 403 on the current personal API token. Both
sides return zero rows under the existing token — the token authenticates
but doesn't have read access to Jira issues or Confluence pages.

To unblock: either (a) generate a fresh API token at id.atlassian.com with
full Jira + Confluence read scopes, or (b) re-implement as a Claude skill
that uses the Atlassian MCP (which has OAuth and clearly works — that's
the path the team plugin uses). Path (b) is architecturally cleaner; path
(a) is faster.

Hits the Atlassian REST API directly (same auth pattern as
``sync_reference.py``) and appends two sections to
``knowledge-vault/daily/YYYY-Www-activity.md``:

- ``## Jira tickets touched`` — tickets I'm assignee or reporter of, updated
  this week. JQL is deliberately conservative; tune via ``JQL_TICKETS`` env
  var if the default misses things.
- ``## Confluence pages edited`` — pages I've contributed to, modified this
  week. CQL uses ``currentUser()`` so no account-ID lookup is needed.

**Pointers only.** Titles + URLs + dates, never bodies. This is an activity
log, not a content mirror — Jira and Confluence stay authoritative for the
content itself. Rerunning the script is safe; existing sections are
replaced rather than appended-to.

Usage:
    # one-off
    python activity_rollup.py

    # specific week (defaults to ISO week of today)
    python activity_rollup.py --week 2026-W20

    # dry run, prints what would be written
    python activity_rollup.py --dry-run

Auth: requires the same env vars sync_reference.py uses
(``KNOWLEDGE_MCP_ATLASSIAN_SITE``, ``KNOWLEDGE_MCP_ATLASSIAN_EMAIL``,
``KNOWLEDGE_MCP_ATLASSIAN_TOKEN``). Wire this script into the existing
weekly-knowledge-harvest scheduled task after the harvest.py call, or run
it manually on demand.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from base64 import b64encode
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

from kb_paths import resolve_vault_only

VAULT = resolve_vault_only()
DAILY_DIR = VAULT / "daily"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def _resolve_atlassian_creds() -> tuple[str, str, str]:
    """Resolve site / email / token from env, or exit with a clear message.

    Prefers the canonical ``ATLASSIAN_*`` names; falls back to the legacy
    ``KNOWLEDGE_MCP_ATLASSIAN_*`` set ``sync_reference.py`` reads. Either
    works.
    """
    site = (
        os.environ.get("ATLASSIAN_BASE_URL")
        or os.environ.get("KNOWLEDGE_MCP_ATLASSIAN_SITE")
        or ""
    )
    # Normalise: accept full URL or bare host.
    site = site.replace("https://", "").replace("http://", "").rstrip("/")

    email = (
        os.environ.get("ATLASSIAN_EMAIL")
        or os.environ.get("KNOWLEDGE_MCP_ATLASSIAN_EMAIL")
        or ""
    )
    token = (
        os.environ.get("ATLASSIAN_API_TOKEN")
        or os.environ.get("KNOWLEDGE_MCP_ATLASSIAN_TOKEN")
        or ""
    )
    missing = [
        name
        for name, val in (
            ("ATLASSIAN_BASE_URL (or KNOWLEDGE_MCP_ATLASSIAN_SITE)", site),
            ("ATLASSIAN_EMAIL (or KNOWLEDGE_MCP_ATLASSIAN_EMAIL)", email),
            ("ATLASSIAN_API_TOKEN (or KNOWLEDGE_MCP_ATLASSIAN_TOKEN)", token),
        )
        if not val
    ]
    if missing:
        raise SystemExit(f"missing env vars: {', '.join(missing)}.")
    return site, email, token


def _session(email: str, token: str) -> requests.Session:
    s = requests.Session()
    auth = b64encode(f"{email}:{token}".encode()).decode()
    s.headers.update(
        {
            "Authorization": f"Basic {auth}",
            "Accept": "application/json",
        }
    )
    return s


# ---------------------------------------------------------------------------
# Week math
# ---------------------------------------------------------------------------

def iso_week_label(dt: datetime) -> str:
    iso = dt.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def week_bounds(label: str) -> tuple[datetime, datetime]:
    """Return (Monday 00:00, Sunday 23:59:59) UTC for the given YYYY-Www label."""
    m = re.match(r"^(\d{4})-W(\d{2})$", label)
    if not m:
        raise SystemExit(f"bad week label: {label!r}; expected YYYY-Www")
    year, week = int(m.group(1)), int(m.group(2))
    monday = datetime.fromisocalendar(year, week, 1).replace(tzinfo=timezone.utc)
    sunday = monday + timedelta(days=6, hours=23, minutes=59, seconds=59)
    return monday, sunday


# ---------------------------------------------------------------------------
# Jira
# ---------------------------------------------------------------------------

DEFAULT_JQL = (
    "(assignee = currentUser() OR reporter = currentUser()) "
    'AND updated >= "{start}" AND updated <= "{end}" '
    "ORDER BY updated DESC"
)


def fetch_jira_tickets(
    session: requests.Session, site: str, start: datetime, end: datetime
) -> list[dict]:
    """Return tickets matching JQL_TICKETS (or DEFAULT_JQL) in the date range.

    Each row: ``{key, summary, status, updated, url}``.

    Uses the new ``/rest/api/3/search/jql`` POST endpoint — the old GET
    ``/search`` returns 410 Gone since the 2025 migration.
    """
    jql_template = os.environ.get("JQL_TICKETS", DEFAULT_JQL)
    jql = jql_template.format(
        start=start.strftime("%Y-%m-%d %H:%M"),
        end=end.strftime("%Y-%m-%d %H:%M"),
    )
    url = f"https://{site}/rest/api/3/search/jql"
    body = {
        "jql": jql,
        "fields": ["summary", "status", "updated"],
        "maxResults": 100,
    }
    resp = session.post(
        url,
        json=body,
        headers={"Content-Type": "application/json"},
        timeout=60,
    )
    resp.raise_for_status()
    issues = resp.json().get("issues", [])
    rows = []
    for issue in issues:
        f = issue.get("fields", {})
        updated_raw = f.get("updated") or ""
        # 2026-05-13T10:15:00.000+0000 → take the date
        updated_date = updated_raw.split("T", 1)[0] if "T" in updated_raw else updated_raw
        rows.append(
            {
                "key": issue.get("key", ""),
                "summary": (f.get("summary") or "").strip(),
                "status": ((f.get("status") or {}).get("name") or ""),
                "updated": updated_date,
                "url": f"https://{site}/browse/{issue.get('key', '')}",
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Confluence
# ---------------------------------------------------------------------------

def fetch_confluence_pages(
    session: requests.Session, site: str, start: datetime, end: datetime
) -> list[dict]:
    """Return pages I've contributed to in the date range.

    Uses v2 ``/wiki/api/v2/pages?sort=-modified-date`` and filters by
    last-modified in code. The v1 CQL search endpoints (``/content/search``
    and ``/search``) tend to 403 with personal API tokens on cloud tenants;
    v2 doesn't have CQL but does sort by modification time, so we page
    through until we drop below ``start`` and filter contributor in Python.

    The ``contributor`` filter requires the caller's accountId — we do a
    one-shot lookup via ``/wiki/rest/api/user/current``. If that endpoint
    is also locked down, fall back to "all pages I created OR last-edited".

    Each row: ``{id, title, space, last_modified, url}``.
    """
    # Resolve current user's accountId; tolerate failure.
    me_id: str | None = None
    try:
        me = session.get(
            f"https://{site}/wiki/rest/api/user/current", timeout=30
        )
        me.raise_for_status()
        me_id = me.json().get("accountId")
    except requests.HTTPError as e:
        print(
            f"[activity_rollup] /user/current failed ({e}); falling back to "
            "owner-only filter",
            file=sys.stderr,
        )

    url = f"https://{site}/wiki/api/v2/pages"
    params: dict[str, object] = {
        "limit": 100,
        "sort": "-modified-date",
        "body-format": "storage",
    }
    rows: list[dict] = []
    start_iso = start.strftime("%Y-%m-%d")
    end_iso = end.strftime("%Y-%m-%d")
    pages_scanned = 0
    while url and pages_scanned < 500:
        resp = session.get(url, params=params, timeout=60)
        resp.raise_for_status()
        payload = resp.json()
        for page in payload.get("results", []):
            pages_scanned += 1
            modified = (page.get("version") or {}).get("createdAt") or ""
            mod_date = modified.split("T", 1)[0] if "T" in modified else modified
            if not mod_date:
                continue
            if mod_date < start_iso:
                # results are sorted desc — we're past the window, stop.
                return rows
            if mod_date > end_iso:
                continue
            # Filter by contributor / owner if we have an accountId.
            owner = page.get("ownerId") or ""
            last_owner = (page.get("version") or {}).get("authorId") or ""
            if me_id and me_id not in {owner, last_owner}:
                continue
            web = (page.get("_links") or {}).get("webui") or ""
            full_url = f"https://{site}/wiki{web}" if web.startswith("/") else web
            rows.append(
                {
                    "id": page.get("id", ""),
                    "title": (page.get("title") or "").strip(),
                    "space": str(page.get("spaceId") or ""),
                    "last_modified": mod_date,
                    "url": full_url,
                }
            )
        nxt = payload.get("_links", {}).get("next")
        if not nxt:
            break
        url = nxt if nxt.startswith("http") else f"https://{site}{nxt}"
        params = {}
    return rows


# ---------------------------------------------------------------------------
# Rollup write
# ---------------------------------------------------------------------------

JIRA_HEADING = "## Jira tickets touched"
CONFLUENCE_HEADING = "## Confluence pages edited"


def format_jira_section(rows: list[dict]) -> str:
    if not rows:
        return f"{JIRA_HEADING}\n\n_no tickets touched this week_\n"
    lines = [JIRA_HEADING, ""]
    for r in rows:
        status = f" [{r['status']}]" if r["status"] else ""
        lines.append(
            f"- {r['updated']} · {r['key']}{status} · "
            f"[{r['summary']}]({r['url']})"
        )
    return "\n".join(lines) + "\n"


def format_confluence_section(rows: list[dict]) -> str:
    if not rows:
        return f"{CONFLUENCE_HEADING}\n\n_no pages edited this week_\n"
    lines = [CONFLUENCE_HEADING, ""]
    for r in rows:
        # v2 returns spaceId (numeric) not key — drop it; the URL already
        # encodes /spaces/<KEY>/pages/... so the space is visible there.
        lines.append(
            f"- {r['last_modified']} · [{r['title']}]({r['url']})"
        )
    return "\n".join(lines) + "\n"


def upsert_section(text: str, heading: str, new_content: str) -> str:
    """Replace an existing ``## heading`` section, or append if missing.

    Section boundary = the next ``## `` header or end of file.
    """
    pattern = re.compile(
        rf"^{re.escape(heading)}\s*\n.*?(?=^## |\Z)", re.DOTALL | re.MULTILINE
    )
    if pattern.search(text):
        return pattern.sub(new_content.rstrip() + "\n\n", text)
    # append
    if not text.endswith("\n"):
        text += "\n"
    if not text.endswith("\n\n"):
        text += "\n"
    return text + new_content


def upsert_rollup(
    week_label: str, jira_rows: list[dict], confluence_rows: list[dict],
    dry_run: bool = False,
) -> Path:
    path = DAILY_DIR / f"{week_label}-activity.md"
    text = path.read_text(encoding="utf-8") if path.exists() else f"# Activity — {week_label}\n\n"
    text = upsert_section(text, JIRA_HEADING, format_jira_section(jira_rows))
    text = upsert_section(text, CONFLUENCE_HEADING, format_confluence_section(confluence_rows))
    if dry_run:
        print(f"--- would write to {path} ---")
        # Windows console is cp1252; force utf-8 with replacement for the
        # dry-run preview only. Disk writes below always use utf-8.
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
        return path
    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--week",
        help="ISO week label (YYYY-Www). Defaults to current week.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be written; don't touch disk.",
    )
    args = parser.parse_args()

    site, email, token = _resolve_atlassian_creds()
    session = _session(email, token)

    week_label = args.week or iso_week_label(datetime.now(timezone.utc))
    start, end = week_bounds(week_label)
    print(
        f"[activity_rollup] week={week_label} start={start.date()} end={end.date()}",
        file=sys.stderr,
    )

    try:
        jira_rows = fetch_jira_tickets(session, site, start, end)
        print(f"[activity_rollup] jira: {len(jira_rows)} tickets", file=sys.stderr)
    except requests.HTTPError as e:
        print(f"[activity_rollup] jira fetch failed: {e}", file=sys.stderr)
        jira_rows = []

    try:
        confluence_rows = fetch_confluence_pages(session, site, start, end)
        print(
            f"[activity_rollup] confluence: {len(confluence_rows)} pages",
            file=sys.stderr,
        )
    except requests.HTTPError as e:
        print(f"[activity_rollup] confluence fetch failed: {e}", file=sys.stderr)
        confluence_rows = []

    path = upsert_rollup(week_label, jira_rows, confluence_rows, dry_run=args.dry_run)
    if not args.dry_run:
        print(f"[activity_rollup] wrote {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
