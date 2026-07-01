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
5. **No version-bump / breaking-change notes (development phase).** The CDT
   stack is pre-1.0 and deliberately does NOT cut major versions yet. Drop
   `breaking-change-detector`'s output entirely from posted reviews: no
   SemVer-MAJOR recommendations, no `feat!:` / `BREAKING CHANGE:` footer
   suggestions, no "this should bump major" framing, and no breaking-change
   merge-order notes. If a change genuinely breaks an in-repo caller that is a
   normal correctness finding (raise it as such); the *versioning* recommendation
   never appears. This gate applies in the cluster brief and at synthesis.

## Shadow mode (V1 default)

Until `PR_REVIEW_LOOP_LIVE=1` is set, do the full review but write drafts to
`C:\tmp\pr-review-loop\<date>\<repo>-<n>.md` instead of posting, and print the
digest. Lets the verifier be validated on real PRs before posting. Default OFF.

## Process

### 1. Find what to review

`python build.py --actionable` returns JSON of the PRs needing review this run -
new PRs, or PRs with new commits since the loop's last `reviewed-at` marker.
Two classes are skipped here: PRs unchanged since the loop's last review (the
marker is the memory; no external store), and PRs a human has already reviewed.
The loop is the **first-pass reviewer** - it never reviews over a human. A
human-reviewed PR keeps its human attribution in the digest (`reviewed: @<human>`
or `approved: @<human>`), and the loop leaves it alone.

### 2. Cluster

Group PRs reviewed together by linked ticket - parse the branch name first
(`CDT-NNN` / `INTECH-NNN`), which is free. Beyond the ticket, use the Atlassian
(Jira) connector to read ticket bodies for related work, shared contracts, or
explicit cross-PR dependencies. Cross-repo PRs for one ticket cluster together;
unrelated PRs review independently.

### 3. Review - one code-review per cluster, two-model

**Fan out per cluster, not per PR.** The unit of review is the cluster from
step 2, so the number of reviews equals the number of clusters - related PRs
(shared ticket / contract / dependency) are reviewed together for the cross-PR
context, not as N isolated passes.

**Each cluster runs `intech-tools:code-review`.** This is non-negotiable: the
review must be grounded in `intech-tools:coding-standards` via that skill's
citation gate. A generic diff pass that skips the standards does not conform to
Curve review and is not acceptable - using the real skill is the whole point.

**Gate the specialist set by what the diff touches - and by cost.** `code-review`
already scopes several specialists to diff content - `comment-analyzer` only when
comments or docstrings change, `type-design-analyzer` only when types change,
`pr-test-analyzer` only when application or test code changes, `jira-scope-checker`
only on a ticket-prefixed branch. The cluster brief asks for the specialists the
diff warrants, not the full panel on every PR. Two specialists are cut from the
default set for cost reasons:

- **`breaking-change-detector` - do not run it.** Its sole output is SemVer /
  major-bump recommendations, which Hard Rule 5 suppresses in development phase.
  Running it spends ~30-45k tokens to produce output we drop. Instruct the
  cluster brief to skip it.
- **`git-history-reviewer` - run ONLY on `reviewed_before` PRs.** It is by far
  the most expensive specialist (it surveys ~20 commits + prior PRs, routinely
  200-380k tokens and 20-46 tool calls). Its value is catching regressions of
  previously-fixed bugs and recurring review comments - which only exist on a PR
  with prior loop/human history. On a first-pass PR (`reviewed_before: false`)
  there is nothing to regress against, so it is the worst cost-to-value finder in
  the set. Gate it to re-reviews.

The remaining core finders (`code-reviewer`, `silent-failure-hunter`) run on
every cluster; the diff-gated specialists fire only when their trigger is present.
This trims agent count and the heaviest finders without lowering the bug bar on
new code - it skips work that is either suppressed (breaking-change) or has
nothing to look at (git-history on first-pass).

**Verify the skills actually fired - don't take the brief on trust.** Telling a
sub-agent to run `code-review` is not proof it did; a sub-agent can silently
fall back to a generic pass (or lack access to the plugin skills entirely), and
its transcript is purged after it returns, so there is no after-the-fact way to
check. So make each cluster sub-agent **report, in its returned output, the
exact skills and specialist agents it invoked** (e.g. `intech-tools:code-review`
plus the `silent-failure-hunter` / `type-design-analyzer` / ... it spawned). If
a cluster's report does not show `intech-tools:code-review` firing, treat that
cluster as **unverified**: do not report it as reviewed, flag it loudly in the
run summary (step 6), and re-run it before posting. This check is mandatory -
"instructed but unverified" is a silent skip wearing a verdict. The check is on
`code-review` itself, not the full panel: a specialist legitimately gated out by
the diff (no type change, so no `type-design-analyzer`) is expected, not a gap.

