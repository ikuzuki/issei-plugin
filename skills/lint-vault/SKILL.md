---
name: lint-vault
description: Run a whole-vault consistency pass over Issei's personal knowledge vault, surfacing broken links, missing reciprocal backlinks, orphan pages, stale references to deleted infrastructure, contradictions between decisions and later notes, and notes with missing or malformed frontmatter. Use this skill when the user says "lint the vault", "check vault health", "audit my knowledge base", "find broken links in the vault", "vault consistency check", "what's stale in the vault", or after a large distillation pass / structural change. Outputs a report; human approves edits before they land.
---

# Lint the vault

Whole-vault consistency pass. The vault is small enough (~few hundred
notes) to read in full inside Claude's context window — so this skill
literally reads all of it, checks for the failure modes below, and reports.

## Process

1. **Read the schema first.** Open `knowledge-vault/CLAUDE.md`. The
   schema is the lint target — every rule in this skill is derived from
   what that file says, not from independent invention. If the schema and
   this skill disagree, the schema wins.

2. **Enumerate the curated vault.** Glob `knowledge-vault/**/*.md` but
   **exclude `knowledge-vault/reference/**`** — that path is the
   gitignored auto-mirror of Confluence + GitHub produced by the
   `harvest` skill's `sync_reference.py`. It's reference material, not
   curated content; linting it produces noise on files Issei doesn't
   own. Also skip `**/README.md` for some checks (they describe folders,
   they don't belong to the folder's content) but include them for
   link-validity checks.

   Note the singular/plural distinction: `reference/` (singular,
   gitignored, auto-mirror) is excluded. `references/` (plural, curated
   external pointers — part of the schema) is included.

3. **Read every note.** Yes, all of them. Whole-file reads, not chunks.
   Track:
   - Path
   - Frontmatter (parsed): `title`, `created`, `tags`, `links`
   - All outbound markdown links from the body (`[text](path)`)
   - H1 line
   - File size / token count rough estimate

