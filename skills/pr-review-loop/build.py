"""Deterministic data + render layer for the pr-review-loop skill.

The SKILL.md is the source of truth; this is the runnable companion (mirrors
cdt-daily-pr-digest/build.py). It handles the parts that should NOT be left to
the model: fetching PRs, the GitHub review-state quirks, marker detection, and
rendering the digest. The agentic review fan-out lives in the skill.

Two modes:

    python build.py --actionable
        Emit JSON of PRs that need reviewing this run (new, or new commits
        since the loop's last `reviewed-at` marker). The skill reads this,
        fans out reviews, and produces a verdicts map.

    python build.py --render verdicts.json
        Given {"<repo>#<num>": {"verdict": "...", "reviewer": "@claude"}, ...}
        produced by the skill, fetch live state and print the digest markdown.

`gh` must be authenticated with repo + read:org scopes. Uses
`--repo curveanalytics/<repo>` so no personal account switching is needed.
"""
import json
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from collections import defaultdict

ORG = "curveanalytics"

REPOS = [
    "intech-hub", "intech-cicd", "intech-infra", "intech-data", "intech-etl",
    "intech-models", "intech-experience", "intech-control-plane",
    "intech-compute-plane", "intech-data-plane", "intech-experience-ui",
    "intech-ai-plugin",
]

TEAM = {
    "adele-curve": "Adele", "Issei-curve": "Issei", "seanc-curve": "Sean",
    "nik10-mah": "Nikhil", "Luke-curve": "Luke", "J-Curwell": "James",
}

RELEASE_BOTS = {"release-please[bot]", "github-actions[bot]"}

# The marker every loop review leaves; drives idempotency + attribution.
MARKER_RE = re.compile(r"<!--\s*pr-review-loop:\s*reviewed-at=([0-9a-fA-F]+)\s*-->")

CONV_PREFIX_RE = re.compile(
    r"^(feat|fix|chore|docs|test|refactor|perf|build|ci|style|revert)(\([^)]+\))?!?:\s*",
    re.IGNORECASE,
)

NOW = datetime.now(timezone.utc)


def gh_json(args):
    try:
        out = subprocess.run(args, capture_output=True, text=True, timeout=60, check=True)
        return json.loads(out.stdout)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return []


def load_open(repo):
    return gh_json([
        "gh", "pr", "list", "--repo", f"{ORG}/{repo}", "--state", "open",
        "--json", "number,title,author,updatedAt,isDraft,url,headRefOid,"
        "reviewDecision,reviews,reviewRequests", "--limit", "100",
    ])


def load_merged(repo, since: datetime):
    prs = gh_json([
        "gh", "pr", "list", "--repo", f"{ORG}/{repo}", "--state", "merged",
        "--json", "number,title,author,url,mergedAt,mergedBy", "--limit", "50",
    ])
    out = []
    for pr in prs:
        m = pr.get("mergedAt")
        if m and datetime.fromisoformat(m.replace("Z", "+00:00")) >= since:
            out.append(pr)
    return out


def window_start() -> datetime:
    """Last weekday: Tue-Fri -> yesterday 00:00; Mon -> last Friday 00:00."""
    d = NOW
    back = 3 if d.weekday() == 0 else 1  # Monday -> Friday
    start = (d - timedelta(days=back)).replace(hour=0, minute=0, second=0, microsecond=0)
    return start


def is_team_pr(pr):
    if pr.get("isDraft"):
        return False
    author = (pr.get("author") or {}).get("login", "")
    if author in RELEASE_BOTS or author not in TEAM:
        return False
    title = pr.get("title", "")
    if title.startswith("chore(main): release") or title.lower().startswith("release "):
        return False
    return True


def non_self_reviews(pr):
    me = (pr.get("author") or {}).get("login", "")
    return [r for r in (pr.get("reviews") or [])
            if (r.get("author") or {}).get("login") != me]


def loop_marker_sha(pr):
    """Latest reviewed-at SHA the loop recorded on this PR, or None."""
    sha = None
    latest = ""
    for r in (pr.get("reviews") or []):
        m = MARKER_RE.search(r.get("body") or "")
        if m and r.get("submittedAt", "") >= latest:
            latest, sha = r.get("submittedAt", ""), m.group(1)
    return sha


def needs_review(pr):
    """True if unreviewed by the loop, or there are new commits since its marker."""
    sha = loop_marker_sha(pr)
    if sha is None:
        return True
    return not (pr.get("headRefOid", "").startswith(sha) or sha.startswith(pr.get("headRefOid", "")))


def short_title(title, max_len=60):
    t = CONV_PREFIX_RE.sub("", title.strip())
    if t:
        t = t[0].upper() + t[1:]
    return t[: max_len - 1] + "…" if len(t) > max_len else t


