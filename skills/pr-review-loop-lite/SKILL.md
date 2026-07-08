---
name: pr-review-loop-lite
description: Token-efficient variant of the autonomous, scheduled CDT PR-review loop. Same spot / group / review / share spine and the same hard rules as `pr-review-loop`, but replaces the per-PR `intech-tools:code-review` specialist fan-out with a single grounded review pass per PR - one Sonnet agent that loads the coding standards once and reviews all dimensions (bugs, silent failures, test gaps, type design, comment accuracy, scope) in one context. Posts the same neutral top-level verdict plus inline comments, uses the SAME reviewed-at marker as `pr-review-loop` (so the two are interchangeable and idempotent against each other), and ALWAYS defers approval and merge to a human. Use when a scheduled routine fires it, or when the user says "run the lite PR review loop", "do the cheap PR review pass", "/pr-review-loop-lite". Distinct from `pr-review-loop` (heavier, specialist fan-out per PR), `turbo-pr-review` (interactive, single PRs, confirms before posting), and `intech-tools:code-review` (heavy multi-agent single-PR audit). Repo set, team filter, marker detection and digest rendering are reused unchanged from `pr-review-loop/build.py`; comment voice from `pr-review-loop/references/comment-voice.md`.
---

# PR review loop (lite)

A leaner sibling of [`pr-review-loop`](../pr-review-loop/SKILL.md). Same job -
find the CDT PRs needing eyes, group related ones, review each at a consistent
bar, post comments, leave the approve/merge call to a human - and the same
output digest. The one difference is the **review mechanic**: instead of running
`intech-tools:code-review` and fanning out a panel of specialist sub-agents per
PR, lite runs **one grounded review pass per PR** in a single sub-agent context.

