---
name: standup-update
description: Generate a three-block standup update (Yesterday / Today / Blockers) for Issei's 09:10 standup, sourced from Claude Code sessions whose last event fell in the window plus GitHub PR activity on the Issei-curve account. Session classification mirrors the harvest pipeline's privacy_route — work cwd fragments include intech-*, curve-*, and `/knowledge base` (Issei's planning hub); FPL and the `ikuzuki` GitHub account are filtered out. Use this skill whenever Issei says "standup", "prep my standup", "what did I do yesterday", "/standup-update", or when a standup-related scheduled routine fires. Window is the last weekday — Tue-Fri uses yesterday's date, Mon skips back to Friday (weekend not counted). Renders to chat only; no file writes.
---

# Standup update

Get Issei standup-ready by 09:10. Read yesterday's Claude Code sessions
and recent PR activity on the Issei-curve GitHub account, then render a
three-block standup in his voice. Display only — no file writes.

## The window

The window starts at the previous business day at 00:00 local time and
extends through *now* — inclusive of any work Issei has done this
morning before running standup.

- Tue–Fri: window starts at yesterday 00:00 local
- Mon: window starts at last Friday 00:00 local (skip Sat/Sun)

Convert to absolute datetimes with timezone before filtering. Today's
date is in the environment context; current time comes from
`datetime.now()`. The "Yesterday" header in the output is the standup
convention - it covers everything since the last standup, including
this morning's pre-standup work.

## Implementation reliability

Two failure modes have bitten this skill in production; avoid both.

**1. Don't author the session-scan script via Bash heredoc.** Anything
non-trivial in Python (f-strings, escaped quotes, regex) wedges
`cat << 'EOF' ... EOF`, especially on Windows where Bash sits over
PowerShell. Write the script with the `Write` tool to e.g.
`C:\tmp\standup_scan.py`, then run `python C:/tmp/standup_scan.py`.

**2. Get cwd from the event JSON, not from the folder name.** Every
event in a `.jsonl` carries a `cwd` field (e.g.
`"C:\\Users\\IsseiKuzuki\\intech-ai-plugin"`). Trust that. *Do not*
try to invert folder names like `c--Users-IsseiKuzuki-intech-ai-plugin`
back into a path — the folder uses `-` as both path separator AND
within-name character, so `replace("-", "/")` mangles `intech-ai-plugin`
into `intech/ai/plugin` and the classifier silently drops every
matching session.

Normalise the event cwd before substring-matching:
forward-slashes, lowercase, strip the `C:` drive prefix.

## Team vs personal — what counts

The standup is a work artefact. Only Issei's *team* work belongs here.
Classification mirrors the harvest pipeline's `privacy_route` rule
(`issei-plugin/skills/harvest/scripts/harvest.py`) — single source of
truth for what counts as work across the personal toolchain.

Substring-match the session's canonical cwd (forward-slashed,
lower-cased, worktree-stripped) against these fragments:

**Work cwd fragments** (include):
`/intech-api`, `/intech-data`, `/intech-enrich`, `/intech-enrich-poc`,
`/intech-etl`, `/intech-hub`, `/intech-utils`, `/intech-ai-plugin`,
`/intech-meta`, `/intech-cicd`, `/intech-infra`, `/curve-daas`,
`/curve-hub`, `/curve-hackathon`, `/claude/claudemaxing`,
`/knowledge base`, `/projects/intech`, `/sandbox`.

`/knowledge base` is in the work list deliberately — Issei uses it as
a planning hub for team work (PR reviews, sprint demo prep, vault
searches against team topics). Don't treat it as personal-by-default.

**FPL fragments** (exclude — personal):
`/fpl-platform`, `/fpl project`.

**Default** when nothing matches: personal — exclude.

**Privacy exclusion keywords** — drop the session regardless of cwd if
the first three user messages mention HR/medical topics:
`salary`, `compensation`, `comp`, `hr`, `performance review`,
`terminated`, `termination`, `disciplinary`, `medical`, `therapist`.

**Intent overrides cwd in one narrow case**: a session in `/knowledge
base` whose ONLY intent is vault maintenance (`/lint-vault`,
`/distil-vault`, `/weekly-vault-review`, "clean up the vault") is
personal admin, not team work. Drop. A K-B session that searches the
vault for a team topic ("anything in my vault on sprint demo") is
team work — keep.

**Banter filter**: drop sessions whose user messages are pure chat
("Ay big man ting...", "tell me a joke") with no team-topic substance.
Short sessions with no team artefact produced are noise.

**GitHub account**: `Issei-curve` only. The `ikuzuki` account is
personal (FPL, personal-site repos) and never goes in the standup.

