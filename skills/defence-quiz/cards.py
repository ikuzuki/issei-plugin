"""Defence-card queue: pick due cards, record results, check staleness, export.

Cards live as markdown with YAML frontmatter under the vault's cards/ folder.
This script owns the scheduling arithmetic and the frontmatter writes so the
skill never has to parse YAML in prose.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

VAULT = Path(r"C:\Users\IsseiKuzuki\Knowledge Base\knowledge-vault")
CARDS = VAULT / "cards"
CAP_DAYS = 90
GITHUB_ORG = "curveanalytics"
LOCAL_REPOS = {
    "fpl-platform": Path(r"C:\Users\IsseiKuzuki\fpl-platform"),
    "knowledge-base": Path(r"C:\Users\IsseiKuzuki\Knowledge Base"),
}

FM_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", re.S)


def load(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if not m:
        raise ValueError(f"no frontmatter: {path}")
    fm = yaml.safe_load(m.group(1)) or {}
    # YAML 1.1 reads a bare `no` as boolean False; the mark is the string.
    if fm.get("confidence") is False:
        fm["confidence"] = "no"
    return fm, m.group(2)


def dump(path: Path, fm: dict, body: str) -> None:
    head = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=1000)
    path.write_text(f"---\n{head}---\n{body}", encoding="utf-8")


def iter_cards():
    for p in sorted(CARDS.glob("*.md")):
        if p.name.lower() == "readme.md":
            continue
        fm, body = load(p)
        yield p, fm, body


def as_date(v) -> dt.date | None:
    if v in (None, "", "null"):
        return None
    if isinstance(v, dt.date):
        return v
    return dt.date.fromisoformat(str(v)[:10])


def pick(rows: list[tuple], n: int) -> list[dict]:
    """Soonest due first, fewest tests next, then a shuffle, spread across areas.

    rows are (due_date, tested, fm). Ties are broken randomly rather than by
    id so a fresh deck does not come out alphabetically, and the greedy pass
    prefers an area not yet picked so three cards are three topics.
    """
    import random

    rows = sorted(rows, key=lambda r: (r[0], r[1], random.random()))
    picked: list[dict] = []
    seen_areas: set[str] = set()
    for _, _, fm in rows:
        if len(picked) >= n:
            break
        if fm.get("area") in seen_areas:
            continue
        picked.append(fm)
        seen_areas.add(fm.get("area"))
    if len(picked) < n:
        chosen = {fm["id"] for fm in picked}
        for _, _, fm in rows:
            if len(picked) >= n:
                break
            if fm["id"] not in chosen:
                picked.append(fm)
    return picked


def cmd_due(a: argparse.Namespace) -> None:
    today = dt.date.today()
    rows = []
    for p, fm, _ in iter_cards():
        if a.area and fm.get("area") != a.area:
            continue
        if a.level and fm.get("level") != a.level:
            continue
        if a.unreviewed and fm.get("reviewed_by_me"):
            continue
        if a.portable and not fm.get("portable"):
            continue
        due = as_date(fm.get("next_due")) or today
        if a.only_overdue and due > today:
            continue
        rows.append((due, int(fm.get("tested") or 0), fm))
    picked = pick(rows, a.n)
    if a.json:
        print(json.dumps(picked, default=str, indent=2))
        return
    for fm in picked:
        print(
            f"{fm['id']}\t{fm.get('area')}\t{fm.get('level')}\t{fm.get('confidence')}"
            f"\tdue {fm.get('next_due')}\t{fm['question']}"
        )


def cmd_show(a: argparse.Namespace) -> None:
    p = CARDS / f"{a.id}.md"
    print(p.read_text(encoding="utf-8"))


def cmd_record(a: argparse.Namespace) -> None:
    p = CARDS / f"{a.id}.md"
    fm, body = load(p)
    today = dt.date.today()
    interval = int(fm.get("interval_days") or 1)
    if a.mark == "whiteboard":
        interval = min(CAP_DAYS, max(2, interval * 2))
    elif a.mark == "shaky":
        interval = max(1, interval // 2)
    else:
        interval = 1
    fm["confidence"] = a.mark
    fm["interval_days"] = interval
    fm["last_tested"] = today.isoformat()
    fm["next_due"] = (today + dt.timedelta(days=interval)).isoformat()
    fm["tested"] = int(fm.get("tested") or 0) + 1
    if a.miss:
        body = body.rstrip("\n") + f"\n- {today.isoformat()}: {a.miss}\n"
    dump(p, fm, body)
    print(f"{a.id}: {a.mark}, interval {interval}d, next due {fm['next_due']}")


def cmd_set(a: argparse.Namespace) -> None:
    p = CARDS / f"{a.id}.md"
    fm, body = load(p)
    for kv in a.pairs:
        k, _, v = kv.partition("=")
        fm[k] = yaml.safe_load(v)
    dump(p, fm, body)
    print(f"{a.id}: set {', '.join(a.pairs)}")


def cmd_stats(a: argparse.Namespace) -> None:
    today = dt.date.today()
    by_area: dict[str, dict[str, int]] = {}
    total = overdue = stale = unreviewed = 0
    for _, fm, _ in iter_cards():
        total += 1
        area = str(fm.get("area"))
        conf = str(fm.get("confidence"))
        by_area.setdefault(area, {"whiteboard": 0, "shaky": 0, "no": 0, "n": 0})
        by_area[area][conf] = by_area[area].get(conf, 0) + 1
        by_area[area]["n"] += 1
        if (as_date(fm.get("next_due")) or today) <= today:
            overdue += 1
        if fm.get("stale"):
            stale += 1
        if not fm.get("reviewed_by_me"):
            unreviewed += 1
    if a.json:
        print(json.dumps({"total": total, "due": overdue, "stale": stale, "unreviewed": unreviewed, "by_area": by_area}, indent=2))
        return
    print(f"cards {total}  due {overdue}  stale {stale}  not yet in my words {unreviewed}")
    for area, c in sorted(by_area.items()):
        print(f"  {area:16} n={c['n']:3}  whiteboard={c['whiteboard']:3}  shaky={c['shaky']:3}  no={c['no']:3}")


def cmd_export(a: argparse.Namespace) -> None:
    out = []
    for p, fm, body in iter_cards():
        out.append({**fm, "body": body, "file": p.name})
    print(json.dumps(out, default=str, indent=2))


_compare_cache: dict[tuple[str, str], set[str] | None] = {}


def changed_files(repo: str, sha: str) -> set[str] | None:
    key = (repo, sha)
    if key in _compare_cache:
        return _compare_cache[key]
    files: set[str] | None
    try:
        if repo in LOCAL_REPOS:
            local = LOCAL_REPOS[repo]
            subprocess.run(["git", "-C", str(local), "fetch", "-q", "origin"], check=False)
            out = subprocess.run(
                ["git", "-C", str(local), "diff", "--name-only", sha, "origin/main"],
                capture_output=True, text=True, check=True,
            ).stdout
        else:
            out = subprocess.run(
                ["gh", "api", f"repos/{GITHUB_ORG}/{repo}/compare/{sha}...main", "--paginate",
                 "--jq", ".files[].filename"],
                capture_output=True, text=True, check=True,
            ).stdout
        files = {line.strip() for line in out.splitlines() if line.strip()}
    except subprocess.CalledProcessError as e:
        print(f"  ! could not compare {repo}@{sha[:8]}: {e.stderr.strip()[:200]}", file=sys.stderr)
        files = None
    _compare_cache[key] = files
    return files


def cmd_refresh(a: argparse.Namespace) -> None:
    today = dt.date.today().isoformat()
    flagged = 0
    for p, fm, body in iter_cards():
        moved = []
        for s in fm.get("sources") or []:
            if not isinstance(s, dict) or "repo" not in s or not s.get("sha") or not s.get("path"):
                continue
            files = changed_files(s["repo"], str(s["sha"]))
            if files is None:
                continue
            path = str(s["path"]).rstrip("/")
            if path in files or any(f.startswith(path + "/") for f in files):
                moved.append(f"{s['repo']}:{path}")
        if moved and not fm.get("stale"):
            fm["stale"] = True
            fm["stale_note"] = f"{today}: moved since pin: " + ", ".join(moved)
            dump(p, fm, body)
            flagged += 1
            print(f"stale  {fm['id']}  {', '.join(moved)}")
    print(f"refresh done: {flagged} newly stale")


def cmd_repin(a: argparse.Namespace) -> None:
    p = CARDS / f"{a.id}.md"
    fm, body = load(p)
    for s in fm.get("sources") or []:
        if not isinstance(s, dict) or "repo" not in s or not s.get("sha"):
            continue
        repo = s["repo"]
        if repo in LOCAL_REPOS:
            sha = subprocess.run(["git", "-C", str(LOCAL_REPOS[repo]), "rev-parse", "origin/main"],
                                 capture_output=True, text=True, check=True).stdout.strip()
        else:
            sha = subprocess.run(["gh", "api", f"repos/{GITHUB_ORG}/{repo}/commits/main", "--jq", ".sha"],
                                 capture_output=True, text=True, check=True).stdout.strip()
        s["sha"] = sha
    fm["stale"] = False
    fm.pop("stale_note", None)
    dump(p, fm, body)
    print(f"{a.id}: repinned to current main, stale cleared")


BODY_ORDER = ["Claim", "Why", "Rejected", "Where", "Prevents", "Trade-off", "Misses"]
AREAS = ["sys", "mt", "auth", "cp", "cmp", "ing", "ml", "etl", "dp", "exp", "ops", "ai", "fund", "me"]
LEVELS = {"system", "component", "mechanism", "integration", "operational"}
KINDS = {"mechanism", "decision", "fundamental"}


def cmd_lint(a: argparse.Namespace) -> None:
    """Structural checks; with --repos-dir also checks pinned repo paths exist."""
    problems = 0
    repos_dir = Path(a.repos_dir) if a.repos_dir else None
    for p, fm, body in iter_cards():
        cid = fm.get("id", p.stem)
        errs = []
        if cid != p.stem:
            errs.append(f"id {cid} != filename {p.stem}")
        prefix = p.stem.split("-")[0]
        if fm.get("area") != prefix:
            errs.append(f"area {fm.get('area')!r} should be {prefix!r}")
        if fm.get("level") not in LEVELS:
            errs.append(f"level {fm.get('level')!r}")
        if fm.get("kind") not in KINDS:
            errs.append(f"kind {fm.get('kind')!r}")
        if fm.get("confidence") not in ("whiteboard", "shaky", "no"):
            errs.append(f"confidence {fm.get('confidence')!r}")
        if not isinstance(fm.get("portable"), bool):
            errs.append("portable not set")
        if "?" not in str(fm.get("question", "")):
            errs.append("question is not a question")
        labels = re.findall(r"^\*\*([\w-]+)\.\*\*", body, re.M)
        missing = [l for l in BODY_ORDER[:-1] if l not in labels]
        if missing:
            errs.append(f"missing body lines {missing}")
        if [l for l in labels if l in BODY_ORDER] != [l for l in BODY_ORDER if l in labels]:
            errs.append(f"body line order {labels}")
        content_lines = [l for l in body.splitlines() if l.strip() and not l.startswith("#")]
        if len(content_lines) > 12:
            errs.append(f"body has {len(content_lines)} non-empty lines (ceiling ten plus Misses)")
        if "not recorded" in body.lower():
            errs.append("Rejected not recorded in sources (review, not necessarily wrong)")
        for s in fm.get("sources") or []:
            if not isinstance(s, dict):
                errs.append(f"source not a mapping: {s!r}")
                continue
            if "repo" in s:
                if not s.get("sha"):
                    errs.append(f"repo source without sha: {s.get('repo')}:{s.get('path')}")
                if repos_dir and s.get("path") and (repos_dir / s["repo"]).exists():
                    if not (repos_dir / s["repo"] / str(s["path"]).rstrip("/")).exists():
                        errs.append(f"path missing in staged repo: {s['repo']}:{s['path']}")
            if "vault" in s and not (VAULT / str(s["vault"])).exists():
                errs.append(f"vault note missing: {s['vault']}")
        if errs:
            problems += len(errs)
            print(f"{cid}")
            for e in errs:
                print(f"  - {e}")
    print(f"lint: {problems} findings")


def cmd_normalise(a: argparse.Namespace) -> None:
    """Set area to the filename prefix on every card."""
    n = 0
    for p, fm, body in iter_cards():
        prefix = p.stem.split("-")[0]
        if fm.get("area") != prefix:
            fm["area"] = prefix
            dump(p, fm, body)
            n += 1
    print(f"normalised area on {n} cards")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("due", help="cards to test next, soonest due first")
    d.add_argument("--n", type=int, default=3)
    d.add_argument("--area")
    d.add_argument("--level")
    d.add_argument("--unreviewed", action="store_true", help="only cards not yet in my words")
    d.add_argument("--portable", action="store_true", help="only cards whose idea transfers beyond Curve")
    d.add_argument("--only-overdue", action="store_true")
    d.add_argument("--json", action="store_true")
    d.set_defaults(fn=cmd_due)

    s = sub.add_parser("show", help="print one card")
    s.add_argument("id")
    s.set_defaults(fn=cmd_show)

    r = sub.add_parser("record", help="record a quiz result and reschedule")
    r.add_argument("id")
    r.add_argument("--mark", choices=["whiteboard", "shaky", "no"], required=True)
    r.add_argument("--miss", help="what was wrong or missing, appended under Misses")
    r.set_defaults(fn=cmd_record)

    st = sub.add_parser("set", help="set frontmatter keys, e.g. reviewed_by_me=true")
    st.add_argument("id")
    st.add_argument("pairs", nargs="+")
    st.set_defaults(fn=cmd_set)

    x = sub.add_parser("stats")
    x.add_argument("--json", action="store_true")
    x.set_defaults(fn=cmd_stats)

    e = sub.add_parser("export", help="all cards as JSON, for the UI")
    e.set_defaults(fn=cmd_export)

    f = sub.add_parser("refresh", help="mark cards stale when pinned code moved")
    f.set_defaults(fn=cmd_refresh)

    rp = sub.add_parser("repin", help="after re-verifying a stale card, pin to current main")
    rp.add_argument("id")
    rp.set_defaults(fn=cmd_repin)

    ln = sub.add_parser("lint", help="structural checks over every card")
    ln.add_argument("--repos-dir", help="folder of staged repos to verify pinned paths against")
    ln.set_defaults(fn=cmd_lint)

    nm = sub.add_parser("normalise", help="set area = filename prefix on every card")
    nm.set_defaults(fn=cmd_normalise)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
