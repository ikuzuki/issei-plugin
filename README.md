# issei-plugin

Personal Claude Code plugin. Bundles Issei's skills, slash commands, and the MCP wiring for [`knowledge-mcp`](https://github.com/ikuzuki/knowledge-mcp) into one installable unit.

Public so Claude Desktop and Cowork can fetch it without an org-level GitHub connector. Nothing in here is secret — the skills encode personal voice and workflow preferences, the commands reference env vars not paths, and the MCP config is generic. Genuinely private content lives in the separate `knowledge-vault` repo.

## What's in it

`skills/` — four skills migrated from `~/.claude/skills/`:

- `issei-voice` — drafts short-to-medium async comms in Issei's voice
- `meeting-agenda` — meeting prep / agenda drafting
- `drawio-diagrams` — generating drawio diagrams
- `skill-creator` — meta-skill for authoring new skills

`commands/` — personal slash commands:

- `/search-vault <query>` — hybrid search over the knowledge vault
- `/distil-session <input>` — turn a Cowork transcript into a vault note

`.mcp.json` — wires the `knowledge` MCP server so vault search/create/update tools are available in every session.

No hooks and no agents yet. Add when friction demands them.

## Install

Prerequisite: [`knowledge-mcp`](https://github.com/ikuzuki/knowledge-mcp) installed and a vault checked out locally.

```powershell
# 1. Clone
git clone https://github.com/ikuzuki/issei-plugin.git "$env:USERPROFILE\Knowledge Base\issei-plugin"

# 2. Set env vars (once per machine)
setx KNOWLEDGE_MCP_BIN         "C:\Users\IsseiKuzuki\Knowledge Base\knowledge-mcp\.venv\Scripts\knowledge-mcp.exe"
setx KNOWLEDGE_MCP_VAULT_PATH  "C:\Users\IsseiKuzuki\Knowledge Base\knowledge-vault"

# 3. Install the plugin into Claude Code
claude plugin install "$env:USERPROFILE\Knowledge Base\issei-plugin"
```

Restart Claude Code (and Claude Desktop if using the MCP there). Confirm:

- `/search-vault something` returns hits
- Skills appear in `/skills` or activate automatically when their descriptions match

## Migrating from `~/.claude/`

After the plugin is installed and working, delete the duplicates so you're not running two copies:

```powershell
Remove-Item -Recurse "$env:USERPROFILE\.claude\skills\issei-voice"
Remove-Item -Recurse "$env:USERPROFILE\.claude\skills\meeting-agenda"
Remove-Item -Recurse "$env:USERPROFILE\.claude\skills\drawio-diagrams"
Remove-Item -Recurse "$env:USERPROFILE\.claude\skills\skill-creator"
```

The global `~/.claude/CLAUDE.md` stays where it is — global identity is not a plugin concern.

Intech-specific commands (`add-collector`, `pr`, `deploy`, etc.) and `rules/intech-conventions.md` are deliberately not in this plugin. They belong in the team/org plugin.

## Layout

```
issei-plugin/
├── .claude-plugin/plugin.json
├── .mcp.json
├── skills/
│   ├── issei-voice/SKILL.md
│   ├── meeting-agenda/SKILL.md
│   ├── drawio-diagrams/SKILL.md
│   └── skill-creator/SKILL.md
├── commands/
│   ├── search-vault.md
│   └── distil-session.md
├── agents/           # empty; add as needed
└── README.md
```

## Adding new skills

Use the bundled `skill-creator` skill. Place the new skill under `skills/<name>/SKILL.md` with a YAML frontmatter `name` and `description`. The description is what Claude matches against — be specific about when the skill should fire.

## Related repos

- [`knowledge-mcp`](https://github.com/ikuzuki/knowledge-mcp) — public MCP server that indexes and serves the vault
- `knowledge-vault` — private; the actual markdown content