## Sources

### Claude Code sessions

Sessions live at `C:\Users\IsseiKuzuki\.claude\projects\<project-folder>\<uuid>.jsonl`.
Flat JSONL events per session, one folder per cwd.

1. List `.jsonl` files under `.claude\projects\*\`. For each, scan
   events for the *last* one carrying a `timestamp` field. **Use the
   last-event timestamp, not file mtime.** A session that started
   2026-05-26, did its substantive work 2026-05-27, but had a final
   queue-op event at 2026-05-28 00:01 will have its mtime in today
   and still belong to yesterday's standup. The harvest pipeline uses
   `ended_at` for the same reason; mirror it.
2. Keep sessions whose last-event timestamp falls in the window.
3. Skip the `subagents/` subdirs — those are subagent transcripts,
   noise here.
4. Decode the project name from the folder, e.g.
   `c--Users-IsseiKuzuki-intech-ai-plugin` → `intech-ai-plugin`. Case-
   insensitive — `c--...` and `C--...` are the same project.
5. Collapse worktrees to the parent: any folder matching
   `<parent>--claude-worktrees-<slug>` rolls up under `<parent>`. Don't
   double-count work that happened in a worktree off the same repo.
6. Exclude scheduled-task autoruns. Three forms to watch for:
   - First user message starts with `<scheduled-task ...>`
   - First user message starts with `<system-reminder>` or
     `<command-name>` and never gets a real human message after
   - First user message is the inlined body of a `SKILL.md` (often
     starts with `Base directory for this skill: ...`) and the rest
     of the session is autonomous skill execution
   The `daily-pr-digest` and `weekly-knowledge-harvest` routines are
   regular offenders.
7. Apply the team-vs-personal classification from the section above.
   Drop everything that classifies as personal, fpl, or excluded.
8. For each remaining session, extract the **in-window slice of
   intent**, not the session-level intent. Issei has long-running
   sessions that span weeks (the CDT ClickHouse PoC session has
   4000+ events from 2026-05-11 to today). The session's *first* user
   message describes what then-Issei wanted on the start date - that's
   irrelevant to today's standup. Walk events in order, track current
   timestamp, and only consider events whose timestamp is inside the
   window:
   - The first substantive in-window user message (skip wrappers and
     `<command-name>` tags)
   - Any `mark_chapter` titles inside the window
   - In-window assistant turns that summarise shipped work (e.g.
     benchmark results, table-state confirmations, "done -" recaps)
   - In-window user-message count and tool-use density - high =
     substantive work, low = pivot/clarification only

   A long session that touched a topic for one in-window message and
   then pivoted is not "a piece of work on that topic"; a long session
   with 30 in-window user messages and a results-shaped assistant
   summary at the end *is* substantive work, even if it opened months
   ago with a generic "help me with X" message.

Group by project. Don't quote raw session content; render the intent in
Issei's voice. When pulling substance from a long-running session, name
the underlying piece of work (e.g. "CDT ClickHouse PoC"), not the
session itself.

### GitHub PR activity

Account: `Issei-curve` only (work). The `ikuzuki` account is personal
(FPL, personal-site repos) and never goes in the standup. Check
`gh auth status`; if a different account is active, switch with
`gh auth switch --user Issei-curve` before running the queries.

`gh search prs` only accepts `--state=open|closed` — there is no `all`.
Run three queries:
- `gh search prs --author=@me --updated=">=YYYY-MM-DD" --state=open --json number,title,state,url,repository,updatedAt`
- `gh search prs --author=@me --updated=">=YYYY-MM-DD" --state=closed --json number,title,state,url,repository,updatedAt`
- `gh search prs --review-requested=@me --state=open --json number,title,url,repository` (this feeds Today)

From the first two queries: opened, merged, commented-on in the window.
From the third: PRs awaiting his review right now.

## Today inference

- Open PRs awaiting Issei's review (from the review-requested query)
- In-flight work from yesterday's sessions that didn't merge yet — e.g.
  branches/PRs touched in sessions where the corresponding PR is still
  open
- Local in-flight work: check `git status` / `git log origin/main..HEAD`
  in known team repos (`intech-ai-plugin`, `intech-data`, `intech-api`,
  `intech-enrich`, `curve-daas`). Commits ahead of remote, especially
  on `INTECH-<n>-...` / `CDT-<n>-...` branches, are clear Today fodder.
- Don't invent ambition. If yesterday was "finish X", Today is "land X,
  then pick up Y" — not a fresh roadmap.

## Blockers

Scan session content for explicit blocker phrases — "blocked",
"stuck", "waiting on X", "can't get Y to work", "Y is broken".
Surface only real blockers, not exploratory hiccups. Empty Blockers is
correct; drop the section entirely rather than padding with "no
blockers identified".

## Output

Render to chat only. The block should be self-contained and copy-
pasteable into Teams. Shape:

```
**Standup — YYYY-MM-DD**

