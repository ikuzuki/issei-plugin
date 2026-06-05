# issei-plugin

Personal Claude Code plugin. Bundles Issei's skills into one installable
unit.

Public so Claude Desktop and Cowork can fetch it without an org-level
GitHub connector. Nothing in here is secret - the skills encode personal
voice and workflow preferences. Genuinely private content lives in the
separate `knowledge-vault` repo.

## What's in it

`skills/` - twelve skills, grouped by what they touch.

Vault skills (read/write the personal knowledge vault directly via
filesystem; no MCP, no index):

- `search-vault` - find relevant notes by Glob + Grep + Read against
  `knowledge-vault/`. Fires on "what do I have on X", "what did I write
  about Y", etc.
- `research-vault` - answer research-shaped questions by scanning the
  vault first, identifying gaps, then filling only the gaps via
  external sources (WebSearch / WebFetch / Atlassian MCP / gh /
  Context7). Internal-vs-external provenance explicitly marked.
- `challenge-vault` - devil's advocate. Argues against a stated
  position using vault evidence (decisions, patterns, prior stance).
  Read-only.
- `distil-vault` - promote raw material (transcripts, harvest outputs,
  inbox notes) into the vault. Writes the new note and updates 5-15
  neighbouring pages with backlinks.
- `lint-vault` - whole-vault consistency pass. Flags broken links,
  missing backlinks, stale references, orphans, stale temporal
  references, stale TBC/TBD markers, dead person references,
  contradictions.
- `weekly-vault-review` - read-only weekly cadence report. Surfaces
  what changed in the vault this week, pending inbox/harvest items,
  themes, light lint findings, suggested actions. Designed to run on
  a weekly schedule.

Pipeline / cadence skills (scheduled or routine reports):

- `harvest` - weekly knowledge-base harvest pipeline. Extracts the
  week's Claude Code sessions, Confluence pages, and GitHub PRs/reviews
  into `harvest/sources.parquet`, writes the weekly rollup, commits the
  vault. Co-located Python scripts under `harvest/scripts/`.
- `standup-update` - three-block standup (Yesterday / Today / Blockers)
  from the last weekday's Claude Code sessions plus GitHub PR activity.
  Renders to chat only; no file writes.

Voice / doc skills:

- `issei-voice` - drafts short-to-medium async comms in Issei's voice
- `blog-voice` - drafts long-form technical writing in Issei's voice
- `exec-summary` - condense a saturated spike / PoC / working doc into a
  tight, outcome-focused doc a human reads in ~5 minutes; anti-AI-slop

Review skills:

- `turbo-pr-review` - lightweight human-in-the-loop PR walkthrough.
  Fetches the PR, explains it in plain English with jargon unpacked,
  flags potential issues, drafts inline comments in Issei's voice,
  surfaces drafts, posts only on explicit confirmation. Handles
  multi-PR grouping when PRs share a ticket / contract / dependency.
  Designed as a lighter alternative to `intech-tools:code-review` -
  no specialist sub-agents, no auto-posting.

Other:

- `meeting-agenda` - meeting prep / agenda drafting

`drawio-diagrams` and `skill-creator` deprecated 2026-05-13 - the team
plugin (`intech-tools`) supplies `drawio-diagram` and pulls in
`skill-creator` as a dependency, so this plugin no longer bundles
duplicates.

Most skills fire on intent. Two are also user-invocable as slash
commands: `/meeting-agenda` and `/exec-summary`. No MCP servers wired.
No hooks, no agents - add when friction demands them.

## Install

```powershell
# 1. Clone
git clone https://github.com/ikuzuki/issei-plugin.git "$env:USERPROFILE\Knowledge Base\issei-plugin"

# 2. Install into Claude Code
claude plugin install "$env:USERPROFILE\Knowledge Base\issei-plugin"
```

Restart Claude Code. Confirm skills appear in `/skills` or activate
automatically when their descriptions match.

The vault skills assume the vault lives at
`$env:USERPROFILE\Knowledge Base\knowledge-vault`. If the vault is
elsewhere, adjust paths in the skill descriptions accordingly (or
symlink).

## Migrating from `~/.claude/`

After the plugin is installed and working, delete the duplicates so
you're not running two copies of the personal skills:

```powershell
Remove-Item -Recurse "$env:USERPROFILE\.claude\skills\issei-voice"
Remove-Item -Recurse "$env:USERPROFILE\.claude\skills\meeting-agenda"
Remove-Item -Recurse "$env:USERPROFILE\.claude\skills\drawio-diagrams"
Remove-Item -Recurse "$env:USERPROFILE\.claude\skills\skill-creator"
```

The global `~/.claude/CLAUDE.md` stays where it is - global identity is
not a plugin concern.

Intech-specific commands (`add-collector`, `pr`, `deploy`, etc.) and
`rules/intech-conventions.md` are deliberately not in this plugin. They
belong in the team / org plugin.

## Layout

```
issei-plugin/
├── .claude-plugin/plugin.json
├── skills/
│   ├── search-vault/SKILL.md
│   ├── research-vault/SKILL.md
│   ├── challenge-vault/SKILL.md
│   ├── distil-vault/SKILL.md
│   ├── lint-vault/SKILL.md
│   ├── weekly-vault-review/SKILL.md
│   ├── harvest/SKILL.md            # + scripts/
│   ├── standup-update/SKILL.md
│   ├── issei-voice/SKILL.md
│   ├── blog-voice/SKILL.md         # + references/
│   ├── exec-summary/SKILL.md
│   └── meeting-agenda/SKILL.md
├── agents/           # empty; add as needed
├── commands/         # empty; user-invocable skills cover slash-command needs
└── README.md
```

## Adding new skills

Use the `skill-creator` skill (from the team `intech-tools` plugin).
Place the new skill under `skills/<name>/SKILL.md` with YAML frontmatter
`name` and `description`. The description is what Claude matches against -
be specific about when the skill should fire.

## Related repos

- `knowledge-vault` - private; the actual markdown content
