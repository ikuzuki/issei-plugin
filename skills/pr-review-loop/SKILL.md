---
name: pr-review-loop
description: Autonomous, scheduled PR-review loop over the CDT team's open pull requests. Surfaces PRs by lifecycle state, clusters related ones, fans out to cheaper-model sub-agents for the review, posts a structured top-level verdict plus inline comments in a neutral voice, and ALWAYS defers approval and merge to a human. Idempotent - skips PRs already reviewed at the current head commit. Its run output is a status digest that supersedes cdt-daily-pr-digest. Use when a scheduled routine fires it, or when the user says "run the PR review loop", "do the PR review pass", "review the open CDT PRs", or "/pr-review-loop". Distinct from `turbo-pr-review` (interactive, single PRs, confirms before posting) and `intech-tools:code-review` (heavy multi-agent single-PR audit). Do NOT use for an interactive walkthrough of one PR (use `turbo-pr-review`) or for code not yet raised as a PR. Repo set and team filter live in `build.py`; comment voice in `references/comment-voice.md`.
---

# PR review loop

An unattended review pass over the CDT team's open PRs, built to run on a cron.
It finds the PRs needing eyes, groups related ones, reviews each at a consistent
bar, posts comments, and leaves only the approve/merge judgment to a human. Its
output digest replaces `cdt-daily-pr-digest` once live.

This is a loop, not an interactive skill - the audience for its comments is the
PR author and any downstream agent, not a human reading a walkthrough. It skips
the plain-English explainer `turbo-pr-review` leads with, and writes in the
neutral voice defined in [`references/comment-voice.md`](references/comment-voice.md).

`build.py` is the runnable companion (mirrors `cdt-daily-pr-digest/build.py`):
it owns the repo set, team filter, the GitHub review-state quirks, marker
detection, and digest rendering. The skill drives the agentic review around it.
`gh` must be authenticated with `repo` + `read:org` scopes; the script uses
`--repo curveanalytics/<repo>` so no account switching is needed.

## Hard rules

1. **Never approve, request-changes, or merge.** Every posted review is
   `event=COMMENT`. The verdict is advisory; a human approves. Branch
   protection is the backstop.
2. **Defer business logic.** If correctness hinges on domain intent not legible
   from the code, don't guess - verdict `Needs Judgment`, name the lines.
3. **Idempotent.** Never review the same PR at the same head commit twice.
4. **Fail loud.** Unreachable repo, sub-agent error, budget trip - all go in
   the run summary. A silent skip looks like "nothing to review".

## Shadow mode (V1 default)

Until `PR_REVIEW_LOOP_LIVE=1` is set, do the full review but write drafts to
`C:\tmp\pr-review-loop\<date>\<repo>-<n>.md` instead of posting, and print the
digest. Lets the verifier be validated on real PRs before posting. Default OFF.

## Process

### 1. Find what to review

`python build.py --actionable` returns JSON of the PRs needing review this run -
new PRs, or PRs with new commits since the loop's last `reviewed-at` marker.
Unchanged PRs are skipped here (the marker is the memory; no external store).

### 2. Cluster

Group PRs reviewed together by linked ticket - parse the branch name first
(`CDT-NNN` / `INTECH-NNN`), which is free. Beyond the ticket, use the Atlassian
(Jira) connector to read ticket bodies for related work, shared contracts, or
explicit cross-PR dependencies. Cross-repo PRs for one ticket cluster together;
unrelated PRs review independently.

### 3. Review - fan out on a cheaper model

