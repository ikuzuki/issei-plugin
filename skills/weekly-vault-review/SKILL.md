---
name: weekly-vault-review
description: Run a weekly read-only review of Issei's personal knowledge vault — surface notes touched or created this week, identify patterns and themes, flag what didn't get captured, propose distil candidates from the inbox and harvest pipelines, and run a quick lint pass. Use this skill when the user says "weekly review", "run my weekly vault review", "what happened in the vault this week", "what should I distil this week", or when a scheduled routine fires. Output is a structured report; never writes to the vault, never auto-distils, never auto-fixes lint findings. Designed to run on a weekly cadence (manual or scheduled).
---

# Weekly vault review — read-only health and patterns pass

A weekly cadence skill that gives Issei a structured view of:

- What changed in the vault this week
- What's sitting in `inbox/` and `harvest/` that hasn't been distilled
- What patterns or themes are emerging across the recent notes
- What hygiene issues `lint-vault` would flag (summary only — full
  lint is a separate call)
- What's worth deciding to do in the coming week

Designed to run on a weekly schedule (e.g. Friday afternoon or Sunday
evening) or on demand. **The output is a report, not vault edits.**
The whole point is to give Issei a thinking surface; he chooses what
to action.

## When to use

- The user explicitly says "weekly review" / "run my weekly vault
  review".
- A scheduled routine fires this skill (see "Scheduling" below).
- The user asks "what happened in the vault this week" / "what
  should I distil this week".
- After a busy week to surface what didn't make it into the vault.

Do not fire this skill for ad-hoc vault questions — those are
`search-vault` or `research-vault`.

## Process

1. **Determine the review window.** Default: last 7 days from now.
   If the user gives a different window ("last two weeks", "since
   the CDT planning session"), use that. Capture the window in the
   report header.

2. **Read the schema if you haven't this session.** Open
   `knowledge-vault/CLAUDE.md` for folder taxonomy.

3. **Find vault activity in the window.**
   - Run `git -C "$VAULT" log --since="<window>" --name-only --pretty=format:"%H|%ai|%s"`
     where `$VAULT` is `knowledge-vault/`. This gives every commit
     with timestamp, message, and files touched.
   - Group commits into: new files (added), modified files, deleted
     files.
   - For each new file, capture the path and a one-line description
     from the file's lede.
   - For each modified file, capture the path and the commit message
     for context.

4. **Survey the inbox.** Glob `inbox/*.md`, `inbox/*.docx`, and
   `inbox/*.txt` (and any other extensions present). For each item:
   - Filename
   - Approximate size / lines
   - Date dropped (file mtime)
   - One-line guess at content from the first paragraph (or
     filename) if it's a markdown file

   This is the "what's pending distillation" list.

5. **Triage the harvest output — top promotion candidates.** This is
   the harvest → distil gate. Without it, the harvest grows faster
   than `distil-vault` keeps up, and the curated layer falls behind.

   Scope: glob `knowledge-vault/reference/sessions/YYYY-Www/` for
   the current week's session files (and last week's if the review
   window covers it). Also glob `harvest/` for any pending parquet
   or extracts that haven't yet been folded into the session
   archive.

   Rank by promotion-worthiness. Read the YAML frontmatter of each
   session file (cheap — just the block, not the body) and score
   on these signals:

   - **Length.** Sessions over ~5000 chars carry real depth. Short
     ones are usually one-off Qs.
   - **Files touched.** `files_touched: 3+` means cross-file work,
     not a single-file edit. Multi-file sessions are usually
     pattern-generating.
   - **Topic novelty.** Grep the curated vault for the session's
     main topic (extracted from title). If the topic appears in 0-1
     curated notes, the session may be filling a real gap. If it
     appears in 5+, the session is likely re-covering ground.
   - **Decision / pattern signal.** Grep the session body (Read
     with offset/limit if large) for phrases that signal durable
     content: "decided", "going with", "rejected", "the pattern
     is", "the trick is", "in retrospect", "i'd lean".

   Score each session loosely high / medium / low across the four
   signals combined. Read the top 3-5 candidates' first ~200 lines
   to confirm; don't promote anything you can't justify.

   **Tag each candidate with a consumer** — who will actually read
   the distilled note. Knowledge with no reader rots, so this is a
   gate, not a label: `team-adr` / `team-confluence` (a reusable
   decision or pattern worth promoting to a team artefact),
   `personal-lab-prep` / `personal-saa` (feeds Issei's learning /
   role-prep track), or `personal-reference` (future-Issei on the
   same system). **If a candidate has no plausible consumer, don't
   surface it** — a note nobody will revisit isn't worth the distil.

   Cap output at 5 candidates. More than 5 means the rank failed;
   tighten it. Fewer than 3 is fine - the harvest doesn't always
   produce promotables.

   Don't read parquet directly; identify files and signals only.
   Distillation from harvest is a `distil-vault` call the user
   makes, not this skill.

