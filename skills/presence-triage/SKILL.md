---
name: presence-triage
description: The cockpit for Issei's presence layer - digest what's landed across Teams and Outlook since the last check, show each thing that needs him in plain language with a recommended reply (already drafted) or action, iterate on the drafts, and hand off a gated send (Issei always presses send). Use when Issei says "triage", "triage my messages", "presence", "any messages I need to reply to", "check my Teams", "what's come in", "/presence-triage", or after a presence desktop toast fires. Reads via the dedicated automation Edge (CDP) - the same authenticated session the presence scripts use. Never sends, never auto-acts. Distinct from standup-update (team-facing backward summary) and morning-brief (day assembly); this is the reply-to-what-came-in loop.
---

# Presence triage

The interactive front-end to the presence scripts in `project-autopilot`. The toast
is just the nudge ("N need a reply"); this is where Issei digests what happened, sees
the recommended reply/action, iterates, and sends. Scripts do the plumbing (poll,
classify, thread-read, draft); this skill does the judgement and the conversation.

**Precondition:** the dedicated automation Edge must be running (it holds the
authenticated M365 session; CDP is `localhost:9222`). If the readers error with
"sources unreachable", tell Issei to run `launch_automation_edge.ps1` and retry -
don't fall back to anything that would need a fresh login.

## Flow

Run from `C:\Users\IsseiKuzuki\Claude\project-autopilot\scripts\`.

1. **Get the current picture.** `python presence_poll.py --markdown` - a fresh poll,
   classified, new-since-last-check only. (Or read `captures/presence_triage.json` if
   you just want the last poll without re-hitting the browser.)
2. **Deepen the needs-reply items.** For each Teams item that needs a reply,
   `python presence_draft.py --chat "<name>"` - it reads the actual thread and
   re-assesses (skips social/resolved), then drafts in Issei's voice. Trust the
   re-assess: if it says no reply needed, drop it from the "needs you" list.
3. **Present, don't dump.** For each item that genuinely needs Issei:
   - *who / what*, in plain English (a teammate who hasn't seen the thread should get it)
   - the **recommended reply** (the draft), or for a task the **recommended action**
     ("this is asking you to do X, not reply - add it / it's CDT-NNN")
   Then a short tail of FYI / action-elsewhere items so he sees what else landed, and
   flag any `capture`-worthy items (offer to distil to the vault - see Capture).
4. **Iterate in the chat.** "warmer", "shorter", "push back on that", "just the first
   one", "why does this need me?" - redraft via `issei-voice` (+ `voice/*` refs),
   re-read the thread with `teams_thread.py` if more context is needed.
5. **Gated send (Issei always sends).** On an explicit "send that" / "reply to X":
   open the thread in the automation Edge so it's in front of him and present the
   final text to paste and send. Auto-typing the compose box (pre-fill, stop on the
   cursor) is the planned upgrade; until it's built and tested, hand off the text +
   the open thread. Never press send, never pick a recipient he hasn't seen.

## Capture (feeds the memory tiers)

The poll flags durable items (`capture: true`) and logs them to
`working-state/_presence-capture.md` (Tier 2). When something is genuinely durable -
a decision, a commitment, a key fact - offer to promote it to the vault via
`distil-vault` (Tier 3). Presence is a capture *source* into the existing memory,
not a new store.

## Boundaries

Read + draft only. Never sends, never auto-acts, never touches the presence
indicator. Work-focused - personal and banter are filtered by the classifier and the
re-assess gate; if something personal slips through, drop it, don't draft it. The
automation Edge is Issei's real authenticated session, so treat it with care: read
freely, but the only write is a reply Issei has explicitly approved and sends himself.

## Composition

`presence_poll.py` (poll + classify), `presence_draft.py` + `teams_thread.py`
(thread context + draft), `issei-voice` (+ `knowledge-vault/voice/*`) for wording,
`cal_read.py` if a reply needs Issei's availability, `distil-vault` for capture.
Runs on the same CDP substrate as the rest of the presence layer.
