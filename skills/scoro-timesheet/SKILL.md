---
name: scoro-timesheet
description: Fill in Issei's Scoro timesheet, driving the dedicated automation Edge over CDP (the same persistent session the presence layer uses - saved credentials, so a dropped session self-recovers; no per-session login). Invoke when the user asks to fill, log, plan, submit, or backfill their Scoro timesheet, or says "fill in my timesheet", "do my timesheet", "log my hours in Scoro", "backfill last week's hours", or when the Friday-16:00 routine fires. Flow is gather requirements -> propose plan -> confirm -> fill cells -> offer to submit; never types into a cell before the user approves the plan, never submits without explicit confirmation.
---

# Scoro timesheet

Drive Issei's Scoro timesheet via the **dedicated automation Edge over CDP** (the
persistent profile signed into `curve.scoro.com`, with the Scoro credentials saved so
a dropped session self-recovers via `scoro_login.py`). No fresh browser, no per-session
MCP login. Flow: **gather requirements -> propose plan -> confirm -> fill cells**.
Never type into cells before the user approves the plan.

Scripts live in `C:\Users\IsseiKuzuki\Claude\project-autopilot\scripts\`.

## Step 0 - Pre-flight

1. The automation Edge must be running (`launch_automation_edge.ps1`). Its profile
   has the Scoro credentials saved, so a dropped session self-recovers - no
   fresh-login browser, no MCP login path.
2. `python scoro_login.py --markdown` - ensures `curve.scoro.com` is authenticated
   before any read/fill. It submits the autofilled login form but never types
   credentials itself. Statuses:
   - `already_logged_in` / `logged_in` -> proceed.
   - `login_needed` -> the form wasn't prefilled; tell Issei to log into Scoro once
     by hand in the automation Edge (the profile then persists it). Don't guess creds.
   - `unavailable` -> CDP unreachable, i.e. the automation Edge isn't running; tell
     Issei to launch it. Hard stop.
3. `python scoro_read.py --markdown` - reads the current week heading + the live task
   rows + each row's Mon-Fri values. Trust these *live* rows, not a hardcoded list
   (the task set changes; e.g. Week 28 shows Product R&D / Enablement / Meetings plus
   the Internal Activities rows).

## Step 1 - Identify the week

`scoro_read.py` returns the heading (`June 2026 Week 27`). Ask which week to fill:
the currently-displayed one (default - Scoro lands on the latest) or a backfill of a
prior week. To change week, navigate Previous/Next in the Edge (a small CDP click)
then re-read - only on explicit instruction, since you can't tell a genuinely-unfilled
prior week from an already-submitted one by reading alone.

## Step 2 - Gather plan inputs

From the live rows, read off the valid task targets. Ask, in order:

1. **Which tasks get hours, and roughly what split?** ("bulk in Product R&D, some in
   Meetings, a bit of Personal Development" - don't demand exact per-cell hours.)
2. **Which days are 8h (overtime) vs the standard 7.5h?** Default 7.5h/working day;
   most weeks have one 8h day for variance. "no overtime this week" is fine.
3. **Any non-working days?** (bank holidays - flagged in the date row - or AL.)

## Step 3 - Generate a natural plan

Per-day, per-task table satisfying:
- All values **multiples of 0.5h**, in `h:mm` (`5:30`, not `5.5`).
- Each day sums to its target (7.5h or 8h).
- Bulk-task hours **vary day-to-day** (4:30 / 5:00 / 5:30, not flat) - flat rows look
  manufactured.
- Smaller tasks sprinkled across days, not every day.
- Meetings taper (often less Friday, none on holidays); bank holidays 0h.

Show it as a markdown table (tasks x days + a Day Total row) with a one-paragraph
variance rationale. **Wait for explicit "go" / "fill it in" before writing a cell.**

### Enablement vs Product R&D - what goes where

Per James Curwell (May 2026): **Enablement** is narrow - designing/documenting/
implementing ways of working, ceremonies, best practices, design patterns, dev
processes, enablers, accelerators. The steady state is small. Most CDT tech time
(planning, research, design, prototyping, development, scaffolding, AWS, repo/
pipeline/model work) lands in **Product R&D** (or the relevant model row), not
Enablement. Default Issei's bulk hours to Product R&D unless the week was genuinely
dominated by process/ceremony/accelerator work. Apply going forward only.

Also: **annual leave must be logged in both Scoro and Outlook.**

## Step 4 - Fill cells (after confirmation)

`python scoro_fill.py plan.json` - the plan is `{"<task label substr>": {"Mon":"5:30",
"Tue":"5:00", ...}, ...}` using the live task labels from `scoro_read.py`, omitting
0h days. Preview first with `--dry` (reports which cells it would fill vs skip).
Mechanism (proven live): click the empty day cell -> an hours INPUT focuses ->
select-all + type `h:mm` -> Tab commits.

- **Only fills EMPTY cells.** A cell that already has a value opens a NOTE textarea on
  click (a Scoro quirk), not the hours editor, so `scoro_fill` SKIPS filled cells
  rather than risk writing into the wrong field. Clearing/editing a filled cell isn't
  automated - do that in the Scoro UI.
- **Footer overlay** can intercept clicks on lower rows - `scoro_fill` scrolls each
  cell into view first.
- **Verify after** (Step 5): `scoro_read` reflects changes only after a reload
  (`scoro_fill` reloads at the end); filled values display as `30m` / `5h 30m`.
- Never submits.

## Step 5 - Verify and offer to submit

`scoro_read.py` again; confirm each day's total matches the plan, then summarise:

```
Week 27 filled: Mon 7:30, Tue 7:30, Wed 8:00, Thu 7:30, Fri 7:30 -> 38h.
Not submitted - submit yourself, or shall I click Submit week?
```

**Never click Submit without explicit confirmation.** Submission is irreversible
from Issei's side (needs admin to reopen). For the Friday-16:00 routine: auto-*fill*
the plan, then stop and surface it for Issei to review + submit - never auto-submit.

## Not for

- Reading historical timesheet reports (use Scoro's reports view).
- Editing already-submitted (locked) weeks.
- Anyone else's timesheet - hard-scoped to Issei's `curve.scoro.com` session.
