---
name: scoro-timesheet
description: Fill in Issei's Scoro timesheet, driving the dedicated automation Edge over CDP (the same persistent session the presence layer uses - saved credentials, so a dropped session self-recovers; no per-session login). Invoke when the user asks to fill, log, plan, submit, or backfill their Scoro timesheet, or says "fill in my timesheet", "do my timesheet", "log my hours in Scoro", "backfill last week's hours", or when the Friday-16:00 routine fires. Also books time off / annual leave / holiday via Scoro's Time off requests module ("book holiday in Scoro", "log my AL", "book time off", "book leave"). Flow is gather requirements -> propose plan -> confirm -> fill cells -> offer to submit; never types into a cell before the user approves the plan, never submits without explicit confirmation.
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
   before any read/fill. **If Edge lands on Scoro's login page, log in - don't ask
   whether you should.** The saved credentials autofill the form, so `scoro_login.py`
   just clicks Login for Issei (it never types credentials itself). This is the
   sanctioned "click login" action and needs no confirmation; run it as a normal part
   of pre-flight and only surface the login page to Issei in the `login_needed` case
   below. Statuses:
   - `already_logged_in` / `logged_in` -> proceed.
   - `login_needed` -> the form genuinely wasn't prefilled (nothing to click); tell
     Issei to log into Scoro once by hand in the automation Edge so the profile
     persists it. Never guess or type credentials.
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

Also: **annual leave must be logged in both Scoro and Outlook** - book the Scoro
side via the [Booking time off](#booking-time-off--annual-leave) section below (the
timesheet grid has no Annual Leave row; leave lives in a separate module).

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

## Booking time off / annual leave

Scoro's **Time off requests** module (top nav) is separate from the timesheet grid: a
full-day AL / holiday goes here, *not* in a timesheet cell - there is no Annual Leave
row in the grid. `scoro_timeoff.py` drives the New form end to end:

```
python scoro_timeoff.py --date 24/07/2026                # Vacation, Approved, Full Day
python scoro_timeoff.py --date 24/07/2026 --dry          # fill but DON'T Save (verify first)
python scoro_timeoff.py --date 12/08/2026 --type "Sick Leave" --status Submitted
```

- **Type of Time Off**: Vacation, Sick Leave, Parental Leave, Study Leave, Other time
  off, Extra availability, Compassionate Leave. **Vacation == annual leave / holiday**
  (the default).
- **Status**: Approved (default) / Submitted / Rejected / Cancelled. Only set Approved
  when Issei says so; otherwise Submitted and let the manager approve.
- **Dates** is a 3-month range picker; clicking a day mis-fires (three "24"s on screen
  plus a week-number 24 - easy to land on the wrong month), so the script sets the
  field value directly in `dd/mm/yyyy`. One-day requests only; a genuine range would
  need extending the script.
- **Duration** defaults to Full Day; **Hours** then saves as `0:00 h` - expected
  (Hours is only used for partial days), not a bug.
- Creates a real HR record. Run `--dry` first, eyeball owner/status/type/date, then do
  the live run. Writing an *approved* record is a standing-record change - confirm with
  Issei before the non-dry run, exactly like the Submit gate. Verify after via the
  saved `/timeoffrequests/view/<id>` page.
- **Also log the leave in Outlook** - Scoro is not the calendar source of truth.

## Not for

- Reading historical timesheet reports (use Scoro's reports view).
- Editing already-submitted (locked) weeks.
- Anyone else's timesheet - hard-scoped to Issei's `curve.scoro.com` session.
