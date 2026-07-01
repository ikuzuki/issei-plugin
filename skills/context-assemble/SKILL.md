---
name: context-assemble
description: Pull all the relevant context for a thing Issei is about to work on - a Jira ticket, a branch, a PR, or a free-text topic - by fanning out every retrieval primitive (Jira, GitHub, Confluence, working-memory, vault) and assembling one ranked bundle of the exact artefacts, then deep-reading only the hits that matter. Use when Issei says "pull the context for X", "get me up to speed on X", "what's the context on CDT-nnn", "gather everything on <topic>", "context for this branch/ticket/PR", or "/context-assemble", and as the grounding step the execution loop (ticket-dispatch) runs before writing a spec. Emits pointers first (cheap), full content on demand. Reads a mix of team sources plus Issei's personal vault - the bundle is for Issei's own use and must never be cited into a team artefact.
---

# Context assemble

The context-router's front-end. Given one anchor, land the exact artefacts across
every source without Issei pointing at them - the fix for "retrieval is meh once
routed" (I always had to say *reference this repo / this page / this ticket*). The
collector script does the fan-out and ranking; this skill does the judgement:
interpret the anchor, read the bundle, deep-read the few hits that matter, and
present a tight context brief.

Scripts live in `C:\Users\IsseiKuzuki\Claude\project-autopilot\scripts\`.

## Step 1 - Assemble the bundle

```
python context_assemble.py "<anchor>" --markdown
```

The anchor is whatever Issei names it - a ticket key (`CDT-410`), a branch
(`CDT-244-pr-digest-cron`), or a topic ("entity classification"). The script detects
the type and derives a good per-source query itself (for a bare key it runs Jira
first and reuses the issue *summary* as the query for the fuzzy sources, which is far
sharper than the key). It runs **all five sources** - each returns empty on a
non-match, so an empty section is a real signal ("no design page exists"), not a
failure. One source erroring never sinks the bundle; it's reported inline.

The bundle is **pointers**, not content: Jira key+link, GitHub repo/path + PR links,
Confluence title+URL, working-memory note identity, vault path+snippet. That keeps
the fan-out cheap.

## Step 2 - Read the bundle, decide what actually matters

Look across the sections and identify the canonical artefacts for this anchor:
the ticket, the design page, where the code lives, whether Issei has touched it
before. Empty sections are informative - say so ("no Confluence page for this").
Rank by relevance to the *task*, not by source.

## Step 3 - Deep-read only the hits you need

The bundle points; now pull full content for the handful that matter, each with its
natural reader:

- **Jira** - full description/comments: `getJiraIssue` (Atlassian MCP), or
  `python context_jira.py "<key>"` for just the summary line again.
- **Confluence** - page body: `getConfluencePage` / the Atlassian `fetch` tool on the
  page URL.
- **GitHub** - a file: `gh` (`gh api` / view raw) or read it locally if the repo is
  cloned; a PR: `gh pr view <n> --repo curveanalytics/<repo>`.
- **Working memory** - `python recall.py show "<branch>"` prints the full note.
- **Vault** - read the file at the given path directly.

Pull two or three, not everything - the point is a focused brief, not a document dump.

## Step 4 - Present the context brief

A short synthesis, most-relevant first: what the ticket asks, the canonical design
page, where the code lives (repo/path + the closest prior PR), any prior working
state or vault note, and the obvious gaps. Plain language. This is the grounding a
spec (or Issei) then works from.

## Boundary - personal vs team

The vault leg reads Issei's **personal** knowledge-vault. The assembled brief is for
Issei's own consumption. Personal context may cite team artefacts, **never** the
reverse - so nothing from the vault section may flow into a team PR, Jira comment, or
Confluence page. If team-facing output needs a vault fact, promote it to Confluence
first (see the personal-vs-team boundary in the global CLAUDE.md).

## Not for

- Replying to messages / triaging what's landed - that's `presence-triage`.
- Assembling the day (calendar + brief) - that's `morning-brief`.
- Doing the work itself - this only grounds it; the execution loop consumes the brief.
