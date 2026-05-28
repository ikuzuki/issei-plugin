"""Sync Confluence CA space + selected GitHub repos into the vault reference corpus.

Mirrors external source material (Confluence pages, GitHub docs and code) into
``<vault>/reference/`` as markdown files with YAML frontmatter. The knowledge-mcp
file watcher picks the files up and chunks them for hybrid retrieval.

Usage:
    python -m scripts.sync_reference --pilot
    python -m scripts.sync_reference --source github --org intech
    python -m scripts.sync_reference --dry-run

See ``knowledge-vault/projects/knowledge-reference-corpus-plan.md`` for context
and the docstring of each helper for the operational contract. All deviations
from the plan are commented inline.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import logging
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET

import frontmatter  # type: ignore[import-untyped]
import requests
from markdownify import markdownify as md_convert  # type: ignore[import-untyped]

logger = logging.getLogger("sync_reference")


def _resolve_vault_path() -> Path:
    """Resolve the vault path via the shared kb_paths helper."""
    from kb_paths import resolve_vault_only
    return resolve_vault_only()

# ---------------------------------------------------------------------------
# Constants

CA_SPACE_ID = "294917"
CA_SPACE_KEY = "CA"
PILOT_PAGE_LIMIT = 20
PILOT_REPO = "intech-enrich"
SKIP_REPOS = {"intech-data-science"}

CURVE_ORG = "curveanalytics"
PERSONAL_USER = "ikuzuki"
CURVE_GH_ACCOUNT = "Issei-curve"
PERSONAL_GH_ACCOUNT = "ikuzuki"

CODE_EXTS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".sql",
    ".sh", ".ps1", ".yaml", ".yml", ".toml", ".tf", ".hcl",
}
CODE_BASENAMES = {"Dockerfile", "Makefile"}
CODE_SUFFIX_MK = ".mk"

DOC_DIR_PREFIXES = ("docs/", "adr", "ADR")
SKIP_DIR_TOKENS = (
    "node_modules/", ".venv/", "dist/", "build/", "target/", ".next/",
    "__pycache__/",
)
SKIP_BASENAME_GLOBS = (
    ".env", "package-lock.json", "yarn.lock", "poetry.lock", "Pipfile.lock",
)
SKIP_EXTS = {
    ".lock", ".pyc", ".so", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
    ".pdf", ".zip", ".tar", ".gz", ".bin", ".exe", ".dll", ".class", ".jar",
    ".woff", ".woff2", ".ttf", ".eot", ".ipynb",
}
MAX_FILE_BYTES = 200 * 1024

DRAWIO_SUFFIXES = (".drawio", ".drawio.svg", ".drawio.png")
DRAWIO_MEDIA_TYPE = "application/vnd.jgraph.mxfile"


# ---------------------------------------------------------------------------
# Small helpers

def now_iso() -> str:
    """Return current UTC timestamp in ISO-8601."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def slugify(title: str, page_id: str) -> str:
    """Generate a filename-safe slug for a Confluence page.

    Lower-case, replace non-alphanum runs with ``-``, strip edges, truncate to 80
    chars, append ``__<page_id>`` for collision safety.
    """
    base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    if not base:
        base = "untitled"
    base = base[:80]
    return f"{base}__{page_id}"


def _basename(path: str) -> str:
    return path.rsplit("/", 1)[-1]