For each group, spawn a sub-agent with **`model: sonnet`** (not the
orchestrator's Opus - running every review on Opus is the cost trap). Each
sub-agent runs the `intech-tools:code-review` analysis flow, citing
`intech-tools:coding-standards`, over the group's diff and returns findings
categorised as real bugs / design questions / nits (secret scanning rides along
in that flow - don't duplicate). It cross-references existing comments and does
not re-raise a point already made or contradict a human reviewer without new
reasoning. For stacked PRs, review only the incremental diff. The orchestrator
keeps Opus for clustering, business-logic judgment, and synthesis.

Budget guard: cap PRs per run and sub-agents in flight; on the first run (whole
backlog at once) cap hard and note what was deferred. Trip the budget - stop and
report, don't spin.

### 4. Assign a verdict and compose

Each group gets exactly one verdict:

- `Looks good` - no blocking findings; needs a human approve.
- `Minor comments` - only nits; approvable as-is.
- `Needs Changes` - a real bug or blocking concern; author's court.
- `Needs Judgment` - correctness hinges on domain/business logic the code
  doesn't make legible; named lines left for a human. A deliberate hand-off,
  not a failure to review.

Compose the top-level comment + inline comments per
[`references/comment-voice.md`](references/comment-voice.md). The top-level body
MUST end with the marker `<!-- pr-review-loop: reviewed-at=<head-oid> -->` - it
drives idempotency (step 1) and attribution (step 6). Inline comments target a
`path:line` inside a diff hunk; lead with the verdict, group small stuff rather
than carpeting the PR.

### 5. Post (live) or write (shadow)

- **Shadow:** write each review to `C:\tmp\pr-review-loop\<date>\<repo>-<n>.md`.
- **Live** (`PR_REVIEW_LOOP_LIVE=1`): post one review per PR via
  `gh api -X POST repos/<owner>/<repo>/pulls/<n>/reviews` with `event=COMMENT`,
  `commit_id` (head OID), `body` (top-level + marker), and `comments` (inline
  array). On 422 "Line could not be resolved", move the comment to the nearest
  in-hunk line and retry once; if it still fails, fold it into the top-level
  body. Never silently lose a finding.

### 6. Render the digest

Write a verdicts map - `{"<repo>#<n>": {"verdict": "...", "reviewer": "@claude",
"note": "re-reviewed"}, ...}` - covering every PR you reviewed, then
`python build.py --render verdicts.json`. The script fetches live state, applies
the reviewer-attribution rule (this run → `@claude`; approved/merged → the human
actor; untouched-but-previously-reviewed → `@claude` if the latest review
carries the marker, else the human who left it), classifies into the four
sections, and prints the digest. **The digest is a status summary, not a review
- no findings or headlines, just the PR title (linked), author, `reviewed: @x`,
and the verdict tag.** The PR title is the only link; there's no separate
`[review]` link (the PR reference already points there). This output supersedes
`cdt-daily-pr-digest`.

Always print a run summary too (shadow or live): reviewed, skipped, deferred,
errors - fail loud.

## Anti-patterns

- Posting without the `reviewed-at` marker - breaks idempotency and attribution.
- Re-reviewing a PR whose head OID matches the marker.
- Running the review on Opus instead of Sonnet sub-agents.
- APPROVE / REQUEST_CHANGES / merge. Never.
- Guessing on business logic instead of `Needs Judgment`.
- Putting review content (findings, headlines, nit detail) in the digest - it's
  a status summary; detail lives in the posted review, reached via the PR link.
- Silent skips or swallowed errors.
- Reviewing draft or release-bot PRs (`build.py` filters these).

## Scope

The autonomous, scheduled, consistent-bar review pass. NOT interactive
walkthroughs (`turbo-pr-review`), multi-agent deep audits
(`intech-tools:code-review`), or anything that approves/merges. A prototype in
`issei-plugin`; promote to `intech-tools` before the team relies on it, at which
point the fan-out should compose the team's `code-reviewer` agents rather than
spawn inline.

## References

- [`build.py`](build.py) - runnable companion: repo set, team filter, GitHub
  review-state handling, marker detection, `--actionable` and `--render` modes.
- [`references/comment-voice.md`](references/comment-voice.md) - neutral comment
  voice and the top-level comment format. Self-contained; no external deps.
- `intech-tools:code-review` / `intech-tools:coding-standards` - the analysis
  flow and standards the fan-out sub-agents apply.
- `turbo-pr-review` - the interactive, human-confirmed sibling. Same posting
  mechanics; this is the unattended, idempotent version.
