# issei-plugin

Personal Claude Code plugin. Bundles Issei's skills into one installable
unit.

Public so Claude Desktop and Cowork can fetch it without an org-level
GitHub connector. Nothing in here is secret — the skills encode personal
voice and workflow preferences. Genuinely private content lives in the
separate `knowledge-vault` repo.

## What's in it

`skills/` — five skills:

Vault skills (read/write the personal knowledge vault directly via
filesystem; no MCP, no index):

- `search-vault` — find relevant notes by Glob + Grep + Read against
  `knowledge-vault/`. Fires on "what do I have on X", "what did I write
  about Y", etc.
- `distil-vault` — promote raw material (transcripts, harvest outputs,
  inbox notes) into the vault. Writes the new note and updates 5–15
  neighbouring pages with backlinks.
- `lint-vault` — whole-vault consistency pass. Flags broken links,
  missing backlinks, stale references, orphans, contradictions.

Personal skills (migrated from `~/.claude/skills/`):

- `issei-voice` — drafts short-to-medium async comms in Issei's voice
- `meeting-agenda` — meeting prep / agenda drafting

`drawio-diagrams` and `skill-creator` deprecated 2026-05-13 — the team
plugin (`intech-tools`) supplies `drawio-diagram` and pulls in
`skill-creator` as a dependency, so this plugin no longer bundles
duplicates.

No slash commands (skills fire on intent, which is the right shape for
all of these). No MCP servers wired. No hooks, no agents — add when
friction demands them.

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

The global `~/.claude/CLAUDE.md` stays where it is — global identity is
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
│   ├── distil-vault/SKILL.md
│   ├── lint-vault/SKILL.md
│   ├── issei-voice/SKILL.md
│   ├── meeting-agenda/SKILL.md
│   ├── drawio-diagrams/SKILL.md
│   └── skill-creator/SKILL.md
├── agents/           # empty; add as needed
├── commands/         # empty; skills replaced slash commands
└── README.md
```

## Adding new skills

Use the bundled `skill-creator` skill. Place the new skill under
`skills/<name>/SKILL.md` with YAML frontmatter `name` and `description`.
The description is what Claude matches against — be specific about when
the skill should fire.

## Related repos

- `knowledge-vault` — private; the actual markdown content
