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

2. **Enumerate the vault.** Glob `knowledge-vault/**/*.md`. Skip
   `**/README.md` for some checks (they describe folders, they don't
   belong to the folder's content) but include them for link-validity
   checks.

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
     suspicious elsewhere
   - Contradiction between a `decisions/` note and later
     `patterns/` / `projects/` content. Flag for human review — do
     not auto-resolve
   - Note written directly to `daily/` outside the harvest format
     (manual edits to weekly rollups are fine; new files are not)

   **Low severity:**
   - H1 doesn't match `title` frontmatter
   - `tags` use inconsistent casing or non-hyphenated forms
   - Title is a full sentence rather than a noun phrase
   - File hasn't been touched in >6 months and is in a fast-moving area
     (`projects/`, `strategy/`) — candidate for review, not necessarily
     edit
   - Note that should plausibly cross-link to a hub (`projects/<x>.md`)
     but doesn't

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

7. **Don't auto-fix decision contradictions.** If a later note disagrees
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
