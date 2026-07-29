---
name: my-open-prs
description: A private status table of every open PR Issei has authored across curveanalytics, drafts included - grouped by the part of the system they touch and by dependency chain, with the linked Jira ticket (key, summary and status), a one-line what-it-does, the current state (still being written / awaiting first review / automated pass only / human-reviewed and needs changes / approved and mergeable / blocked), and the single next action. Use when the user asks "what PRs do I have open", "where am I with my PRs", "my PR queue / board / status", "what am I waiting on", "what needs merging", "have I lost track of anything", "which of mine need chasing", or "/my-open-prs". Read-only - never comments, approves, merges or pushes. Distinct from `cdt-daily-pr-digest` and `pr-review-loop` (whole team, Teams-facing), `share-prs` (turns a batch into a message for a reviewer), and `understand-prs` (reviewing other people's PRs).
---

# My open PRs

Issei raises PRs faster than he can hold them in his head, across four or five
repos, often in dependency chains where one has to be released before the others
can pin to it. This produces one table so nothing is lost: what's open, what it's
waiting on, and what he does next.

Output is a markdown table in chat. This one is **not** for Teams - it's his own
view, so tables are fine and preferred. When he wants something sendable, that's
`share-prs`.

## Process

### 1. Discover

```bash
unset GITHUB_TOKEN && gh auth switch --user Issei-curve
gh search prs --owner curveanalytics --author @me --state open \
  --limit 60 --json number,title,repository,isDraft,url,createdAt,updatedAt
```

One call, all repos, drafts included. **Drafts are in scope** - a draft that's
been sitting for a week is exactly the thing that gets lost.

Filter out release-please bot PRs (`chore(main): release`) if any are attributed
to his account. If the search returns nothing, check `gh auth status` before
concluding the queue is empty - a wrong active account looks identical to zero
PRs.

For personal projects (`fpl-platform` and similar) run the same call against the
`ikuzuki` account and keep the results in a separate table. Never merge personal
and Curve rows - the boundary is hard.

### 2. Enrich per PR

Batched in one tool message:

```bash
gh pr view <n> --repo curveanalytics/<repo> \
  --json number,title,body,headRefName,isDraft,url,additions,deletions,files,reviewDecision,reviews,comments,mergeable,mergeStateStatus,statusCheckRollup
```

### 3. Resolve the ticket

Parse `CDT-NNN` / `INTECH-NNN` from `headRefName`, falling back to title then
body. Fetch the tickets for their summary and status - the PR-versus-ticket
mismatch is a real signal (an approved PR against a ticket still in Backlog, or a
ticket in Done with the PR still open). Link as
`https://curve-analytics.atlassian.net/browse/CDT-NNN`.

Fetch them in **one** `searchJiraIssuesUsingJql` call with a key-set filter
(`key in (CDT-544, CDT-645, CDT-637)`) rather than one `getJiraIssue` per ticket:
`getJiraIssue` returns the entire description even when you ask for two fields, so
per-ticket calls burn a lot of context for a summary and a status.

Two Atlassian MCP servers are configured and the one under `intech-tools` times
out at 300s fairly often. When it does, fall back to the other configured
Atlassian server - its `cloudId` has to be discovered via
`getAccessibleAtlassianResources`, not passed as the site hostname. If both are
unreachable, say so in the output and mark the ticket statuses as unverified
rather than silently inferring them from branch names.

A PR with no resolvable ticket goes in the table with `-` in the ticket column
and gets called out below it. Untracked work is the point of noticing.

### 4. Classify state

**Work out human versus automated by the marker, not by the author.**
`pr-review-loop` posts its reviews **under Issei's own GitHub account**, so a
review by `Issei-curve` is either the bot or him and only the body tells you
which: `<!-- pr-review-loop: reviewed-at=<oid> -->` means automated. Filtering on
"author is Issei" alone therefore throws away the bot's passes and his own inline
replies together, and mislabels the PR as unreviewed. Take the full `reviews`
array (`latestReviews` gets cleared once the author replies inline), tag each
entry automated or human by marker, and drop only his unmarkered `COMMENTED`
self-replies.

Before labelling anything red, **find out why it's red**: `gh pr checks <n>` and
`gh run view <id> --log-failed` on the failing run. "CI failing" and "CI failing
on a stale lock that a regen fixes" lead to completely different next actions, and
the second is common on a chain waiting for a dependency release. Also check the
run's age - a failure from before this morning's push is often already stale.

`mergeable` and `mergeStateStatus` come back `UNKNOWN` while GitHub recomputes,
so a single fetch can mislead. Re-query once if you see `UNKNOWN` before deciding
a PR is blocked.

Then, first match wins - **blocked outranks red**, because a PR that is red
*because* it's waiting on a release is blocked, and calling it "CI failing"
understates it and points the next action at the wrong thing:

| State | Condition |
|---|---|
| `Scratch - not for merge` | draft whose title or body marks it TEMP / DO NOT MERGE / spike (above `Drafting` deliberately - it's the more specific match, and a scratch PR needs no next action beyond "close it or keep ignoring it") |
| `Drafting` | `isDraft` true |
| `Blocked` | `mergeStateStatus` is `DIRTY` (conflicts) or `BEHIND`, or the PR body / a chain sibling needs another PR or a release first - including when that dependency is what's making CI red |
| `CI failing` | `statusCheckRollup` has a failure with no upstream dependency behind it; say in Next whether it's stale and what fixes it |
| `Approved - merge it` | `reviewDecision == APPROVED` and nothing above matched |
| `Changes requested` | latest human review is `CHANGES_REQUESTED`, or has open unaddressed threads |
| `Human reviewed - my turn` | human review exists, no commits since it |
| `Awaiting re-review` | human review exists, commits pushed since it |
| `Bot pass only` | automated review only, no human has looked |
| `Awaiting first review` | no reviews at all |

`mergeStateStatus == BLOCKED` on its own usually means pending checks or branch
protection rather than a real blocker - treat it as pending and re-query.

### 5. Group

Two axes, applied in order:

**Dependency chain first.** PRs on the same ticket, or with explicit cross-PR
dependencies, form one group - ordered by merge order, with the order stated. A
chain where the head is unmerged and the tail shows conflicts is the single most
useful thing this table surfaces.

**Then system area** for whatever's left. Group by what it touches rather than
by repo, since one change often spans repos: dispatch and scheduling, capacity
and rate limiting, ingestion, serving and metrics, ClickHouse schema, entity
resolution, observability and infrastructure, CI and tooling, frontend and BFF.
Name the group by the area, and note the repos it spans.

### 6. Render

Per group, a heading line naming the area or chain (with merge order if it's a
chain), then:

| PR | Ticket | What it does | Reviewed by | State | Next |
|---|---|---|---|---|---|

- **PR** - `[repo #n](url)`, with `(draft)` appended where relevant.
- **Ticket** - `[CDT-NNN](url)` plus the Jira status in brackets when it
  disagrees with the PR state. `-` when untracked.
- **What it does** - one clause, plain English, outcome-shaped. Not the
  conventional-commit title. Strip `feat(scope):` prefixes.
- **Reviewed by** - `human (@adele-curve)`, `bot only`, or `none`. **This column
  is the point of step 4 and must appear** - the classification is worthless if it
  stays in your head. Because `pr-review-loop` posts as Issei, a table that just
  says "Approved" leaves him unable to tell a teammate's approval from an automated
  pass under his own name, which is exactly the confusion this skill exists to
  remove. Where both have looked, name the human. Where an approval exists but was
  dismissed by a later push, say `human (@x), approval dismissed` rather than
  picking between `reviews` and `reviewDecision` and being wrong.

  Add one line under the tables saying how the split was determined - "human vs
  bot is by the `pr-review-loop` marker in the review body, since the loop posts
  under my own account". This is the surface where he is most likely to doubt the
  label, and an unexplained `bot only` on a PR he remembers being reviewed reads
  as a mistake rather than a finding.
- **State** - from the table above, verbatim.
- **Next** - the single next action and whose it is: "chase Adele", "answer the
  two open threads", "merge", "regen the lock to 0.54 and push", "finish and mark
  ready".

Open with a one-line count by state ("11 open: 2 mergeable, 3 awaiting first
review, 4 back with me, 1 draft, 1 blocked"). Close with a short flags section,
outside the tables, for: PRs with no ticket, drafts older than about five days,
anything with no activity for a week or more, chains whose head is stuck, and any
PR-versus-ticket status mismatch.

**Include the standing patterns, not just the per-PR facts.** A view across the
whole queue can see things no single row can - one teammate is the only human
reviewer across every open PR, three PRs are all waiting on the same unreleased
dependency, half the queue is blocked on one lock refresh. Those are the most
actionable observations the table produces and they vanish if you only report
row-by-row. One or two lines, in the flags section.

Then the bottom line - what he should actually do first. One or two sentences,
not a list.

Keep the whole thing tight: this is a glance-and-act view, so table cells are
clauses rather than sentences and the prose around them stays minimal. British
English, and no em dashes - use ` - ` instead, as everywhere else in his output.

## Self-check

- [ ] Drafts included, release-bot PRs excluded?
- [ ] Human versus automated decided by the **marker**, not the author login?
- [ ] Does the rendered table actually carry the `Reviewed by` column?
- [ ] Red PRs diagnosed (stale lock? real failure?) before being labelled?
- [ ] `Blocked` ranked above `CI failing` where a dependency is the cause?
- [ ] No em dashes anywhere?
- [ ] Every ticket link resolved, with its status, in one JQL call?
- [ ] Chains grouped with the merge order stated?
- [ ] Every row carrying a concrete next action with an owner?
- [ ] Personal-account PRs kept in a separate table, if fetched at all?
- [ ] Nothing written - no comment, approve, merge or push?

## Anti-patterns

- **Dropping drafts.** They're the ones that go missing.
- **Counting a `pr-review-loop` verdict as a review.** It isn't one.
- **Computing the bot-versus-human split and then not rendering it.** The column
  is the deliverable, not an intermediate.
- **Filtering reviews on "author is Issei".** The bot posts as him.
- **Labelling a PR `CI failing` without opening the failure.** Stale-lock red and
  broken-code red need different actions.
- **Trusting `latestReviews`**, a single `UNKNOWN` mergeability fetch, or counting
  his own inline replies as reviews.
- **Em dashes.**
- **Grouping by repo.** A chain spanning four repos is one piece of work.
- **A row with no next action.** If there's genuinely nothing to do, the state
  should say why.
- **Sending this anywhere.** It's a private view; `share-prs` produces the
  sendable version.
- **Mixing Curve and personal PRs in one table.**

## References

- `share-prs` - shares the discovery call; use it when the output should be a
  message to a reviewer.
- `understand-prs` - for the inbound direction, and for author-mode replies on
  threads this table flags as needing his turn.
- `cdt-daily-pr-digest` / `pr-review-loop` - the team-wide, Teams-facing view.
- `jira-board-hygiene` - the ticket-side counterpart when the mismatch flags
  point at board drift rather than PR work.