**Model tiering:** specialist sub-agents and the per-cluster `code-review`
runners stay on **Sonnet** (an earlier design tried Haiku; the saving didn't
justify the risk of a weaker tier missing real defects - a reviewer is the wrong
place to economise on bug detection). The loop's own orchestrator (the session
running this skill) should run on **Sonnet too**, not Opus. Earlier guidance kept
the orchestrator on Opus for clustering/synthesis, on the assumption per-run cost
was low - that assumption proved false: the orchestrator unavoidably absorbs the
specialist fan-out (see cost discipline below) and an Opus session bills that at
~5x a Sonnet one. The orchestrator's actual job - cluster by ticket, assign one
of four verdicts, defer anything genuinely hard to a human as `Needs Judgment` -
does not need Opus. So: **schedule the cron on Sonnet**; reach for an Opus
session only for a supervised run where you specifically want deeper synthesis.

**Cost discipline - the dominant cost is the fan-out reaching the Opus
orchestrator, and the cluster-agent layer does NOT reliably contain it.** Each
cluster runs `code-review`, which fans out its specialists as background-async
sub-agents. The intended design is that each cluster agent awaits and consolidates
its specialists internally and returns *one* report, so the orchestrator only ever
reads N consolidated reports. **Observed reality (two runs): it does not work that
way.** The cluster agents stop early after spawning specialists, and the harness
routes the specialist (grandchild) completions - 30-140k tokens each - straight to
the top-level orchestrator. The 2026-06-29 run spent ~39% of a 5-hour budget this
way; the 2026-06-30 run hit ~60% of a usage limit for the same reason on a 10-PR
backlog. Treat this as a standing harness constraint, not a thing you can wish
away. So:

- **Never read or act on grandchild specialist notifications.** When one arrives,
  ignore its content entirely - it is noise the harness escalates. Acting on them
  is what burns the Opus context.
- **Resume each cluster agent once to get its consolidated JSON.** Because the
  cluster agents stop early without consolidating, the *only* reliable way to get
  the per-cluster report is to `SendMessage` the agent once with: "your specialists
  have completed; consolidate from the outputs in your context, do NOT re-spawn
  anything, return the JSON now." This is the opposite of the old "never resume"
  rule - that rule assumed containment that does not hold. One consolidation
  message per cluster, no polling beyond that.
- **The cost levers that fit a ~10-PR/day load are per-PR, not per-run.** Do NOT
  cap the number of PRs - the team ships ~10/day and the loop must clear them all.
  Make each PR cheap instead: (1) the lean specialist panel above (no
  `breaking-change-detector`, `git-history-reviewer` only on re-reviews) roughly
  halves the grandchildren each PR produces; (2) **run the loop's own session on a
  cheaper model.** The orchestrator's dominant cost is absorbing the fan-out that
  reaches it, and that absorption is billed at the session model's rate - so an
  Opus session is ~5x a Sonnet one for the *same* fan-out. The orchestrator's real
  decisions (clustering, verdict assignment, deferring business logic to humans)
  are well within Sonnet's range, and anything genuinely hard is handed to a human
  as `Needs Judgment` anyway. **Recommended: schedule the cron on Sonnet.** Reserve
  an Opus session only for a run you are supervising and specifically want deeper
  synthesis on. The proper structural fix - making `code-review`'s specialists
  consolidate in-tier instead of escalating to the session root - lives upstream
  in `intech-tools:code-review`, not here.

