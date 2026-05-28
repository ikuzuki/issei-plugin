---
name: standup-update
description: Generate a three-block standup update (Yesterday / Today / Blockers) for Issei's 09:10 standup, sourced from yesterday's Claude Code sessions and recent GitHub PR activity on the Issei-curve account. Only counts team work — personal sessions (FPL platform, LinkedIn/CV drafts, vault edits, personal-plugin development) and the `ikuzuki` GitHub account are filtered out. Use this skill whenever Issei says "standup", "prep my standup", "what did I do yesterday", "/standup-update", or when a standup-related scheduled routine fires. The window is the last weekday — Tue-Fri uses yesterday's date, Mon skips back to Friday (weekend work not counted). Renders to chat only; no file writes.
---

# Standup update

Get Issei standup-ready by 09:10. Read yesterday's Claude Code sessions
and recent PR activity on the Issei-curve GitHub account, then render a
three-block standup in his voice. Display only — no file writes.

## The window

"Yesterday" depends on today's weekday:
- Tue–Fri → previous calendar date
- Mon → Friday (skip Sat/Sun; weekend work not counted)

Convert to absolute datetimes before filtering. Today's date is in the
environment context.

## Team vs personal — what counts

The standup is a work artefact. Only Issei's *team* work belongs here.
The personal-vs-team boundary in his global `CLAUDE.md` is hard — apply
it here too.

Team-owned (include):
- Repos: `intech-*` (intech-ai-plugin, intech-data, intech-meta),
  `curve-*` (curve-daas, curve-hackathon-*)
- Jira projects: `INTECH`, `CDT`
- GitHub account: `Issei-curve` only

Personal (exclude):
- Repos and paths: `fpl-platform`, `Other/FPL project`,
  `Knowledge Base/` (including `knowledge-vault/`, `inbox/`, `harvest/`,
  `issei-plugin/`)
- Topics: LinkedIn drafts, CV edits, blog drafts, personal-site work,
  vault distillation, personal-plugin skill development
- GitHub account: `ikuzuki`

Default behaviour:
1. If the session's cwd matches a team repo pattern, presume team work
   and include — unless the session intent is clearly personal (see
   below).
2. If the session's cwd matches a personal path, exclude entirely.
3. If the cwd is ambiguous (`~`, scratch dirs, system folders), judge
   from the first substantive user turn.

Cross-cutting case to watch: a session opened in a *team* cwd whose
actual intent is *personal* — e.g. the cwd is `intech-ai-plugin` but
the work is editing a personal `issei-plugin` skill. Exclude on intent.
This exact case applies to the session that authored this skill.

## Sources

### Claude Code sessions

Sessions live at `C:\Users\IsseiKuzuki\.claude\projects\<project-folder>\<uuid>.jsonl`.
Flat JSONL events per session, one folder per cwd.

1. List `.jsonl` files under `.claude\projects\*\` where the file's
   mtime falls in the window. Either use `find ... -newermt` or check
   the first/last `timestamp` field inside the jsonl. Skip the
   `subagents/` subdirs — those are subagent transcripts, noise here.
2. Decode the project name from the folder, e.g.
   `c--Users-IsseiKuzuki-intech-ai-plugin` → `intech-ai-plugin`. Case-
   insensitive — `c--...` and `C--...` are the same project.
3. Collapse worktrees to the parent: any folder matching
   `<parent>--claude-worktrees-<slug>` rolls up under `<parent>`. Don't
   double-count work that happened in a worktree off the same repo.
4. Exclude scheduled-task autoruns. Sessions where *every* user turn is
   a `<scheduled-task ...>` or `<system-reminder>` wrapper are Claude
   running chores on Issei's behalf, not Issei doing work. The
   `daily-pr-digest` routine is a regular offender — filter it out.
5. Exclude personal sessions per the team-vs-personal rules above.
   Hard-drop any cwd matching `fpl-platform`, `Other/FPL project`, or
   `Knowledge Base/...`. For surviving sessions, check the first
   substantive user turn — if the intent is personal (FPL, LinkedIn,
   CV, blog, vault, personal-plugin), drop it even if the cwd is a
   team repo.
6. For each remaining session, extract *intent*, not transcript:
   - The first substantive user message (skip the wrappers above and
     any `<command-name>` tags)
   - Any `mark_chapter` titles — these signal phase boundaries within
     a session and are gold for capturing what actually happened
   - The last assistant turn only if it summarises a piece of work

Group by project. Don't quote raw session content; render the intent in
Issei's voice.

### GitHub PR activity

Account: `Issei-curve` only (work). Do **not** query the `ikuzuki`
account — that's personal (FPL, personal-site repos, etc) and never
goes in the standup. Check `gh auth status`; if a different account is
active, switch with `gh auth switch --user Issei-curve` before
running the queries.

Two queries:
- `gh search prs --author=@me --updated=">=YYYY-MM-DD" --state=all --json number,title,state,url,repository,updatedAt`
- `gh search prs --review-requested=@me --state=open --json number,title,url,repository` (this feeds Today)

From the first query: opened, merged, commented-on in the window.
From the second: PRs awaiting his review right now.

## Today inference

- Open PRs awaiting Issei's review (from the second `gh` query above)
- In-flight work from yesterday's sessions that didn't merge yet — e.g.
  branches/PRs touched in sessions where the corresponding PR is still
  open
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

No preamble, no postamble, no closing line. Just the block.

Voice: terse, lowercase-friendly, British English, no em-dashes (use
` - `), no corporate-speak, no "I successfully completed" / "I worked
on". State what shipped or moved. Consult the `issei-voice` skill if
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
  personal vault, personal-plugin development, anything from the
  `ikuzuki` GitHub account — all stays personal. The standup is a
  team artefact.
- Padding empty Blockers with "no blockers identified at this time".
  Drop the line.
- Inventing Today. If yesterday ended mid-work, Today is finishing it.
- Treating frustration as a blocker. "This is annoying" is not a
  blocker; "waiting on Adele's review" is.
- Writing anything to a file. This skill is display-only.