def should_index_github_file(path: str, size: int | None) -> tuple[bool, str | None]:
    """Return ``(include, kind)`` where kind is ``doc``, ``code`` or ``None``.

    Filters by the path, basename, extension and size rules in the plan. Pure
    function so tests can exercise it without a network.
    """
    if size is not None and size > MAX_FILE_BYTES:
        return False, None

    lower = path.lower()
    # Skip anywhere a forbidden directory token appears.
    for token in SKIP_DIR_TOKENS:
        if token in lower or lower.startswith(token.rstrip("/") + "/"):
            return False, None

    base = _basename(path)
    base_lower = base.lower()

    # Env files (.env, .env.local, etc.) anywhere.
    if base_lower == ".env" or base_lower.startswith(".env."):
        return False, None
    if base_lower in {"package-lock.json", "yarn.lock", "poetry.lock", "pipfile.lock"}:
        return False, None
    if ".min." in base_lower:
        return False, None

    # Extensions to skip outright.
    dot = base_lower.rfind(".")
    ext = base_lower[dot:] if dot > 0 else ""
    if ext in SKIP_EXTS:
        return False, None

    # Docs classification.
    if ext == ".md":
        return True, "doc"
    if base_lower.startswith("readme") or base_lower.startswith("changelog"):
        return True, "doc"
    if lower.startswith("docs/") or "/docs/" in lower:
        return True, "doc"
    if re.match(r"^adr[^/]*/", lower) or "/adr" in lower:
        # ADR directories may be ``adrs/`` or similar.
        if "/adr" in lower or lower.startswith("adr"):
            return True, "doc"

    # Code classification.
    if ext in CODE_EXTS:
        return True, "code"
    if base in CODE_BASENAMES:
        return True, "code"
    if ext == CODE_SUFFIX_MK:
        return True, "code"

    return False, None


def github_filename(kind: str, path: str) -> str:
    """Flatten a repo-relative path into ``kind__seg__seg.ext.md``.

    The trailing ``.md`` is required so the knowledge-mcp watcher + reindexer
    pick the file up — they both filter `*.md` exclusively. Content bodies are
    already written as markdown (fenced blocks for code) so adding the suffix
    is purely a filter-matching concern.
    """
    flattened = path.replace("/", "__")
    return f"{kind}__{flattened}.md"


# ---------------------------------------------------------------------------
# drawio extraction

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(value: str) -> str:
    return html.unescape(_TAG_RE.sub("", value)).strip()


def extract_drawio_labels(xml_text: str) -> list[str]:
    """Extract human-readable labels from mxGraph XML.

    Walks ``mxCell@value``, ``UserObject@label`` and ``object@label``. Strips
    HTML tags and entities. Preserves order of appearance, drops blanks and
    exact duplicates.
    """
    labels: list[str] = []
    seen: set[str] = set()
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return labels

    for elem in root.iter():
        tag = elem.tag.rsplit("}", 1)[-1]
        attr = None
        if tag == "mxCell":
            attr = elem.get("value")
        elif tag in {"UserObject", "object"}:
            attr = elem.get("label")
        if not attr:
            continue
        text = _strip_html(attr)
        if not text or text in seen:
            continue
        seen.add(text)
        labels.append(text)
    return labels


def _decode_drawio_svg(svg_bytes: bytes) -> str | None:
    """Extract the embedded mxfile XML from a drawio SVG wrapper."""
    try:
        root = ET.fromstring(svg_bytes)
    except ET.ParseError:
        return None

    # ``content`` attribute on the root svg element (common form).
    content = root.get("content")
    if content:
        return content

    # Or a ``<content>`` child element.
    for child in root.iter():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "content" and child.text:
            return child.text
    return None


# ---------------------------------------------------------------------------
# Confluence