**Isolated clone per cluster - required, not deferred.** `code-review` runs
`gh pr checkout` and reads the working tree, so two clusters reviewing in
parallel against one clone race on the branch checkout. Each cluster must run in
its own fresh clone under `C:\tmp\pr-review-loop\clones\<repo>-<n>\` (a `git
worktree` off an existing checkout works too, but a fresh clone is simpler and
needs no local checkout to exist - the isolation is the point, not the
mechanism). If isolation isn't wired, **serialise the clusters** rather than
racing them - never fan out checkout-based reviews against a shared working
tree. Clear the clones at the end of the run (see step 6).

The review cross-references existing comments and does not re-raise a point
already made or contradict a human reviewer without new reasoning. For stacked
PRs, review only the incremental diff.

**Ingest replies to the loop's own prior comments - do not re-raise a point the
author has already answered.** On any PR the loop has reviewed before, the
author will have replied to the loop's earlier comments. Before composing, fetch
those threads in full - including the author's replies to the loop's own review
comments (`gh api repos/<owner>/<repo>/pulls/<n>/comments`, which returns the
threaded conversation, not just the top-level review) - and feed them to the
review sub-agents as required context. A point the author has rebutted with a
concrete reason is **settled**: drop it. Re-raise only if there is genuinely new
evidence the rebuttal is wrong, and if so, engage with the rebuttal explicitly
rather than restating the original comment. Re-stating a settled point as though
it were fresh is the most common failure of an unattended re-review and erodes
the author's trust in the loop. This is especially sharp when a finding came
from `coding-standards` and the author has explained that the cited
module/API/pattern does not exist in the *pinned* dependency (the reference
catalogue runs ahead of what is shipped): the author's ground truth wins - do
not re-raise.

**No per-run PR cap - review every actionable PR.** The team genuinely churns
~10 PRs/day, so a run handling 10+ actionable PRs is the normal load, not a
backlog to cap against. The answer to cost is making each PR cheap to review
(lean specialist panel above, cheap orchestrator below), never reviewing fewer of
them. Bound only the fan-out concurrency (~5-6 cluster agents in flight) so you
don't spawn dozens at once; the rest queue and drain. If a sub-agent errors,
record it and carry on - fail loud, never drop a PR silently.

### 4. Assign a verdict and compose

Each group gets exactly one verdict:

- `Looks good` - no blocking findings; needs a human approve.
- `Minor comments` - only nits; approvable as-is.
- `Needs Changes` - a real bug or blocking concern; author's court.
- `Needs Judgment` - correctness hinges on domain/business logic the code
  doesn't make legible; named lines left for a human. A deliberate hand-off,
  not a failure to review.

**Staged and stacked PRs are graded on their own diff, not on what's missing
downstream.** A PR that depends on an unmerged sibling, or that ships a unit
(an assembler, a model) deliberately wired by a follow-on PR, does NOT earn
`Needs Changes` for the absent caller or the not-yet-merged dependency - those
are sequencing facts, not defects in this diff. Flag them as a merge-order note
and grade only what this PR actually changes: if the only blocking finding is
"its dependency hasn't merged yet", the verdict is `Minor comments` with that
note, not `Needs Changes`. Reserve `Needs Changes` for a real defect in the
code under review (a bug, a security gap, a standards violation that bites
today). A finding that only bites *after* a sibling merges belongs in the body
as a pre-merge checklist item, not as the grade.

Compose the top-level comment + inline comments per
[`references/comment-voice.md`](references/comment-voice.md). The top-level body
MUST end with the marker `<!-- pr-review-loop: reviewed-at=<head-oid> -->` - it
drives idempotency (step 1) and attribution (step 6). Inline comments target a
`path:line` inside a diff hunk; lead with the verdict, group small stuff rather
than carpeting the PR.

**Sub-agent line numbers are not trustworthy - validate every anchor against
the diff before posting.** Observed in practice: the review agents routinely
cite line numbers that don't match the actual diff (off by hundreds of lines).
The reviews API is **atomic** - one unresolvable anchor 422s the *entire*
review, taking every other comment with it. So 422-recovery after the fact is
the wrong shape. Before composing the `comments` array, fetch the **combined**
diff (`gh pr diff <n>` - NOT `--patch`: that emits per-commit format-patch which
repeats each changed file once per commit and resets hunk line numbers, so the
numbers you compute will not match GitHub's `base...head` diff and the review
422s. `gh pr diff <n>` with no flag gives the single combined diff GitHub
actually uses). Parse the hunks, and map each finding to a real right-side
(added/context) line by **matching on the code it refers to**, not on the number
the agent guessed. A context line inside a hunk is a valid anchor; a line absent
from every hunk is not - drop or relocate it and fold the finding into the
top-level body rather than dropping it. Post only once the whole `comments`
array is known to resolve.

**Never probe-post.** Resolve line numbers by parsing the diff text offline -
never post a throwaway "test" review to the live PR to discover where a line
lands. (This happened once in an early run and left junk reviews on a
teammate's PR that could not be deleted.) When the orchestrator fans out the
posting work to sub-agents, this rule and the offline-anchor rule above MUST be
in each sub-agent's brief - they post to real PRs and there is no one watching
to clean up after an unattended run.

### 5. Post (live) or write (shadow)

- **Shadow:** write each review to `C:\tmp\pr-review-loop\<date>\<repo>-<n>.md`.
- **Live** (`PR_REVIEW_LOOP_LIVE=1`): post one review per PR via
  `gh api -X POST repos/<owner>/<repo>/pulls/<n>/reviews` with `event=COMMENT`,
  `commit_id` (head OID), `body` (top-level + marker), and `comments` (inline
  array, anchors validated per the rule above). A 422 should be rare once
  anchors are pre-validated; if one still occurs, move the comment to the
  nearest in-hunk line and retry once, else fold it into the top-level body.
  Never silently lose a finding.

### 6. Render the digest

Write a verdicts map - `{"<repo>#<n>": {"verdict": "...", "reviewer": "@claude",
"note": "re-reviewed"}, ...}` - covering every PR you reviewed, then
`python build.py --render verdicts.json`. The script fetches live state, applies
the reviewer-attribution rule (this run → `@claude`; approved/merged → the human
actor; untouched-but-previously-reviewed → `@claude` if the latest review
carries the marker, else the human who left it), classifies into the four
sections, and prints the digest. Bucketing rule: **any human review hands the
PR to the author** - a PR a human has reviewed (even a `COMMENTED` review, not
just a formal `CHANGES_REQUESTED`) lands in "Needs follow-up - waiting on the
author", since the team reviews with comments rather than the formal states.
"Awaiting human review" therefore holds only loop-reviewed (`@claude`) and
genuinely untouched PRs; approved PRs go to their own section. **The digest is a status summary, not a review
- no findings or headlines, just the PR title (linked), author, `reviewed: @x`,
and the verdict tag.** Each open PR also carries an age dot (🟢 <3d · 🟡 3-6d ·
🔴 7d+ since opened) so stale PRs that need merging or closing are scannable;
the thresholds live in `build.py` (`AGE_GREEN_LT` / `AGE_AMBER_LT`). The PR
title is the only link; there's no separate `[review]` link (the PR reference
already points there). This output supersedes `cdt-daily-pr-digest`.

Always print a run summary too (shadow or live): reviewed, skipped, deferred,
errors - fail loud. Include a **skills-invoked** line per the verification rule
in step 3: confirm `intech-tools:code-review` fired for every cluster reviewed,
and list any cluster whose sub-agent did not report it as **unverified** rather
than counting it among the reviewed.

### 7. Clean up

Remove the per-cluster clones once the digest is rendered:
`Remove-Item -Recurse -Force C:\tmp\pr-review-loop\clones\*`. They are
throwaway checkouts, not state - the marker on each PR is the only memory the
loop keeps. Leave the shadow drafts under `C:\tmp\pr-review-loop\<date>\` in
place; they're the run's review artefact. If a clone can't be removed (file
lock), record it in the run summary rather than failing the run.

## Anti-patterns

- Posting without the `reviewed-at` marker - breaks idempotency and attribution.
- Re-reviewing a PR whose head OID matches the marker.
- Running the review on Opus instead of Sonnet sub-agents.
- Reading or acting on grandchild specialist notifications. They will reach the
  orchestrator under this harness - ignore their content; act only on each
  cluster agent's one consolidated JSON. Reading them was the dominant cost in
  both observed runs.
- Running `breaking-change-detector`, or posting any SemVer / major-bump note
  (Hard Rule 5 - development phase).
- Running `git-history-reviewer` on a first-pass (`reviewed_before: false`) PR -
  it has nothing to regress against and is the most expensive finder.
- Validating anchors against `gh pr diff <n> --patch` - the per-commit format
  repeats files and gives wrong line numbers; use the combined `gh pr diff <n>`.
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
`issei-plugin`; promote to `intech-tools` before the team relies on it (the
review logic already composes `intech-tools:code-review` per step 3, so the move
is mostly relocation + distribution, not a redesign).

## References

- [`build.py`](build.py) - runnable companion: repo set, team filter, GitHub
  review-state handling, marker detection, `--actionable` and `--render` modes.
- [`references/comment-voice.md`](references/comment-voice.md) - neutral comment
  voice and the top-level comment format. Self-contained; no external deps.
- `intech-tools:code-review` / `intech-tools:coding-standards` - the analysis
  flow and standards the fan-out sub-agents apply.
- `turbo-pr-review` - the interactive, human-confirmed sibling. Same posting
  mechanics; this is the unattended, idempotent version.
