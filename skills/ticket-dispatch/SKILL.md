---
name: ticket-dispatch
description: Take a Jira ticket from key to a reviewable draft PR - the execution loop. Ground the ticket with the context-router, draft an implementation spec and get Issei's sign-off, then implement it in an isolated git worktree, verify with the repo's tests + ruff, and open a DRAFT PR for Issei to review and merge. Use when Issei says "dispatch CDT-nnn", "work on CDT-nnn", "pick up <ticket>", "implement this ticket", "start on CDT-nnn", "/ticket-dispatch", or hands over a ticket to build. Two hard human gates: Issei approves the spec before any code, and Issei reviews + merges the PR (never auto-merge, never mark ready-for-review without asking). Automates the work, not a misrepresentation of it - the PR reflects real, tested changes Issei reviews with his own judgement. Distinct from turbo-pr-review / pr-review-loop (reviewing others' PRs) and context-assemble (grounding only, no build).
---

# Ticket dispatch

The execution loop: a Jira ticket → a reviewable draft PR, with Issei on the two
decisions that matter (the spec, and the merge) and the machine doing the mechanical
production in between. This is the biggest lever in Project Autopilot and the one
that most needs its gates - so the gates are non-negotiable, not conveniences.

Scripts live in `C:\Users\IsseiKuzuki\Claude\project-autopilot\scripts\`. CDT repos
are cloned flat at `C:\Users\IsseiKuzuki\<repo>` under the `curveanalytics` org on the
`Issei-curve` gh account - no account switch (unlike the personal repos).

## Step 0 - Pre-flight

- `gh auth status` shows `Issei-curve` active. If not, `gh auth switch --user Issei-curve`.
- The target repo has a local clone at `C:\Users\IsseiKuzuki\<repo>`. If not, stop and
  tell Issei to clone it - don't guess a path.

## Step 1 - Ground the ticket (context-router)

```
python context_assemble.py "<TICKET-KEY>" --markdown
```

Then deep-read what matters: the ticket itself (`getJiraIssue` via the Atlassian MCP -
full description, acceptance criteria, comments), the closest existing code + the most
relevant prior PR from the GitHub section, and any design page from Confluence. This is
the `context-assemble` flow; lean on it rather than re-deriving. Identify the **target
repo** from the code hits (which repo does the change actually live in?).

## Step 2 - Draft the spec, then STOP (GATE 1)

Write a short implementation spec Issei can approve at a glance:

- **Goal** - what the ticket asks, in one or two plain sentences.
- **Target** - repo + the specific files/modules that change.
- **Approach** - how, referencing the existing patterns found in Step 1 (match the
  codebase, don't invent). Call out the one or two real decisions.
- **Changes** - a concrete bullet list of what will be added/edited.
- **Tests** - what proves it works (new tests + which existing suites must stay green).
- **Risks / out-of-scope** - what this deliberately does NOT touch; anything uncertain.

**Present it and wait.** No worktree, no code until Issei approves or amends. If the
ticket is under-specified or the approach has a genuine fork, surface that here - a bad
spec is the expensive failure, not a slow one. If scope looks wrong for the ticket,
say so (this is the same instinct as `jira-scope-checker`).

## Step 3 - Isolate a worktree

Only after sign-off:

```
python dispatch.py start <TICKET-KEY> <repo> --slug "<short-desc>"
```

Creates an isolated `git worktree` on a `<KEY>-<slug>` branch off a freshly-fetched
`origin/main`, at `C:\Users\IsseiKuzuki\.autopilot-worktrees\<repo>-<KEY>`. Issei's own
checkouts are never touched. Use the returned path as the working dir for Step 4.

## Step 4 - Implement to the approved spec

Work in the worktree, to the spec - not beyond it (surgical changes; match the repo's
conventions, read neighbouring code first). For a self-contained change, do it inline.
For a larger one, dispatch a subagent (the Agent tool) with the worktree path + the
approved spec as its brief. Commit in logical steps with Conventional-Commit messages
(`feat:`/`fix:`/... per the Intech conventions). Do not expand scope mid-build - if you
discover the spec was wrong, stop and re-confirm with Issei (back to Gate 1), don't
silently redesign.

## Step 5 - Verify (honestly)

Run the repo's real checks in the worktree - `ruff check .`, `ruff format --check .`,
and `pytest` (or the repo's documented test command). Report pass/fail **as it is**:
a red suite blocks the PR. "Tests pass" is only true if they all did; if you skipped
any, say which and why. Fix and re-run, or surface the failure - never paper over it.

## Step 6 - Draft PR, then STOP (GATE 2)

```
python dispatch.py open-pr <worktree-path>          # prints the plan (safe default)
python dispatch.py open-pr <worktree-path> --yes    # push + create the DRAFT PR
```

Run the dry plan first, show Issei the PR it will create (title + branch + base), then
`--yes` to push and open it as a **draft**. Write the PR body in Issei's voice
(compose `issei-voice`): what changed, why, how it was verified, and a link to the
ticket. Then hand back:

> Draft PR opened: <url>. Tests: <result>. Review it and merge when happy - I won't.

**Never** `gh pr merge`, never `--ready`/mark-ready, never push to `main`. Merging and
flipping to ready-for-review are Issei's, by hand. `dispatch.py` has no merge path by
design.

## After merge - cleanup

Once Issei confirms the PR is merged: `python dispatch.py cleanup <worktree-path>`
removes the worktree (the branch ref is kept until Issei is sure). Offer it; don't
assume the merge happened.

## Guardrails (the whole point)

- **Two gates, always:** spec approved before code; Issei reviews + merges. No
  exceptions, even for a "trivial" ticket.
- **Draft PRs only.** Nothing team-visible-as-ready happens without Issei.
- **Real work, honestly reported.** The change is genuine and tested; the PR describes
  what actually happened. This automates the production, never a misrepresentation of
  it - if quality isn't there, the PR says so rather than hiding it.
- **Team boundary.** Ground from team sources; if the context bundle surfaced a vault
  hit, that's personal - never cite it into the PR or ticket.

## Not for

- Reviewing someone else's PR - that's `turbo-pr-review` / `pr-review-loop`.
- Just gathering context without building - that's `context-assemble`.
- Merging, deploying, or releasing - out of scope by design.
- Overnight / unattended dispatch - a later phase; today's loop is in-session with Issei.