@dataclass
class ConfluenceClient:
    site: str
    email: str
    token: str
    session: requests.Session = field(default_factory=requests.Session)

    def __post_init__(self) -> None:
        self.session.auth = (self.email, self.token)
        self.session.headers.update({"Accept": "application/json"})

    def _base(self) -> str:
        return f"https://{self.site}"

    def _get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """GET with simple 429-aware backoff; up to 5 attempts."""
        attempt = 0
        backoff = 1.0
        while True:
            attempt += 1
            resp = self.session.get(url, params=params, timeout=60)
            if resp.status_code == 429 and attempt < 5:
                retry_after = resp.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else min(30.0, backoff * 2)
                logger.warning("confluence 429, sleeping %.1fs (attempt %d)", delay, attempt)
                time.sleep(delay)
                backoff *= 2
                continue
            resp.raise_for_status()
            return resp.json()

    def _get_bytes(self, url: str) -> bytes:
        resp = self.session.get(url, timeout=60)
        resp.raise_for_status()
        return resp.content

    def list_pages(self, space_id: str, limit: int = 100) -> Iterable[dict[str, Any]]:
        """Yield CA space pages in reverse-modified order. Honours ``_links.next``."""
        url = f"{self._base()}/wiki/api/v2/spaces/{space_id}/pages"
        params: dict[str, Any] = {"limit": limit, "sort": "-modified-date"}
        while url:
            payload = self._get(url, params=params)
            for page in payload.get("results", []):
                yield page
            nxt = payload.get("_links", {}).get("next")
            if not nxt:
                return
            # v2 returns a path like ``/wiki/api/v2/...`` — prefix with host.
            if nxt.startswith("http"):
                url = nxt
            else:
                url = f"{self._base()}{nxt}"
            params = None

    def get_page(self, page_id: str, body_format: str = "storage") -> dict[str, Any]:
        url = f"{self._base()}/wiki/api/v2/pages/{page_id}"
        return self._get(url, params={"body-format": body_format})

    def list_attachments(self, page_id: str) -> list[dict[str, Any]]:
        url = f"{self._base()}/wiki/rest/api/content/{page_id}/child/attachment"
        params = {"expand": "extensions.fileSize,metadata.mediaType"}
        payload = self._get(url, params=params)
        return payload.get("results", [])

    def page_url(self, page: dict[str, Any]) -> str:
        """Canonical web URL for a v2 page payload."""
        web = page.get("_links", {}).get("webui") or ""
        if web.startswith("http"):
            return web
        return f"{self._base()}/wiki{web}" if web else f"{self._base()}/wiki/spaces/{CA_SPACE_KEY}/pages/{page.get('id')}"


def _drawio_xml_from_attachment(
    attachment: dict[str, Any], raw: bytes
) -> str | None:
    """Return the raw mxGraph XML for a drawio attachment, if recoverable."""
    title = (attachment.get("title") or "").lower()
    if title.endswith(".drawio"):
        try:
            return raw.decode("utf-8", errors="replace")
        except UnicodeDecodeError:
            return None
    if title.endswith(".drawio.svg"):
        return _decode_drawio_svg(raw)
    # .drawio.png: PNG metadata parsing is skipped for the pilot per plan.
    return None


def render_confluence_page(
    client: ConfluenceClient, page: dict[str, Any]
) -> tuple[str, dict[str, Any], bool]:
    """Return ``(markdown_body, frontmatter_dict, has_diagrams)`` for one page."""
    page_id = str(page["id"])
    storage_html = (
        page.get("body", {}).get("storage", {}).get("value", "")
    )
    body_md = md_convert(storage_html, heading_style="ATX")

    has_diagrams = False
    try:
        attachments = client.list_attachments(page_id)
    except requests.HTTPError as exc:
        logger.warning("attachments fetch failed for page %s: %s", page_id, exc)
        attachments = []

    diagram_sections: list[str] = []
    for att in attachments:
        title = att.get("title") or ""
        media = (att.get("metadata") or {}).get("mediaType") or ""
        is_drawio = title.lower().endswith(DRAWIO_SUFFIXES) or media == DRAWIO_MEDIA_TYPE
        if not is_drawio:
            continue
        download = (att.get("_links") or {}).get("download")
        if not download:
            continue
        url = download if download.startswith("http") else f"{client._base()}/wiki{download}"
        try:
            raw = client._get_bytes(url)
        except requests.HTTPError as exc:
            logger.warning("drawio download failed %s: %s", title, exc)
            continue
        xml_text = _drawio_xml_from_attachment(att, raw)
        if not xml_text:
            continue
        labels = extract_drawio_labels(xml_text)
        if not labels:
            continue
        has_diagrams = True
        bullets = "\n".join(f"- {lbl}" for lbl in labels)
        diagram_sections.append(f"## Diagram: {title}\n\n{bullets}\n")

    if diagram_sections:
        body_md = body_md.rstrip() + "\n\n" + "\n".join(diagram_sections)

    fm = {
        "source": "confluence",
        "source_url": client.page_url(page),
        "title": page.get("title", ""),
        "synced_at": now_iso(),
        "last_updated_at": (
            (page.get("version") or {}).get("createdAt") or now_iso()
        ),
        "space": CA_SPACE_KEY,
        "page_id": str(page_id),
    }
    if has_diagrams:
        fm["has_diagrams"] = True
    return body_md, fm, has_diagrams


