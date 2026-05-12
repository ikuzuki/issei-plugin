---
name: search-vault
description: Find and surface relevant notes from Issei's personal knowledge vault by reading the markdown files directly (Glob + Grep + Read). Use this skill whenever the user asks "what do I have on X", "what did I write about Y", "what did I decide about Z", "search my notes", "find that note about W", "what's in the vault on V", "remind me of my thinking on U", or references a topic that's likely captured in the vault. Also use proactively when answering a question that could plausibly be informed by Issei's prior notes — check first, then answer. Do NOT use for live system content (Jira tickets, Confluence pages, GitHub code) — those have their own MCPs.
---

# Search the vault

Read directly from `knowledge-vault/` using Glob, Grep, and Read. There is
no index, no MCP server. The vault is small enough (~few hundred notes)
that whole-file reads on the relevant subset beat any retrieval layer at
this scale.

**Do not reach for `mcp__knowledge__*` tools.** They were deleted on
2026-05-12 and will return "no matching deferred tools found" or
errors. Do not ToolSearch for them either — they are gone. This skill
exists *because* the MCP was retired; using it via Glob/Grep/Read is
the entire point. See `knowledge-vault/decisions/2026-05-12-vault-is-markdown-no-index.md`
for the rationale.

## Process

1. **Read the schema if you haven't this session.** Open
   `knowledge-vault/CLAUDE.md` once to know the folder taxonomy. Don't
   re-read it every search.

2. **Start broad with Glob + Grep.** For a query like "what did I decide
   about X":
   - Glob `knowledge-vault/**/*.md`
   - Grep the keyword(s) and key entities across that file set
   - Use `output_mode: "files_with_matches"` first to see the shape of
     the result, then `content` with context if needed

   Topic-shaped queries: start in the most likely folder
   (`projects/<x>.md` for project queries, `decisions/` for decision
   queries, `patterns/` for technical patterns) and follow links from
   there. The hub-and-spoke structure is deliberate.

3. **Read whole files for the top hits.** Not chunks. Pick 3–5 files
   that look most relevant from the Grep output and Read them in full.
   The whole point of the no-index design is that you have the room to
   load real context.

4. **Follow links.** If a relevant note references another note via
   markdown link or `links` frontmatter, read those too if they look
   plausibly useful. The vault is structured for navigation.

5. **Answer with citations.** Format each cited note as a clickable
   relative path on its own line, with a one-sentence summary of what
   it contributed:

   ```
   Found in the vault:

   - `decisions/2026-05-12-vault-is-markdown-no-index.md` — the
     reasoning for ripping out the embedding pipeline.
   - `projects/knowledge-base.md` — current state of play.

   <answer that synthesises across them>
   ```

6. **Be honest about negative results.** If nothing in the vault matches,
   say so plainly. Don't fabricate. Don't gesture at content that isn't
   there. "I didn't find anything in the vault on X — closest match is
   <Y>, which is adjacent but not the same thing" is a fine answer.

## Tactics for harder queries

- **Acronyms and project names** — vault uses Intech / Curve / Issei's
  own terminology heavily. Grep for both the acronym and the expansion
  (e.g. "CDT" and "Curve Digital Track"; "FoDI" and "field of detection").
- **Decision-shaped queries** — if the user asks "what did I decide
  about X", look in `decisions/` first. The filenames are
  date-stamped and slug-named so the right one is usually obvious from
  Glob alone.
- **People-shaped queries** — `people/` is sensitive; surface contents
  but don't paraphrase in a way that could embarrass the user if read
  aloud.
- **Date-bounded queries** — frontmatter `created` is the truth.
  Filenames in `daily/` and `decisions/` have dates too; you can Glob
  by pattern (`daily/2026-W1*.md`).
- **No-hit broadening** — if Grep on the literal keyword returns
  nothing, broaden to synonyms or related concepts before declaring
  nothing found.

## Anti-patterns

- Calling any `mcp__knowledge__*` tool. Those don't exist any more.
- Stopping at the Grep output without reading the files. Grep tells
  you *which* file matches; you still need the content to answer.
- Reading only one file when 3–5 files would build a fuller picture.
  The vault is hub-and-spoke; one note is rarely the full story.
- Fabricating a quote or a path that wasn't actually in the Read
  output. Cite what you read, nothing more.
- Searching the vault for content that obviously lives elsewhere
  (Jira tickets, Confluence pages, repo code). Route to the right
  MCP instead.