4. **Run the checks.** Each finding gets: severity (high / medium / low),
   path, one-sentence description, suggested fix.

   **High severity:**
   - Broken outbound link — points to a path that doesn't exist
   - Stale infrastructure reference — mentions `knowledge-mcp`,
     `mcp__knowledge__*` tools, `LanceDB`, `Ollama` embedding pipeline,
     the file watcher, the FTS index, or the `/search-vault` /
     `/distil-session` slash commands. All deleted per
     `decisions/2026-05-12-vault-is-markdown-no-index.md`. Replacement
     guidance: skills (`search-vault`, `distil-vault`, `lint-vault`)
     and direct filesystem tools.
   - Edit to a historical `decisions/` file that changes the recorded
     view (check git history if available) — decisions are immutable.
     The one allowed edit is updating `Status:` to
     `superseded by <link>`.

   **Medium severity:**
   - Missing required frontmatter (`title`, `created`)
   - `links` array contains a path that doesn't exist
   - Reciprocal-backlink miss — A's `links` includes B, but B's `links`
     doesn't include A
   - Orphan page — note has zero inbound links from anywhere in the
     vault. Acceptable for some `daily/` and `decisions/` entries;
     suspicious elsewhere. For non-hub pages outside `daily/` and
     `decisions/`, orphan status is a real findng — surface with
     suggested hub to link from
   - Contradiction between a `decisions/` note and later
     `patterns/` / `projects/` content. Flag for human review — do
     not auto-resolve
   - Note written directly to `daily/` outside the harvest format
     (manual edits to weekly rollups are fine; new files are not)
   - **Stale temporal reference.** Note contains phrases like "next
     week", "this sprint", "currently", "this quarter", "in the
     coming days" combined with a `created` date more than 6 weeks
     old. Likely the content has aged out of accuracy. Flag with the
     specific phrase and the staleness window
   - **Stale "TBC / TBD / open question" markers.** Note flags
     something as TBC / TBD / "to be decided" / "open question" and
     was last touched more than 3 months ago. Either resolve and
     update, or migrate the question into a `questions/` note (if
     the vault has that folder), or accept the marker is permanent
     and rephrase to remove the implicit "this will be answered
     soon" framing
   - **Dead person reference.** Note references a colleague by name
     in a "what they own / what they're working on" framing, but
     no `people/<name>.md` exists. Either add the people note or
     soften the framing. (Note: this catches the easy case; doesn't
     detect colleagues who've left the team — that needs a
     deliberate list to lint against, which doesn't exist yet)
   - **Stale synthesis.** A `strategy/`, `patterns/`, `playbooks/`,
     or `team-enablement-notes/` page with `status: current` and
     `updated` more than 90 days old. Surface for re-affirmation,
     supersession, or content refresh. Don't auto-flip status.
   - **Missing synthesis status.** Same folders, page without a
     `status:` field. Treat as a first-time-tagging finding;
     suggest `status: current` and `updated: <created or today>`.
   - **Source-page hygiene.** A `references/<x>.md` page missing
     required source-page frontmatter (`upstream`, `last_synced`,
     `ingested`). Schema mandates these per the source-page rule
     in `knowledge-vault/CLAUDE.md`.
   - **Stale source sync.** A `references/<x>.md` page with
     `last_synced` more than 60 days old. Suggest a manual re-sync
     (re-read the upstream, bump `last_synced`). If the upstream is
     gone, switch the page to mirrored body and note the deprecation.
   - **Emergent hub candidate.** A `tags:` value appearing on 4+
     curated notes with no hub of the same name. Strong signal
     that an area has accumulated enough material to deserve a
     stable entry point. Output: the tag, the files using it, and
     a suggested hub path (likely `projects/<tag>.md`,
     `strategy/<tag>.md`, or `patterns/<tag>.md` depending on
     content shape). The emergent-pattern detector lives here
     because it's structural and quarterly-paced; week-level theme
     emergence stays in `weekly-vault-review`.

   **Low severity:**
   - H1 doesn't match `title` frontmatter
   - `tags` use inconsistent casing or non-hyphenated forms
   - Title is a full sentence rather than a noun phrase
   - File hasn't been touched in >6 months and is in a fast-moving area
     (`projects/`, `strategy/`) — candidate for review, not necessarily
     edit
   - Note that should plausibly cross-link to a hub (`projects/<x>.md`)
     but doesn't
   - **Unsourced claim in a `patterns/` or `strategy/` note.**
     Patterns and strategy notes should be grounded in a source
     (Confluence link, decision, prior project). A pattern note with
     no Source footer and no inline citations is suspicious — it
     might still be right but the provenance has decayed

5. **Report.** Group by severity, then by folder. Each finding is one
   bullet:

   `[HIGH] <path>: <description>. Fix: <suggested edit>.`

   At the top of the report:
   - Total notes scanned
   - Total findings by severity
   - Anything that looks systemic (e.g. "12 notes still reference
     `mcp__knowledge__search` — likely a sweep is needed")

6. **Offer to fix.** After the report, ask Issei which findings to
   action. Group fixes by:
   - **Mechanical** — broken links, stale infra references, missing
     reciprocal backlinks. Safe to batch.
   - **Judgment** — orphans, contradictions, stale-area review. Each
     needs Issei's call.

   On confirmation, make the edits in one pass using Edit. Don't fix
   piecemeal across multiple confirmations — that fragments the audit.

7. **Regenerate `knowledge-vault/index.md`.** Walk the curated layer
   (exclude `reference/` and folder READMEs) and produce a fresh
   catalog grouped by folder. Format:

   ```
   # knowledge-vault index

   Last generated: YYYY-MM-DD by lint-vault.
   Total notes: N.

   ## decisions/
   - `decisions/YYYY-MM-DD-<slug>.md` — <title> [<status>]
   - ...

   ## projects/
   - `projects/<slug>.md` — <title>
   - ...

   [continue per folder]
   ```

   Sort within each folder: date-prefixed files reverse-chronological,
   others alphabetical by filename. Always run, even when no fixes
   were applied - new files may have arrived since last lint. Cheap
   operation; no need to gate.

8. **Commit.** Stage approved fixes + regenerated `index.md` in one
   commit. Message: `lint: <short summary>` (e.g.
   `lint: fix 12 broken links + refresh index`, or
   `lint: refresh index` when nothing else changed). Follow house
   convention (terse, imperative, lowercase first word, no emoji, no
   Claude co-author). Don't push - Issei pushes when state should
   leave the machine. If nothing actually changed (no fixes, index
   already current), skip the commit.

9. **Don't auto-fix decision contradictions.** If a later note disagrees
   with a `decisions/` entry, that might mean: the decision is
   superseded (write a new dated decision), the later note is wrong
   (edit the later note), or both are valid in different contexts (no
   change needed). Surface it; Issei decides.

## Anti-patterns

- Editing `decisions/` files to "fix" contradictions. They're immutable.
- Auto-deleting orphan pages. Some orphans are intentional; ask.
- Treating `daily/` entries as first-class notes for backlink purposes.
  They're activity logs; expecting reciprocal links into and out of
  them is wrong.
- Flagging every README as an orphan. READMEs describe folders, not
  content, and don't need inbound links from notes.
- Running the lint in a worktree or scratch copy — always lint the
  live vault, otherwise the report doesn't match reality.
- Trying to fix everything in one turn. A typical run surfaces 20–50
  findings. Triage, batch the mechanical ones, defer the judgment
  ones to follow-up turns.

## When to run

- After a `distil-vault` pass that touched many neighbours
- After deleting infrastructure (like the May 2026 knowledge-mcp removal)
- On a quarterly cadence as vault hygiene
- When the vault "feels stale" — broken navigation, dead links
- Never on a schedule unless Issei sets one explicitly. Distillation and
  lint are deliberate operations, not background jobs.

## Relationship to weekly-vault-review

The `weekly-vault-review` skill runs a *fast* lint over content created
or modified in the past week — catches new-content hygiene before it
accumulates. This skill is the full pass: every note, every rule. Run
this one quarterly or after structural changes; let the weekly review
catch new content.