def human_reviewer(pr):
    """Latest non-self human reviewer login + whether they requested changes."""
    nsr = [r for r in non_self_reviews(pr) if not MARKER_RE.search(r.get("body") or "")]
    if not nsr:
        return None, False
    nsr.sort(key=lambda r: r.get("submittedAt", ""), reverse=True)
    top = nsr[0]
    return (top.get("author") or {}).get("login"), top.get("state") == "CHANGES_REQUESTED"


def key(repo, num):
    return f"{repo}#{num}"


def cmd_actionable():
    out = []
    for repo in REPOS:
        for pr in load_open(repo):
            if is_team_pr(pr) and needs_review(pr):
                out.append({
                    "key": key(repo, pr["number"]), "repo": repo, "number": pr["number"],
                    "url": pr["url"], "title": pr["title"],
                    "author": (pr.get("author") or {}).get("login"),
                    "headRefOid": pr.get("headRefOid"),
                    "reviewed_before": loop_marker_sha(pr) is not None,
                })
    print(json.dumps(out, indent=2))


def cmd_render(verdicts_path):
    with open(verdicts_path, encoding="utf-8") as f:
        verdicts = json.load(f)  # {"<repo>#<n>": {"verdict": "...", "reviewer": "@x", "note": "..."}}

    since = window_start()
    shipped, approved, awaiting, followup = [], [], [], []

    for repo in REPOS:
        for pr in load_merged(repo, since):
            if (pr.get("author") or {}).get("login") in TEAM:
                shipped.append((repo, pr))
        for pr in load_open(repo):
            if not is_team_pr(pr):
                continue
            k = key(repo, pr["number"])
            v = verdicts.get(k, {})
            verdict = v.get("verdict")
            if pr.get("reviewDecision") == "APPROVED":
                approved.append((repo, pr, v))
            elif verdict == "Needs Changes":
                followup.append((repo, pr, v))
            elif verdict in ("Looks good", "Minor comments", "Needs Judgment"):
                awaiting.append((repo, pr, v))
            else:
                # No loop verdict this run - attribute to the human reviewer if any.
                who, changed = human_reviewer(pr)
                v = {"reviewer": f"@{who}" if who else None}
                (followup if changed else awaiting).append((repo, pr, v))

    print(render(shipped, approved, awaiting, followup, since))


def _line(repo, pr, v=None, show_verdict=True):
    author = (pr.get("author") or {}).get("login", "?")
    base = f"- {short_title(pr['title'])} ([{repo}#{pr['number']}]({pr['url']}), @{author})"
    if not v:
        return base
    bits = []
    if v.get("reviewer"):
        bits.append(f"reviewed: {v['reviewer']}")
    if show_verdict and v.get("verdict"):
        bits.append(f"`{v['verdict']}`")
    if v.get("note"):
        bits.append(v["note"])
    return base + " — " + " · ".join(bits) if bits else base


def render(shipped, approved, awaiting, followup, since):
    L = [f"**CDT PR digest — {NOW.strftime('%a %d %b')}**"]
    counts = [f"{len(approved) + len(awaiting) + len(followup)} open"]
    if awaiting:
        counts.append(f"{len(awaiting)} awaiting human review")
    if followup:
        counts.append(f"{len(followup)} with the author")
    if approved:
        counts.append(f"{len(approved)} ready to merge")
    L += [f"`{' · '.join(counts)}`", ""]

    if shipped:
        L.append(f"🎉 **Shipped since {since.strftime('%A')}** ({len(shipped)})")
        L += [_line(r, pr) for r, pr in shipped] + [""]
    if approved:
        L.append(f"✅ **Approved — ready to merge** ({len(approved)})")
        for r, pr, v in approved:
            author = (pr.get("author") or {}).get("login", "?")
            L.append(f"- {short_title(pr['title'])} ([{r}#{pr['number']}]({pr['url']}), "
                     f"@{author}) — approved: {v.get('reviewer') or '?'}")
        L.append("")
    if awaiting:
        L.append(f"👀 **Awaiting human review** ({len(awaiting)})")
        # business-logic (Needs Judgment) pinned to the top with a ⚠️ flag
        ordered = sorted(awaiting, key=lambda t: t[2].get("verdict") != "Needs Judgment")
        for r, pr, v in ordered:
            line = _line(r, pr, v)
            if v.get("verdict") == "Needs Judgment":
                line = "- ⚠️ " + line[2:]
            L.append(line)
        L.append("")
    if followup:
        L.append(f"🟠 **Needs follow-up — waiting on the author** ({len(followup)})")
        L += [_line(r, pr, v) for r, pr, v in followup] + [""]

    return "\n".join(L).rstrip()


def main():
    if "--actionable" in sys.argv:
        cmd_actionable()
    elif "--render" in sys.argv:
        cmd_render(sys.argv[sys.argv.index("--render") + 1])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
