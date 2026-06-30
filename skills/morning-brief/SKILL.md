---
name: morning-brief
description: Assemble Issei's day into one read - mid-flight work (working memory), PRs awaiting his review and re-review, his own open PRs with their state, in-progress Jira tickets, and a proposed deep-block plan. Use when Issei says "morning brief", "what's on today", "set me up for the day", "what should I focus on", "/morning-brief", or when a morning scheduled routine fires. Has a catch-up mode for leave-return - "I've been on AL, catch me up", "what did I miss" - that widens the lens to what shipped across the team while he was away. Forward-looking and private to Issei; distinct from standup-update (the backward-looking team artefact) and working-memory (single-task recall).
---

# Morning brief

Replace the six-tool morning gather (working state, PR queue, Jira, what-shipped)
with one read, and end on a proposed deep-block plan Issei approves or edits. The
gathering is deterministic (`brief.py`); your job is the judgement on top - what
to prioritise, what's blocked on others vs on him, what's gone stale - and the
plan. Display only; this proposes, it never acts.

The gatherer lives in the `project-autopilot` repo (stable path, same as the
working-memory scripts); this skill calls it, then layers Jira + any calendar +
synthesis on top.

## Two modes

- **Daily** (default) - "morning brief", "what's on today", "set me up".
- **Catch-up** - "I've been on AL, catch me up", "what did I miss". Infer the
  away-since date (ask if unclear) and pass `--merged-since YYYY-MM-DD` so the
  brief also shows what shipped across the team while he was out. This is the
  leave-return case the brief generalises to; widen the narration accordingly.

## 1. Gather (deterministic)

`brief.py` uses the *active* gh account, so check it first:

```bash
unset GITHUB_TOKEN
gh auth status        # if not Issei-curve: gh auth switch --user Issei-curve
```

Then, from `C:\Users\IsseiKuzuki\Claude\project-autopilot\scripts\`:

- Daily: `python brief.py`
- Catch-up: `python brief.py --merged-since 2026-06-23` (the away-since date)

It emits markdown: mid-flight work (newest-first working-state notes), **Awaiting
your review**, **Awaiting your re-review** (PRs where the head moved since Issei
last reviewed - the candidate for `turbo-pr-review`'s re-review mode), **Your open
PRs** with review state, and in catch-up mode **Shipped while you were away**. Use
`--json` instead if you want to manipulate the data before rendering. The script
reports which gh account it used in its header - if it says anything but
`Issei-curve`, the PR buckets are wrong; re-run after switching.

## 2. Add the tickets (Jira, via the Atlassian MCP)

`brief.py` deliberately skips Jira (it needs the MCP, which is Claude-only). The
cloudId for curve-analytics is `958db0ed-b775-4ed5-b4c4-e82d60a3feef`. Pull only
Issei's *active* tickets with `searchJiraIssuesUsingJql` - not the whole
not-Done set. `statusCategory != Done` returns ~28 issues, most of them
`READY FOR QA` (handed off, off his deep-block plate). What the brief wants is
what he's working or about to:

```
assignee = currentUser() AND status IN ("In Progress", "To Do", "READY FOR CODE REVIEW") ORDER BY updated DESC
```

Reliability, bitten in testing: **this search overflows the tool result every
time** - ~158k chars for the broad set, still ~54k even with
`responseContentFormat: "markdown"`, minimal `fields`
(`["summary","status","issuetype","updated"]`), and `maxResults: 20`, because the
MCP returns heavy ADF payloads regardless. So expect the overflow and use the
saved file: the error gives a path; extract a compact list with jq rather than
reading it raw:

```bash
jq -r '.issues.nodes[] | "\(.key) | \(.fields.status.name) | \(.fields.summary)"' <file>
```

Still pass the markdown + minimal-fields + low-maxResults options (they shrink the
file), but plan on the jq step.

Keep it to the handful that matter, and cross-reference against the working-state
notes and PR buckets: a ticket with a mid-flight note or an open PR is where the
day's momentum already is. `READY FOR QA` items are handed off - mention only if
one is relevant, don't list the pile.

## 3. Calendar (optional)

There is no local calendar feed today. If Issei pastes his agenda, fold the
meetings into the plan (they bound the deep block). Otherwise add one line -
"calendar not wired; paste today's meetings to fold them in" - and move on. Don't
fabricate a schedule.

## 4. Synthesise the brief

Render to chat in Issei's voice (terse, British, no em-dash - use ` - `, no
corporate filler, no preamble). Don't just reprint `brief.py`; add the judgement.
Shape:

```
**Morning brief - <date>**

Where you left off
- <1-2 lines per active thread, from working state + its ticket/PR>

Needs you today
- <review requests, re-review queue, your PRs blocked on a decision>

Deep block (proposed)
- <the 1-2 highest-leverage things to spend the focused morning on, and why>

Tickets in flight
- <in-progress Jira, tied to the above where they overlap>
```

In catch-up mode, lead with a short **While you were away** block (what shipped,
what now needs you, what moved on your tickets) before the rest.

The **deep block** is the point of the brief. Propose 1-2 concrete focus items
drawn from the queues - clear a re-review, progress a ticket, answer a review
request - with a one-line why each. Flag what's blocked on others (chase, don't
sit on) vs blocked on Issei (the real work). Propose; he decides.

## 5. Offer to chain (don't auto-run)

End by offering the obvious next action, gated on his word:

- re-review queue has items -> "want me to run turbo-pr-review on #48?"
- needs a standup -> "/standup-update" (separate, team-facing artefact)
- resume a specific thread -> working-memory (`recall.py show <topic>`)

## Boundaries

Read-only and advisory. Proposes a plan; never merges, approves, dispatches,
posts, or sends. No file writes (display only, like standup-update). Uses the
`Issei-curve` work account. Distinct from `standup-update` (backward-looking, for
the team) and `working-memory` (single-task recall) - the brief is the
forward-looking, private day-assembler that ties them together.