6. **Light pattern detection.** Look across this week's vault
   changes for:
   - **Theme repetition.** Multiple notes touching the same project,
     person, or technical concept. May indicate a pattern worth
     promoting to its own note, or a hub that needs updating.
   - **Open questions surfaced.** New notes that flag "open
     question", "TBC", "TBD", "decide later" — collect these.
   - **Decisions made.** New `decisions/` entries this week, plus
     `Status:` changes on existing ones.
   - **People activity.** Updates to `people/` notes — who's been
     active in your week.

   Don't over-analyse. Surface what's visibly there; don't invent
   patterns.

7. **Quick lint summary.** Run a *fast* lint pass — not the full
   `lint-vault` skill. Just check:
   - Notes created this week with missing frontmatter
   - Notes created this week with broken outbound links
   - Notes created this week that should plausibly cross-link to a
     hub but don't

   This catches new-content hygiene before it becomes accumulated
   debt. The full `lint-vault` skill is a separate, deeper pass.

8. **Optional: distil candidates from inbox/harvest.** For each
   pending inbox item, suggest a target folder/path based on the
   content shape — but do not auto-distil. The output is "here's
   what I'd promote and where"; the user runs `distil-vault` if they
   agree.

9. **Structure the report.** Format:

   ```
   # Weekly vault review — <window>

   ## Activity

   - **New notes (N):** path — one-line description
   - **Modified notes (N):** path — commit message
   - **Deletions (N):** path — reason if known

   ## Themes this week

   - <theme>: appears in <paths>. <one-line note on the pattern>
   - <theme>: ...

   ## Pending distillation

   ### Inbox (N items)
   - `inbox/<filename>` — <one-line guess at content>.
     Suggested target: `<folder>/<slug>.md`

   ### Harvest triage — top promotion candidates

   1. `reference/sessions/YYYY-Www/<file>` — <one-line topic>.
      Signal: <length / files-touched / topic-gap / decision-shape>.
      Consumer: <team-adr | team-confluence | personal-lab-prep |
      personal-saa | personal-reference>.
      Suggested target: `<folder>/<slug>.md`.
      Suggested action: `distil-vault` on this with framing
      "<short framing for what to extract>".
   2. ...

   (Cap at 5. "No promotion candidates this week" is a valid
   output - say so explicitly rather than padding.)

   ## Open questions surfaced

   - <question>: flagged in `<path>`
   - <question>: ...

   ## Lint check (this week's content)

   - <finding>: `<path>`. Fix: <one-liner>.
   - ...
   (or: "No new hygiene issues in this week's content.")

   ## Suggested actions

   - <one-line action> — run <skill> on <target>
   - <one-line action> — review <topic>
   ```

   Keep it dense. The user reads this in 2 minutes, not 20.

10. **Don't auto-execute.** Every suggested action is a separate
    skill call the user makes. The review surfaces; the user acts.
    This is the property that keeps the curation gate intact.

## Scheduling

This skill runs as the **second stage of the `weekly-knowledge-harvest`
routine** (Monday, right after `harvest` lands last week's sessions), so
it reviews a fully-harvested week. When fired that way it runs unattended,
so it does one extra thing a manual call doesn't: **persist its report to
`inbox/_distil-candidates-YYYY-Www.md`** so the candidates are a standing
surface Issei reviews when he's next present (a chat-only report from an
unattended run would evaporate). Writing its *own report* to `inbox/` is
fine — `inbox/` is the staging area, not the curated vault; the read-only
contract is about never editing curated notes, which still holds.

Whether scheduled or manual, produce the report and stop. Don't
auto-distil, don't auto-fix, don't edit curated notes. The persisted
candidate list is a to-do surface; Issei runs `distil-vault` on the ones
he picks.

The scheduling is intentionally light. Daily reviews would be noise
at this vault size; weekly is the cadence where patterns become
visible.

## Anti-patterns

- **Writing to the *curated* vault.** Read-only there, always. Even
  "obvious" fixes go in the suggested-actions section, not auto-applied.
  (Persisting the review's own report to `inbox/` when scheduled is the
  one allowed write — staging, not curation.)
- **Auto-distilling pending inbox items.** Tempting and wrong.
  Distillation is a deliberate `distil-vault` call. The review
  flags candidates; it doesn't promote them.
- **Running the full `lint-vault` skill.** That's a separate,
  deeper pass. The weekly review does light lint only — new
  content hygiene, not whole-vault audit.
- **Inventing themes that aren't there.** If the week was quiet,
  say so. "Nothing notable this week" is a valid review output.
- **Reporting on `reference/` activity.** That's the gitignored
  auto-mirror. Stick to the curated vault.
- **Long reports.** Target two minutes of reading. Dense bullets,
  not paragraphs. The user has limited time at review moments.
- **Editorialising.** Surface what's there; don't moralise about
  "you should have done X". That's not what the review is for.

## When NOT to use

- Mid-week ad-hoc queries — use `search-vault` or `research-vault`.
- Deep vault hygiene audit — use `lint-vault` directly.
- When the user asks for action, not reflection — pick the right
  skill for the action they want.
- Multiple times in the same day — the review is weekly for a
  reason; rapid repeat fires produce noise.
