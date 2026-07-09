---
name: jira-board-hygiene
description: Surface the hygiene state of Issei's CDT Jira board — tickets assigned to or reported by him that are stuck in a closed sprint, sitting in no sprint, or stale in progress, plus the full open list — then suggest what to move, close, or chase, and apply the agreed changes only on his confirmation. Use when Issei says "check my board", "jira board hygiene", "what's on my board", "anything stale/outdated on my board", "what needs moving", "tidy my tickets", "/jira-board-hygiene", or when a scheduled routine fires it. Read-and-suggest by default; never bulk-transitions or re-sprints tickets without explicit sign-off. Scoped to CDT; distinct from backlog-refinement (team Direction-led MECE grooming) and jira-ticket-gen (creating tickets).
---

# Jira board hygiene

A weekly-ish tidy of Issei's own board: what's drifted (stuck in a closed sprint, no
sprint, stale in progress) and the full open picture, so nothing silently rots the way
those closed-sprint stragglers do. Surfaces and suggests; **Issei confirms before any
ticket is moved or transitioned.** This is the personal board-tidy he was doing by
hand — distinct from `backlog-refinement` (team Direction, MECE) and `jira-ticket-gen`.

Script lives in `C:\Users\IsseiKuzuki\Claude\project-autopilot\scripts\`.

## Step 1 — Pull the board state

```
python jira_board.py --markdown            # CDT by default
python jira_board.py --project INTECH --markdown
```

Uses the Atlassian REST token from the environment (narrow JQL, no MCP overflow). It
returns five buckets: the three **hygiene flags** — `closed_sprint_straggler`,
`no_sprint`, `stale_in_progress` (In-Progress category, untouched >10d) — plus the full
`open_assigned` and `open_reported` lists (oldest-touched first). If it errors on auth,
check `ATLASSIAN_EMAIL` / `ATLASSIAN_API_TOKEN` are set.

## Step 2 — Read it and suggest actions

Don't just echo the buckets — turn them into a short, decisive to-do:

- **Closed-sprint stragglers** → propose the specific move: current sprint if it's
  live work, next sprint if it's planned, or close/back-to-backlog if it's actually
  done or dead. Name the ticket and the proposed destination.
- **No sprint** → into the current/next sprint, or explicitly to the backlog.
- **Stale in progress** → move along, hand back, or drop to To Do — say which.
- **Open assigned/reported** → only flag the ones that look off (a To Do you'll never
  do, a duplicate, something mis-stated). Don't editorialise over the healthy ones.

Keep it to what needs a decision. A clean board is a valid, one-line result.

## Step 3 — Apply, only on confirmation (gated)

Propose the changes as a concrete list and **wait for Issei's explicit go** (all, or a
subset — "do the closed-sprint ones", "just 318 and 20"). Then apply via the Atlassian
MCP:

- **Re-sprint / to backlog** → `editJiraIssue` setting the sprint field (or clearing
  it for backlog).
- **Status move** → `transitionJiraIssue` (fetch `getTransitionsForJiraIssue` first;
  transition names vary by workflow).

Apply only what he approved, report each result plainly (moved / failed + why), and
never invent a transition or sprint that wasn't agreed. If a move fails (permission,
missing transition), say so rather than papering over it. Nothing is auto-applied — the
default output is suggestions; the write step needs his word.

## Not for

- Team-wide backlog grooming against Direction — that's `backlog-refinement`.
- Creating or drafting tickets — that's `jira-ticket-gen`.
- Anyone else's board — hard-scoped to Issei (`assignee`/`reporter = currentUser()`).