# ---------------------------------------------------------------------------
# GitHub via gh CLI

def gh_api(endpoint: str, *, paginate: bool = False) -> Any:
    """Call ``gh api`` and return decoded JSON. Raises on non-zero exit."""
    args = ["gh", "api"]
    if paginate:
        args.append("--paginate")
    args.append(endpoint)
    proc = subprocess.run(
        args, capture_output=True, text=True, check=False, encoding="utf-8"
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh api {endpoint} failed: {proc.stderr.strip()}")
    out = proc.stdout.strip()
    if not out:
        return None
    if paginate:
        # --paginate concatenates JSON arrays; the output might be multiple
        # arrays back-to-back. Join by attempting to parse line-by-line JSON
        # arrays, falling back to a single parse.
        # ``gh --paginate`` in practice concatenates into a single JSON array
        # for list endpoints. If that ever changes we'll see a JSONDecodeError
        # and can revisit.
        return json.loads(out)
    return json.loads(out)


def gh_current_account() -> str | None:
    """Return the currently active ``gh`` account, or ``None`` if unknown."""
    proc = subprocess.run(
        ["gh", "auth", "status"], capture_output=True, text=True, check=False,
        encoding="utf-8",
    )
    text = (proc.stdout or "") + (proc.stderr or "")
    match = re.search(r"active account: true\s*\n[^\n]*account ([^\s]+)", text, re.I)
    if match:
        return match.group(1)
    # Newer gh formats: ``Active account: true`` and ``- Logged in to github.com account <name>``
    match = re.search(r"Logged in to [^ ]+ account ([^ ]+) \(.*active", text)
    if match:
        return match.group(1)
    match = re.search(r"Logged in to [^ ]+ account ([^ ]+)", text)
    return match.group(1) if match else None


def gh_switch(account: str) -> None:
    """Switch the active gh account. Logs + proceeds on error to keep runs resilient."""
    proc = subprocess.run(
        ["gh", "auth", "switch", "-u", account],
        capture_output=True, text=True, check=False, encoding="utf-8",
    )
    if proc.returncode != 0:
        logger.warning("gh auth switch -u %s failed: %s", account, proc.stderr.strip())


def github_subtree_for(repo_name: str, org: str) -> str:
    """Return ``curve``, ``intech`` or ``personal`` for a given repo."""
    if org == "personal":
        return "personal"
    return "intech" if repo_name.startswith("intech-") else "curve"


def repo_meta_markdown(repo: dict[str, Any], readme_excerpt: str, tree_lines: list[str]) -> str:
    """Synthesise a ``_meta.md`` body."""
    lines = [
        f"# {repo.get('name')}",
        "",
        repo.get("description") or "_no description_",
        "",
        f"- full_name: {repo.get('full_name')}",
        f"- primary_language: {repo.get('language')}",
        f"- pushed_at: {repo.get('pushed_at')}",
        "",
        "## Top-level tree",
        "",
    ]
    lines.extend(f"- {entry}" for entry in tree_lines)
    lines.extend(["", "## README excerpt", "", readme_excerpt or "_no README_"])
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# File IO

def write_markdown(path: Path, body: str, fm: dict[str, Any], dry_run: bool) -> None:
    """Write a file with YAML frontmatter, creating parent dirs as needed."""
    if dry_run:
        logger.info("dry-run: would write %s", path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    post = frontmatter.Post(body, **fm)
    text = frontmatter.dumps(post)
    path.write_text(text, encoding="utf-8")


def read_frontmatter(path: Path) -> dict[str, Any]:
    """Return the frontmatter dict of an existing file, or ``{}`` if missing."""
    if not path.exists():
        return {}
    try:
        post = frontmatter.load(path)
        return dict(post.metadata)
    except Exception as exc:  # noqa: BLE001
        logger.warning("frontmatter parse failed for %s: %s", path, exc)
        return {}


# ---------------------------------------------------------------------------
# Runner

@dataclass
class SyncStats:
    pages: int = 0
    files: int = 0
    errors: int = 0

    def summary(self, seconds: float) -> str:
        return (
            f"synced {self.pages} pages, {self.files} files, "
            f"{self.errors} errors in {seconds:.1f} seconds"
        )


def _log_event(log_path: Path, source: str, action: str, detail: dict[str, Any]) -> None:
    """Append one newline-delimited JSON record to the sync log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": now_iso(),
        "source": source,
        "action": action,
        "detail": detail,
    }
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def _require_atlassian_env() -> tuple[str, str, str]:
    missing = [
        name for name in (
            "KNOWLEDGE_MCP_ATLASSIAN_SITE",
            "KNOWLEDGE_MCP_ATLASSIAN_EMAIL",
            "KNOWLEDGE_MCP_ATLASSIAN_TOKEN",
        )
        if not os.environ.get(name)
    ]
    if missing:
        raise SystemExit(
            "Missing required environment variables: " + ", ".join(missing)
        )
    return (
        os.environ["KNOWLEDGE_MCP_ATLASSIAN_SITE"],
        os.environ["KNOWLEDGE_MCP_ATLASSIAN_EMAIL"],
        os.environ["KNOWLEDGE_MCP_ATLASSIAN_TOKEN"],
    )


def sync_confluence(
    ref_root: Path,
    log_path: Path,
    pilot: bool,
    dry_run: bool,
    stats: SyncStats,
) -> None:
    """Sync the CA Confluence space into ``reference/confluence/CA/``."""
    site, email, token = _require_atlassian_env()
    client = ConfluenceClient(site=site, email=email, token=token)
    out_dir = ref_root / "confluence" / CA_SPACE_KEY
    touched: set[Path] = set()

    _log_event(log_path, "confluence", "sync_start", {"space": CA_SPACE_KEY, "pilot": pilot})
    seen = 0
    for page in client.list_pages(CA_SPACE_ID):
        if pilot and seen >= PILOT_PAGE_LIMIT:
            break
        seen += 1
        page_id = str(page["id"])
        title = page.get("title", "untitled")
        slug = slugify(title, page_id)
        target = out_dir / f"{slug}.md"

        remote_updated = (page.get("version") or {}).get("createdAt")
        local_fm = read_frontmatter(target)
        if remote_updated and local_fm.get("last_updated_at") == remote_updated:
            touched.add(target)
            continue

        try:
            full = client.get_page(page_id)
            body, fm, _ = render_confluence_page(client, full)
            write_markdown(target, body, fm, dry_run)
            touched.add(target)
            stats.pages += 1
            _log_event(log_path, "confluence", "page_written", {"page_id": page_id, "title": title})
        except Exception as exc:  # noqa: BLE001
            stats.errors += 1
            logger.exception("confluence page %s failed", page_id)
            _log_event(log_path, "confluence", "error", {"page_id": page_id, "error": str(exc)})

    if not pilot and not dry_run and out_dir.exists():
        _move_untouched(out_dir, touched, ref_root / "_deleted" / "confluence")
    _log_event(log_path, "confluence", "sync_end", {"pages": stats.pages})


def _move_untouched(folder: Path, touched: set[Path], deleted_root: Path) -> None:
    """Move any markdown file under ``folder`` not in ``touched`` to tombstones."""
    for path in folder.rglob("*.md"):
        if path in touched:
            continue
        rel = path.relative_to(folder)
        dest = deleted_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            post = frontmatter.load(path)
            post.metadata["deleted_at"] = now_iso()
            dest.write_text(frontmatter.dumps(post), encoding="utf-8")
        except Exception:  # noqa: BLE001
            dest.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        path.unlink()


def _list_repos(org: str) -> list[dict[str, Any]]:
    if org == "personal":
        endpoint = f"users/{PERSONAL_USER}/repos"
    else:
        endpoint = f"orgs/{CURVE_ORG}/repos"
    repos = gh_api(endpoint, paginate=True) or []
    return [r for r in repos if not r.get("archived")]


def _select_repos(org: str, pilot: bool) -> list[dict[str, Any]]:
    repos = _list_repos("personal" if org == "personal" else org)
    out: list[dict[str, Any]] = []
    for r in repos:
        name = r.get("name", "")
        if name in SKIP_REPOS:
            continue
        if org == "curve":
            if name.startswith("intech-"):
                continue
            out.append(r)
        elif org == "intech":
            if not name.startswith("intech-"):
                continue
            out.append(r)
        elif org == "personal":
            out.append(r)
    if pilot:
        out = [r for r in out if r.get("name") == PILOT_REPO]
    return out


def _decode_contents(payload: dict[str, Any]) -> bytes | None:
    content = payload.get("content")
    encoding = payload.get("encoding")
    if not content or encoding != "base64":
        return None
    return base64.b64decode(content)


def sync_github_repo(
    repo: dict[str, Any],
    org_bucket: str,
    ref_root: Path,
    log_path: Path,
    dry_run: bool,
    stats: SyncStats,
    full_mode: bool,
) -> None:
    """Sync one GitHub repo's docs + code files into the reference tree."""
    full_name = repo["full_name"]
    name = repo["name"]
    default_branch = repo.get("default_branch") or "main"
    pushed_at = repo.get("pushed_at")

    repo_dir = ref_root / "github" / org_bucket / name
    meta_path = repo_dir / "_meta.md"
    local_meta = read_frontmatter(meta_path)
    # Short-circuit only when the remote hasn't moved AND the previous sync
    # left no errors behind. Otherwise re-walk the tree so per-file blob_sha
    # idempotency can pick up anything that was missed last time.
    prior_errors = int(local_meta.get("errors_last_run") or 0)
    if local_meta.get("pushed_at") == pushed_at and prior_errors == 0:
        _log_event(log_path, "github", "repo_skipped", {"repo": full_name})
        return
    repo_errors_at_start = stats.errors

    # Build _meta.md.
    try:
        tree_root = gh_api(
            f"repos/{full_name}/git/trees/{default_branch}?recursive=0"
        ) or {"tree": []}
    except RuntimeError as exc:
        stats.errors += 1
        _log_event(log_path, "github", "error", {"repo": full_name, "error": str(exc)})
        return

    top_entries = [f"{e['path']} ({e['type']})" for e in tree_root.get("tree", [])]

    readme_excerpt = ""
    try:
        readme_payload = gh_api(f"repos/{full_name}/readme")
        if readme_payload:
            raw = _decode_contents(readme_payload) or b""
            readme_excerpt = raw.decode("utf-8", errors="replace")[:500]
    except RuntimeError as exc:
        logger.warning("readme fetch failed for %s: %s", full_name, exc)

    # Full tree first — we need per-file counts before writing _meta.md so
    # `errors_last_run` reflects what actually happened.
    try:
        tree = gh_api(
            f"repos/{full_name}/git/trees/{tree_root.get('sha', default_branch)}?recursive=1"
        ) or {"tree": []}
    except RuntimeError as exc:
        stats.errors += 1
        _log_event(log_path, "github", "error", {"repo": full_name, "error": str(exc)})
        return

    touched: set[Path] = {meta_path}
    for entry in tree.get("tree", []):
        if entry.get("type") != "blob":
            continue
        path = entry["path"]
        size = entry.get("size")
        include, kind = should_index_github_file(path, size)
        if not include or kind is None:
            continue

        filename = github_filename(kind, path)
        target = repo_dir / filename
        touched.add(target)

        # Per-file timestamp check: we don't have per-blob timestamps on the
        # tree listing, so use repo ``pushed_at`` as a coarse gate plus file
        # sha stored in frontmatter as ``blob_sha``.
        local_fm = read_frontmatter(target)
        if local_fm.get("blob_sha") == entry.get("sha"):
            continue

        try:
            content_payload = gh_api(
                f"repos/{full_name}/contents/{path}?ref={default_branch}"
            )
            raw = _decode_contents(content_payload or {}) or b""
        except RuntimeError as exc:
            stats.errors += 1
            _log_event(log_path, "github", "error", {"repo": full_name, "path": path, "error": str(exc)})
            continue

        text = raw.decode("utf-8", errors="replace")
        # Wrap code in a fenced block so the chunker doesn't choke on odd
        # content that happens to contain ``---`` sequences.
        if kind == "code":
            lang = path.rsplit(".", 1)[-1] if "." in path else ""
            body = f"```{lang}\n{text}\n```\n"
        else:
            body = text

        fm = {
            "source": "github_doc" if kind == "doc" else "github_code",
            "source_url": f"{repo.get('html_url')}/blob/{default_branch}/{path}",
            "title": f"{full_name}:{path}",
            "synced_at": now_iso(),
            "last_updated_at": pushed_at,
            "org": org_bucket,
            "repo": full_name,
            "path": path,
            "blob_sha": entry.get("sha"),
        }
        write_markdown(target, body, fm, dry_run)
        stats.files += 1

    # Write _meta.md at the end, stamped with this run's error count so the
    # next run's repo-level gate can tell whether to trust the per-file
    # short-circuit or re-walk the tree.
    errors_this_run = stats.errors - repo_errors_at_start
    meta_body = repo_meta_markdown(repo, readme_excerpt, top_entries)
    meta_fm = {
        "source": "github_doc",
        "source_url": repo.get("html_url"),
        "title": f"{full_name} (overview)",
        "synced_at": now_iso(),
        "last_updated_at": pushed_at,
        "org": org_bucket,
        "repo": full_name,
        "path": "_meta",
        "pushed_at": pushed_at,
        "errors_last_run": errors_this_run,
    }
    write_markdown(meta_path, meta_body, meta_fm, dry_run)
    stats.files += 1

    if full_mode and not dry_run and repo_dir.exists():
        _move_untouched(repo_dir, touched, ref_root / "_deleted" / "github" / org_bucket / name)


def sync_github(
    ref_root: Path,
    log_path: Path,
    pilot: bool,
    dry_run: bool,
    stats: SyncStats,
    org_filter: str | None,
) -> None:
    """Sync configured GitHub subtrees. ``org_filter`` narrows to one bucket."""
    original = gh_current_account()
    _log_event(log_path, "github", "sync_start", {"pilot": pilot, "org": org_filter})

    buckets: list[str]
    if pilot:
        buckets = ["intech"]
    elif org_filter:
        buckets = [org_filter]
    else:
        buckets = ["curve", "intech", "personal"]

    try:
        for bucket in buckets:
            account = PERSONAL_GH_ACCOUNT if bucket == "personal" else CURVE_GH_ACCOUNT
            gh_switch(account)
            repos = _select_repos(bucket, pilot)
            for repo in repos:
                try:
                    sync_github_repo(
                        repo=repo,
                        org_bucket=bucket,
                        ref_root=ref_root,
                        log_path=log_path,
                        dry_run=dry_run,
                        stats=stats,
                        full_mode=not pilot,
                    )
                except Exception as exc:  # noqa: BLE001
                    stats.errors += 1
                    logger.exception("github repo %s failed", repo.get("full_name"))
                    _log_event(log_path, "github", "error", {"repo": repo.get("full_name"), "error": str(exc)})
    finally:
        if original:
            gh_switch(original)
    _log_event(log_path, "github", "sync_end", {"files": stats.files})


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Sync reference corpus into the vault")
    p.add_argument("--pilot", action="store_true", help="20 CA pages + intech-enrich only")
    p.add_argument("--source", choices=["confluence", "github"], help="Only sync one source")
    p.add_argument("--org", choices=["curve", "intech", "personal"], help="Filter GitHub org bucket")
    p.add_argument("--dry-run", action="store_true", help="Fetch + compare but do not write")
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    ref_root = _resolve_vault_path() / "reference"
    ref_root.mkdir(parents=True, exist_ok=True)
    log_path = ref_root / "_sync.log"

    stats = SyncStats()
    started = time.time()

    do_confluence = args.source in (None, "confluence")
    do_github = args.source in (None, "github")

    if do_confluence:
        sync_confluence(ref_root, log_path, args.pilot, args.dry_run, stats)
    if do_github:
        sync_github(ref_root, log_path, args.pilot, args.dry_run, stats, args.org)

    elapsed = time.time() - started
    summary = stats.summary(elapsed)
    logger.info(summary)
    print(summary)
    return 0 if stats.errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