Why: on real runs the specialist fan-out is where nearly all the tokens go, and
most of that is overhead - each specialist reloads the coding standards, the
diff, and the PR metadata into its own context and does a full pass, then its
30-140k-token completion escalates to the orchestrator under this harness (see
`pr-review-loop`'s cost-discipline section for the gory detail). A single
well-grounded call that checks the same dimensions in one context captures the
large majority of the findings at a fraction of the cost. This skill trades some
review depth for a big token saving; reach for `pr-review-loop` when you
specifically want the deeper, adversarial specialist pass on a high-stakes batch.

Because lite reuses the base loop's `build.py` and its `reviewed-at` marker, the
two loops are **interchangeable on the same PRs**: whichever runs, a PR whose
head already carries the marker is skipped by both. Do not run both over the same
backlog in one window - pick one.

## Hard rules (identical to `pr-review-loop` - non-negotiable, restated here so an unattended run never has to dereference another file for safety)

1. **Never approve, request-changes, or merge.** Every posted review is
   `event=COMMENT`. The verdict is advisory; a human approves. Branch
   protection is the backstop.
2. **Defer business logic.** If correctness hinges on domain intent not legible
   from the code, don't guess - verdict `Needs Judgment`, name the lines.
3. **Idempotent.** Never review the same PR at the same head commit twice. The
   marker is shared with `pr-review-loop`, so a PR either loop already reviewed
   at the current head is skipped.
4. **Fail loud.** Unreachable repo, sub-agent error, budget trip - all go in the
   run summary. A silent skip looks like "nothing to review".
5. **No version-bump / breaking-change notes (development phase).** No SemVer-
   MAJOR recommendations, no `feat!:` / `BREAKING CHANGE:` framing, no "this
   should bump major" notes, no breaking-change merge-order notes. A change that
   genuinely breaks an in-repo caller is a normal correctness finding (raise it
   as such); the *versioning* recommendation never appears.

## Shadow mode (default)

Until `PR_REVIEW_LOOP_LIVE=1` is set, do the full review but write drafts to
`C:\tmp\pr-review-loop\<date>\<repo>-<n>-lite.md` instead of posting, and print
the digest. Default OFF.

## Process

Steps 1, 2, 6, 7 are mechanically identical to `pr-review-loop` and reuse the
same `build.py`. Step 3 is the change. Steps 4-5 are the same posting discipline,
restated because the anchor-validation rule is safety-critical.

### 1. Find what to review

Identical to the base loop. From the base skill's directory:

```
python ../pr-review-loop/build.py --actionable
```

Returns JSON of the PRs needing review this run - new PRs, or PRs with commits
past the most recent review (loop or human) sitting on them. A current human
review keeps its human attribution and is left alone until the author pushes past
it. (Run the command from wherever `build.py` lives; the path above assumes the
lite skill dir is a sibling of `pr-review-loop`.)

### 2. Cluster

Identical to the base loop. Group PRs reviewed together by linked ticket - parse
the branch name first (`CDT-NNN` / `INTECH-NNN`), which is free. Beyond the
ticket, use the Atlassian (Jira) connector to read ticket bodies for shared
contracts or explicit cross-PR dependencies. Cross-repo PRs for one ticket
cluster together; unrelated PRs review independently. If the connector is
unavailable, proceed on branch-name clustering and note it in the run summary -
do not fail the run.

### 3. Review - one grounded single-pass agent per PR (THE CHANGE)

**No `intech-tools:code-review`, no specialist fan-out.** Dispatch one review
sub-agent per PR (a cluster of related PRs can share one agent that reviews each
PR's own diff sequentially in the shared context - it loads the standards and
ticket context once and reuses them, which is a further saving). Each sub-agent,
in a single pass:

1. **Loads the Intech coding standards once.** Invoke the
   `intech-tools:coding-standards` skill (or read its reference docs) a single
   time at the start, so the review is grounded in the same standards the base
   loop cites - this grounding is not optional, it is what makes the pass a Curve
   review rather than a generic diff read. Cite the specific rule when a finding
   rests on one.
2. **Works diff-first - no checkout.** Fetch the combined diff with
   `gh pr diff <n>` (NOT `--patch` - that repeats files per-commit and gives
   wrong line numbers). Pull surrounding context on demand with
   `gh api repos/curveanalytics/<repo>/contents/<path>?ref=<head-oid>` for the
   handful of files where the diff alone is not enough to judge correctness.
   Lite deliberately does **not** `gh pr checkout`: diff + on-demand file fetches
   cover a single-pass review, and avoiding the working tree means the clone-
   collision problem the base loop has to manage simply does not arise. If a
   finding genuinely needs the code run (rare), that is the signal to escalate the
   PR to the base loop, not to clone here.
3. **Reviews all dimensions in one pass** - the union of what the base loop's
   specialists cover, applied by one reasoner instead of N:
   - **Correctness / bugs** (the `code-reviewer` lens): logic errors, off-by-one,
     wrong conditionals, mishandled edge cases, broken in-repo callers.
   - **Silent failures** (the `silent-failure-hunter` lens): swallowed
     exceptions, broad `except`, fallbacks that hide errors, ignored return
     codes. Weight this - it is where real defects hide and it is cheap to check
     in the same pass.
   - **Test coverage** (the `pr-test-analyzer` lens) - only when application or
     test code changed: are the new/changed paths covered, are the tests
     meaningful.
   - **Type design** (the `type-design-analyzer` lens) - only when types changed
     (Pydantic models, dataclasses, TS interfaces, classes): are invariants
     expressed and encapsulated.
   - **Comment / docstring accuracy** (the `comment-analyzer` lens) - only when
     comments or docstrings changed: do they match the code.
   - **Scope** (the `jira-scope-checker` lens) - on a ticket-prefixed branch:
     does the diff match the ticket's intent; flag scope creep or miss. If the
     Jira connector is unavailable, skip and note it.
   Do NOT run a breaking-change / SemVer analysis (Hard Rule 5).

**No git-history survey - that is the base loop's job.** Lite does not blame or
`git log` the repo. Its unique output (spotting a regression of a previously-
fixed bug) is low-yield on a pre-1.0 codebase with thin fix-history, and bounding
history exploration is unreliable - the `git-history-reviewer` specialist
"routinely 200-380k tokens" precisely because the model keeps pulling more
context, which is the exact blow-up lite exists to avoid. The *other* half of what
that specialist gives - recurring review points on the same files - is already
covered for free by the prior-thread ingest below. So there is no history escape
hatch in lite: when you actually want regression-hunting on a batch, run the base
loop (`pr-review-loop`), which is what its history specialist is for.

**Ingest replies to prior comments - do not re-raise settled points.** On any PR
the loop has reviewed before (`reviewed_before: true`), fetch the full threaded
conversation via `gh api repos/curveanalytics/<repo>/pulls/<n>/comments` (this
returns author replies to the loop's own review comments, not just top-level
reviews) and feed it to the review. This is cheap and mandatory - it is also what
covers the recurring-review-point value that the base loop's history specialist
provides. A point the
author has rebutted with a concrete reason is **settled**: drop it. Re-raise only
with genuinely new evidence, and engage the rebuttal explicitly. This is sharpest
when a finding came from `coding-standards` and the author has explained the
cited module/API does not exist in the *pinned* dependency - the author's ground
truth wins, do not re-raise.

**Model tiering.** The review sub-agent runs on **Sonnet** - a reviewer is the
wrong place to economise on the model tier, and lite already gets its saving from
cutting the fan-out, not from a weaker model. The orchestrator (this session)
also runs on **Sonnet**; schedule the cron on Sonnet. Reach for Opus only on a
supervised run where you want deeper synthesis.

**Cost note (why lite is cheap).** There are no grandchild specialist
sub-agents, so the harness escalation that dominates the base loop's cost simply
does not happen - each PR produces exactly one sub-agent completion the
orchestrator reads. No resume-to-consolidate dance, no ignoring grandchild
notifications. Bound concurrency to ~5-6 review agents in flight so you don't
spawn dozens at once; the rest queue and drain. Do NOT cap the number of PRs -
the team ships ~10/day and the loop must clear them all; lite makes each PR cheap
instead.

### 4. Assign a verdict and compose

Identical to the base loop. Each PR gets exactly one verdict:

- `Looks good` - no blocking findings; needs a human approve.
- `Minor comments` - only nits; approvable as-is.
- `Needs Changes` - a real bug or blocking concern; author's court.
- `Needs Judgment` - correctness hinges on domain/business logic the code
  doesn't make legible; named lines left for a human.

**Staged and stacked PRs are graded on their own diff, not on what's missing
downstream.** An unmerged dependency or a deferred caller is a merge-order note
in the body, not `Needs Changes`. Reserve `Needs Changes` for a real defect in
the code under review.

Compose the top-level comment + inline comments per
[`../pr-review-loop/references/comment-voice.md`](../pr-review-loop/references/comment-voice.md)
(neutral voice, no em dashes, British English). The top-level body MUST end with
the **same** marker the base loop uses - it drives idempotency and attribution:

```
<!-- pr-review-loop: reviewed-at=<head-oid> -->
```

**Validate every inline anchor against the diff before posting - sub-agent line
numbers are not trustworthy.** The reviews API is **atomic**: one unresolvable
anchor 422s the entire review, taking every other comment with it. Before
building the `comments` array, parse the combined `gh pr diff <n>` hunks and map
each finding to a real right-side (added/context) line by **matching the code it
refers to**, not the number the model guessed. A line absent from every hunk is
not a valid anchor - relocate it to the nearest in-hunk line or fold the finding
into the top-level body. Post only once the whole array is known to resolve.

**Never probe-post.** Resolve line numbers by parsing the diff text offline -
never post a throwaway "test" review to a live PR to find where a line lands.
This rule and the offline-anchor rule MUST be in every posting sub-agent's brief.

### 5. Post (live) or write (shadow)

- **Shadow:** write each review to
  `C:\tmp\pr-review-loop\<date>\<repo>-<n>-lite.md`.
- **Live** (`PR_REVIEW_LOOP_LIVE=1`): one review per PR via
  `gh api -X POST repos/curveanalytics/<repo>/pulls/<n>/reviews` with
  `event=COMMENT`, `commit_id` (head OID), `body` (top-level + marker), and
  `comments` (inline array, anchors validated per step 4). Build the JSON payload,
  write it to a temp file, validate it is well-formed JSON, then pass via
  `--input`. Note: passing `--input` supplies the raw body, so also pass
  `-f event=COMMENT` explicitly; if a review still lands as `state: PENDING`,
  submit it via `POST .../reviews/{id}/events -f event=COMMENT`. Confirm each
  review reads back as `state: COMMENTED`. A 422 should be rare once anchors are
  pre-validated; if one occurs, move the comment to the nearest in-hunk line and
  retry once, else fold it into the top-level body. Never silently lose a finding.

### 6. Render the digest

Identical to the base loop. Write a verdicts map -
`{"<repo>#<n>": {"verdict": "...", "reviewer": "@claude", "note": "..."}, ...}` -
covering every PR you reviewed, then:

```
python ../pr-review-loop/build.py --render verdicts.json
```

The script fetches live state, applies reviewer attribution, classifies into the
four sections, adds the age dots, and prints the digest. Attribution uses
`@claude` (the marker is shared, so the digest does not distinguish lite from the
base loop - both read as an automated `@claude` review, which is intended). On
Windows the render emits emoji, so run it with `PYTHONIOENCODING=utf-8` (or pipe
to a UTF-8 file) to avoid a `charmap` encode error. This output supersedes
`cdt-daily-pr-digest`.

Always print a run summary too (shadow or live): reviewed, skipped, deferred,
errors - fail loud. Include a one-line note confirming the single-pass review ran
grounded in `coding-standards` for every PR; a PR whose sub-agent did not report
loading the standards is **unverified** - flag it and re-run it rather than
counting it among the reviewed.

### 7. Clean up

Lite is diff-first and creates no clones, so there is normally nothing to remove
under `C:\tmp\pr-review-loop\clones\`. Clear any stray temp payload files you
wrote (the review JSON payloads). Leave the shadow drafts under
`C:\tmp\pr-review-loop\<date>\` in place. If anything can't be removed (file
lock), record it in the run summary rather than failing the run.

## Anti-patterns

- Falling back to `intech-tools:code-review` or spawning specialist sub-agents -
  that is the base loop; lite is a single grounded pass by design.
- Skipping the `coding-standards` grounding to "save tokens" - the grounding is
  the point; an ungrounded diff read is not a Curve review.
- Running any git-history / blame survey - lite has no history step by design;
  use the base loop when you want regression-hunting.
- Running `gh pr checkout` - lite is diff-first; a finding that needs the code run
  is the signal to escalate the PR to the base loop.
- Posting without the shared `reviewed-at` marker - breaks idempotency and lets
  the base loop re-review the same head.
- Running both loops over the same backlog in one window.
- Re-reviewing a PR whose head OID already matches the marker.
- Validating anchors against `gh pr diff <n> --patch` (per-commit, wrong line
  numbers) instead of the combined `gh pr diff <n>`.
- Probe-posting a throwaway review to a live PR to find a line.
- APPROVE / REQUEST_CHANGES / merge. Never.
- Guessing on business logic instead of `Needs Judgment`.
- Putting review content in the digest - it is a status summary; detail lives in
  the posted review, reached via the PR link.
- Silent skips or swallowed errors.
- Reviewing draft or release-bot PRs (`build.py` filters these).

## Scope

The token-efficient, single-pass version of the scheduled review loop. NOT the
specialist-fan-out version (`pr-review-loop`), interactive walkthroughs
(`turbo-pr-review`), multi-agent deep audits (`intech-tools:code-review`), or
anything that approves/merges. Validate it against `pr-review-loop` on a shared
set of PRs - diff what the single pass misses versus the fan-out - before letting
it become the default scheduled loop.

## References

- [`../pr-review-loop/build.py`](../pr-review-loop/build.py) - reused unchanged:
  repo set, team filter, review-state handling, marker detection, `--actionable`
  and `--render`.
- [`../pr-review-loop/references/comment-voice.md`](../pr-review-loop/references/comment-voice.md) -
  reused unchanged: neutral comment voice and top-level format.
- [`../pr-review-loop/SKILL.md`](../pr-review-loop/SKILL.md) - the heavier sibling;
  read its cost-discipline section for the fan-out behaviour lite removes.
- `intech-tools:coding-standards` - the standards the single pass grounds in.
