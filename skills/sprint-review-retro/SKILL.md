---
name: sprint-review-retro
description: Prepare Issei's personal CDT sprint review and retrospective talking points before the ceremonies, by mining his own Claude Code work sessions over the sprint window and cross-referencing them against the live CDT sprint document in Confluence. Use whenever Issei says "prep my sprint review", "prep the retro", "sprint review/retro prep", "what should I bring to review/retro", "surface things for the sprint ceremonies", or "/sprint-review-retro". This is Issei's personal prep he walks into the meeting with - distinct from the team-owned sprint-digest (the machine-generated Confluence shipping page) and sprint-doc (the team's planning doc); reach for those when the deliverable is a team Confluence page rather than Issei's own talking points. Produces team-altitude material shaped to the team's real review/retro structure, honest about what chat-mining can and cannot see.
---

# Sprint review & retro prep

Get Issei ready to walk into the CDT Product Development sprint review and
retrospective with substance to contribute. Two artefacts: a **review**
half (what shipped, demo candidates, progress vs goals) and a **retro**
half (went well / could be better / worth solving), both pitched at
**team altitude** and cross-referenced against the live sprint document.

The output is prep he brings to a meeting where the team works a shared
board - not a status report. Shape it so each point is something he could
actually raise in the room.

## The two sources (and only these)

1. **Issei's Claude Code work sessions over the sprint window** - the
   evidence base for technical substance, decisions, blockers, and
   alignment gaps. Extracted with the co-located scripts (below), which
   reuse the harvest pipeline's team-vs-personal classifier.
2. **The live CDT sprint document in Confluence** - the frame. It gives
   the sprint window dates, the stated goals and owners, the demo backlog,
   the AI-first focus with explicit definitions of done, the risks, and
   the retro themes carried forward. Every chat finding is mapped back
   against this.

Don't invent a third source. GitHub PR state is fair game for ground
truth on whether something merged (the chat says "PR open"; `gh pr view`
confirms current state), but it isn't a primary source.

## Step 1 - read the sprint document first

It sets the window and the frame, so fetch it before anything else.

The sprint docs live as child pages under the **CDT Sprint Documents**
page (Confluence page id `539557906`, space `Curve` /
`curve-analytics.atlassian.net`). Get its descendants, pick the
**latest `CDT Sprint N`** child (highest N - ignore the Template and
Archive pages), and fetch its body as markdown.

Use the Atlassian MCP (`getConfluencePageDescendants` then
`getConfluencePage`). If the MCP is unavailable, fall back to the
`confluence` skill from `intech-tools`.

From the body, extract and hold onto:
- **Window dates** - the date-range header. Note the dates are written
  **US `M/D/YYYY`** (month first): `6/5/2026` is 5 June, not 5 May. Take
  the *start* date, convert to `YYYY-MM-DD`, and pass it to the extractor
  as `--since`. Getting month/day backwards silently shifts the whole
  window, so be deliberate here.
- **Sprint goals** - the status/goal/owners table. Note which goals
  Issei owns and what their status icon claims.
- **Demo backlog** - what the team planned to demo.
- **AI-first focus** - each item has an explicit **definition of done**.
  These are the bar to report against literally.
- **Risks/blockers** - especially cross-goal dependencies.
- **Retro themes carried forward** - the recurring observations. Fresh
  evidence against these is the highest-value retro material.

## Step 2 - extract and mine the work sessions

The scripts are co-located in `${CLAUDE_PLUGIN_ROOT}/skills/sprint-review-retro/scripts/`
and reuse `harvest/scripts/harvest.py` (single source of truth for what
counts as Issei's *team* work - the `privacy_route` classifier). No env
setup needed; the scripts set sensible KB path defaults. The extractor
also drops personal-admin noise the base classifier would keep -
`issei-plugin` (his personal plugin) and pure vault maintenance both
match harvest's `/knowledge base` work fragment but aren't CDT team work.

1. **List the sprint's work-threads:**
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sprint-review-retro/scripts/extract_threads.py" --since YYYY-MM-DD
   ```
   (Use the sprint-start date from step 1. Falls back to `--days 16` if
   you have no date.) Prints one block per team work-thread: window,
   cwd, branches, first message, tool histogram, files, and the
   constituent `.jsonl` `paths`. Threads are grouped by cwd + 24h
   rolling window, so a long-running effort is one thread even across
   many sessions.

2. **Render the substantive threads in full** to read their arc:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sprint-review-retro/scripts/render_one.py" "<path-to-session.jsonl>"
   ```
   Prints user + assistant text with tool calls compacted. Pipe through
   `head` or redirect to a temp file if large.

3. **Fan out the mining.** The big threads (the data-plane / ClickHouse
   work, the tooling work, the planning/decision threads) are large.
   Spawn one subagent per major thread in parallel (`Agent` tool),
   giving each the thread's `.jsonl` paths and the `render_one.py`
   command. Ask each to return the same five-bucket digest:
   1. **Shipped / demoable** - what was built and works, with status
      (merged / PR open / PoC-only). Be concrete - name the artefact.
   2. **Decisions made** - architectural/design calls + the reasoning.
      Flag any that *overturned* a prior conclusion - those are the most
      review-worthy.
   3. **Carried over / next** - started-not-finished, explicit "next",
      known TODOs.
   4. **Blockers / friction / frustration** - what went wrong, took too
      long, needed rework, fought the tooling. Honest, even if minor.
   5. **Ways-of-working observations** - how the work happened, not what.

   Tell each subagent to **ignore scheduled-task autorun content** (the
   `[autorun?]`-flagged threads merge a chore-run with real dev work in
   the same cwd - mine the dev/decision substance, skip the autorun
   execution logs) and to drop local-command/banter noise.

## Step 3 - synthesise at team altitude

This is where the skill earns its keep. The raw five-bucket digests are
Issei-task-specific; the ceremonies are about the whole team. Reshape.

**Altitude rule.** Strip anything that is purely Issei's own task hygiene
("my PoC branch was messy", "I debated X before reading Y"). Keep the
high-level points that matter to the team even when they originate in
Issei's work: "we have a database, provisioned and version-controlled"
is a team point; "I refactored my read-bank" is not. When a personal
friction generalises to a team pattern, raise the *pattern*, not the
instance.

**Cross-reference everything against the sprint doc:**
- **Map findings to goals.** Connect technical work to the stated goals
  and risks. If the chat shows ClickHouse schema with mention tables and
  a risk says "Brand Monitoring backend depends on ClickHouse PoC
  outcome", say the dependency is now answered. The doc treats goals as
  separate; the value you add is joining them.
- **Report against definitions of done literally.** An AI-first item
  whose DoD says "shipped or formally deferred" demands a binary call -
  built-but-blocked is neither. Name which.
- **Recurring retro theme + fresh evidence -> propose the action.** A
  theme carried for two-plus sprints with concrete new instances this
  sprint should become a standing action this time, not a third re-note.
- **Be precise about partial progress.** A "CONTINUE" goal Issei
  co-owns where his contribution was foundational (not surface) should
  say so, so "continue" doesn't imply progress that didn't happen.

## The blindspot rule (do not skip this)

Chat-mining is systematically blind to part of the retro. It sees
technical substance, decisions, blockers-with-evidence, and cross-cutting
alignment gaps. It is **blind to team sentiment, ceremony cadence, and
anyone else's workstream** - things like "drop-ins are working",
"standups drift", "the demo got moved again", "AWS notifications are a
nightmare", "roles feel clear". These live in how people felt about the
fortnight, which the logs cannot see.

So:
- **Never fabricate sentiment coverage.** Don't pad the retro with
  feel-good or feel-bad cards you have no evidence for.
- **Surface the gap explicitly.** End the retro half with a short
  "bring to the room" section: prompts for the sentiment/cadence/
  other-people's-work topics this method can't reach, so Issei walks in
  knowing what to listen for rather than thinking the artefact is
  complete.
- **Other people's wins** (login flow shipped, frontend-backend talking)
  may appear as *goals* in the doc but won't appear as *achievements* in
  Issei's chats. Note them as "goal claims to verify in the room", not
  as confirmed wins.

## Output shape

Match the team's actual ceremony structure. Render the full artefact to
chat, and also save a copy to
`C:\Users\IsseiKuzuki\Knowledge Base\working-docs\sprint-prep\<sprint-label>.md`
(create the dir if needed; this is an ephemeral working doc, not a vault
promotion - never commit it). Use the sprint label from the doc title
(e.g. `cdt-sprint-3`).

```
# <Sprint label> - review & retro prep
_Generated <date> from Claude work sessions <window> + the live sprint doc._

## Sprint review

### Goals - status vs the board
- <per goal Issei can speak to: what the chat evidence says about its
  real state, especially where it differs from the status icon>

### Demo candidates (ranked, strongest first)
- <what's genuinely demoable, with one line on why it matters to the
  business - the doc asks "why is this important? why now?">

### Use of AI
- <AI-first items vs their definitions of done; shipped / deferred>

### Celebrations
- <genuine wins worth calling out - evidence-led decisions, reversals
  that held standards under pressure, clean ships>

### Carried over
- <built-not-merged, blocked-on-infra, gated-on-external-signoff,
  open contracts - team-relevant only>

## Sprint retro

### What went well
- <team-altitude positives with evidence>

### What could have gone better
- <friction as team patterns, not one person's hygiene>

### Ideas / problems worth solving
- <concrete experiments; for recurring themes, the action not the re-note>

### Carried themes - status this sprint
- <each carried theme from the doc + what this sprint's evidence says>

### Bring to the room (this method can't see these)
- <sentiment / cadence / other-people's-work prompts to raise live>
```

Drop any section that's genuinely empty rather than padding it.

## Voice & format

Prep for Issei, so terse and direct is fine, but each point must read as
English to a teammate - lead with what the thing *is* or *does*, ticket
keys and PR numbers in parentheses. British English, no em-dashes (use
` - `), no corporate-speak. Prose over lists where a point needs
reasoning; bullets where it's genuinely a list. This is shipping/
discussion evidence, not a session inventory - if there's no substance
for a thread, drop it.

## Anti-patterns

- **Staying at personal-task altitude.** "I cleaned up my branch" is not
  a team review point. Lift to the team-relevant high-level fact or drop
  it. This is the single most common failure - the first pass always
  comes out too personal.
- **Faking sentiment coverage.** If you have no evidence a drop-in was
  useful or the demo slipped, don't write a card for it. Put it in
  "bring to the room" instead.
- **Re-noting a recurring theme without an action.** A theme carried for
  multiple sprints with fresh evidence needs a proposed change, not a
  third description of the problem.
- **Ignoring the definitions of done.** The AI-first items have explicit
  DoDs in the doc. Report against them literally - "shipped or deferred"
  is a binary, not "in progress".
- **Treating goals as confirmed wins.** A goal in the doc that doesn't
  appear in Issei's chats is a claim to verify in the room, not an
  achievement to celebrate on his behalf.
- **Reading only the first user message of a long thread.** The
  multi-week ClickHouse/data-plane thread opens with onboarding from
  weeks ago; the sprint's substance is in the in-window slice. Mine the
  arc, not the opener.
- **Counting autorun chore content as work.** `[autorun?]`-flagged
  threads merge scheduled-task runs with real dev - take the dev
  substance, skip the chore execution logs.
- **Inventing a sprint window.** Use the doc's header dates. Only fall
  back to `--days 16` if the doc genuinely has no dates.
- **Committing the working doc.** The `working-docs/` output is
  ephemeral scaffolding - never `git add` it to the vault.
- **Authoring the scan scripts via Bash heredoc.** They already exist
  co-located; call them. If you must add scripting, use the `Write` tool
  to a `.py` file (heredocs wedge on Windows Bash-over-PowerShell).