Yesterday
- <one bullet per coherent piece of work, project-tagged where it helps>

Today
- <in-flight from yesterday + open PRs awaiting review>

Blockers
- <real blockers only, or omit the section>
```

The date in the header is today's date - this is the standup *for*
today, summarising work done since the last one. No preamble, no
postamble, no closing line. Just the block.

### Substance, not labels

Every bullet must read as descriptive English to a teammate who hasn't
seen the ticket or PR. Lead with what the work *does*; put ticket
keys and PR numbers in parentheses, not in front. Sources for the
substance:

- the PR title (already in the `gh search` JSON)
- the branch name (`CDT-244-pr-digest-cron` → "CDT PR digest cron")
- the first substantive user message in the session
- chapter markers (`mark_chapter` titles) when present

Examples:

- Bad: `shipped CDT-244 + CDT-181`
- Good: `shipped the daily CDT PR digest as a Cloud Claude routine ([PR #28], CDT-244 + CDT-181)`
- Bad: `reviewed [PR #156]`
- Good: `reviewed Rad's FoDI discovered-entities stream work ([intech-enrich#156])`
- Bad: `did some Confluence review`
- Good: `honest review pass on the Confluence Guidelines page, cross-referenced with my vault`

If you genuinely can't find substance for a session (one-line question,
no artefact), drop it - don't bullet "asked a question about X". The
standup is shipping evidence, not session inventory.

### Voice

Terse, lowercase-friendly, British English, no em-dashes (use ` - `),
no corporate-speak, no "I successfully completed" / "I worked on".
State what shipped or moved. Consult the `issei-voice` skill if
phrasing feels off.

## Anti-patterns

- Quoting raw session content verbatim. The reader is Issei at 09:08,
  not future-Issei reading the vault.
- Counting worktree sessions separately from their parent repo.
  Collapse.
- Including `subagents/` transcripts. Noise.
- Including scheduled-task autoruns in Yesterday. Those are Claude's
  chores, not Issei's work.
- Including personal-life sessions or PRs. FPL, LinkedIn, CV, blog,
  personal-plugin development, anything from the `ikuzuki` GitHub
  account — all stays personal. The standup is a team artefact.
- Hard-excluding any `/knowledge base` cwd session. Knowledge Base is
  Issei's planning hub for *team* work too — apply the harvest's
  WORK_CWD_FRAGMENTS rule, not a blunt path exclude.
- Filtering on file mtime instead of last-event timestamp. A session
  that ended yesterday but had a stray queue-op event after midnight
  will have today's mtime and be wrongly excluded.
- Padding empty Blockers with "no blockers identified at this time".
  Drop the line.
- Inventing Today. If yesterday ended mid-work, Today is finishing it.
- Treating frustration as a blocker. "This is annoying" is not a
  blocker; "waiting on Adele's review" is.
- Writing anything to a file. This skill is display-only. (Exception:
  the throwaway session-scan `.py` at `C:\tmp\` is fine - that's
  scaffolding, not output.)
- Inlining the session-scan Python via Bash heredoc. Use the Write
  tool to drop a `.py` file instead - heredocs wedge on f-strings and
  escapes.
- Deriving cwd from the folder name. The `cwd` field is on every
  event; read it from there. Folder-name inversion is ambiguous and
  silently misclassifies every team session.
- Stopping the window at yesterday's midnight. The window extends
  through *now* - this morning's work counts.
- Bulleting ticket or PR numbers without context. "shipped CDT-X" is
  useless without saying what X is. The bullet must read as English to
  a teammate who hasn't seen the ticket.
- Reading only the first user message to judge a session. Issei's
  multi-week CDT ClickHouse PoC session opens with "So I'm just
  onboarding to start working on the data plane for CDT" - that's
  from weeks ago. Yesterday's slice inside the same session has the
  actual standup substance (benchmark results, schema decisions,
  questions for Matt). Walk in-window events; ignore the opener if
  it's outside the window.
- Dismissing a long session as one-line work. A 4000-event,
  30+-in-window-user-message session is the day's primary work, not
  a footnote. Length and density beat first-message inference.
- Treating vault-distillation of *team-shipping* substance as personal
  admin. Distilling the ClickHouse exploration into a vault pattern +
  ADR-lite mirror is team work captured locally - the underlying
  piece of work belongs in the standup (named as the underlying
  thing, e.g. "ClickHouse PoC"), even if the artefact is a vault note.
