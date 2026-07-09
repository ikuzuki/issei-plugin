# issei-plugin

Personal Claude Code plugin. Bundles Issei's skills into one installable
unit.

Public so Claude Desktop and Cowork can fetch it without an org-level
GitHub connector. Nothing in here is secret - the skills encode personal
voice and workflow preferences. Genuinely private content lives in the
separate `knowledge-vault` repo.

## What's in it

`skills/` - twenty-four skills, grouped by what they touch.

Vault skills (read/write the personal knowledge vault directly via
filesystem; no MCP, no index):

- `search-vault` - find relevant notes by Glob + Grep + Read against
  `knowledge-vault/`. Fires on "what do I have on X", etc.
- `research-vault` - answer research-shaped questions by scanning the
  vault first, identifying gaps, then filling only the gaps via
  external sources. Internal-vs-external provenance explicitly marked.
- `challenge-vault` - devil's advocate. Argues against a stated
  position using vault evidence. Read-only.
- `distil-vault` - promote raw material (transcripts, harvest outputs,
  inbox notes) into the vault; updates neighbouring pages with backlinks.
- `lint-vault` - whole-vault consistency pass (broken links, missing
  backlinks, stale references, orphans, contradictions).
- `weekly-vault-review` - read-only weekly cadence report on what
  changed, pending inbox/harvest items, themes, light lint findings.

Pipeline / cadence skills (scheduled or routine reports):

- `harvest` - weekly knowledge-base harvest pipeline into
  `harvest/sources.parquet` + weekly rollup. Co-located Python scripts.
- `standup-update` - three-block standup (Yesterday / Today / Blockers)
  from the last weekday's sessions plus GitHub PR activity. Chat only.

Voice / doc skills:

- `issei-voice` - short-to-medium async comms in Issei's voice.
- `blog-voice` - long-form technical writing in Issei's voice.
- `exec-summary` - condense a saturated spike / PoC / doc into a tight,
  outcome-focused doc a human reads in ~5 minutes; anti-AI-slop.

Review / sprint skills:

- `turbo-pr-review` - lightweight human-in-the-loop PR walkthrough;
  drafts inline comments in Issei's voice, posts only on explicit
  confirmation. Lighter than `intech-tools:code-review`.
- `pr-review-loop` - autonomous, scheduled review over the CDT team's
  open PRs; posts a neutral verdict + inline comments, always defers
  approval and merge to a human.
- `sprint-review-retro` - personal review + retro talking points, mined
  from Claude Code sessions against the live CDT sprint doc.
- `sprint-demo-slide` - single-page HTML sprint-demo slide in Issei's
  visual style.
- `jira-board-hygiene` - surfaces Issei's own CDT board drift (closed-
  sprint stragglers, no-sprint, stale-in-progress) and suggests moves;
  applies them only on confirmation. Read-and-suggest by default.

Autopilot - presence, memory, and execution (part of Project Autopilot;
these drive a dedicated local automation browser over CDP plus local
scripts, with human gates throughout - see the note below):

- `working-memory` - handoff / resume / recall of per-branch working
  state across sessions.
- `morning-brief` - assembles the day (mid-flight work, PRs awaiting
  review, own open PRs, in-progress Jira, a proposed deep-block plan);
  catch-up mode for leave-return.
- `presence-triage` - the cockpit for the presence layer: digest what's
  landed across Teams + Outlook, show a recommended (already drafted)
  reply / action, gated send (Issei always presses send).
- `context-assemble` - the context-router: from a ticket / branch /
  topic, fan out every retrieval primitive (Jira, GitHub, Confluence,
  working-memory, vault) into one ranked bundle of the exact artefacts.
- `ticket-dispatch` - the execution loop: a Jira ticket to a reviewable
  draft PR (ground -> spec + gate -> worktree -> implement -> verify ->
  draft PR + gate). Two hard human gates; never auto-merges.
- `scoro-timesheet` - fill the Scoro timesheet over CDP; proposes a
  plan, fills on confirmation, never submits.

Other:

- `meeting-agenda` - meeting prep / agenda drafting.
- `aws-saa-revision` - interactive quick-fire AWS Solutions Architect
  Associate drilling against local notes with a living progress doc.

`drawio-diagrams` and `skill-creator` deprecated 2026-05-13 - the team
plugin (`intech-tools`) supplies `drawio-diagram` and pulls in
`skill-creator` as a dependency, so this plugin no longer bundles
duplicates.

Most skills fire on intent; any can be invoked by name (e.g.
`/morning-brief`, `/context-assemble`, `/ticket-dispatch`). No MCP
servers wired here, no hooks, no agents.

> **Autopilot skills need `project-autopilot`.** The Autopilot family
> (working-memory, morning-brief, presence-triage, context-assemble,
> ticket-dispatch, scoro-timesheet) calls Python scripts and a dedicated
> already-authenticated automation browser that live in the separate
> private `project-autopilot` repo, not here. This plugin ships only the
> skill definitions; without that repo (and, for the presence/Scoro/
> dispatch skills, the running automation Edge) they won't fully work.

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
│   ├── harvest/SKILL.md               # + scripts/
│   ├── standup-update/SKILL.md
│   ├── issei-voice/SKILL.md
│   ├── blog-voice/SKILL.md            # + references/
│   ├── exec-summary/SKILL.md
│   ├── turbo-pr-review/SKILL.md
│   ├── pr-review-loop/SKILL.md        # + build.py, references/
│   ├── sprint-review-retro/SKILL.md
│   ├── sprint-demo-slide/SKILL.md     # + references/
│   ├── jira-board-hygiene/SKILL.md    # scripts in project-autopilot
│   ├── working-memory/SKILL.md        # Autopilot; scripts in project-autopilot
│   ├── morning-brief/SKILL.md         # Autopilot
│   ├── presence-triage/SKILL.md       # Autopilot
│   ├── context-assemble/SKILL.md      # Autopilot
│   ├── ticket-dispatch/SKILL.md       # Autopilot
│   ├── scoro-timesheet/SKILL.md       # Autopilot
│   ├── meeting-agenda/SKILL.md
│   └── aws-saa-revision/SKILL.md
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
