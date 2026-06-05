---
name: turbo-pr-review
description: Walk through a GitHub PR in plain English, surface potential issues with jargon unpacked, draft inline review comments in Issei's voice, then post only on explicit confirmation. Use this skill when the user pastes a PR URL or PR number and says "review this PR", "have a crack at this PR", "have a crack at this" (when PR context is established), "walk me through this PR", "explain what this PR is doing", "explain this PR in plain English", "in laymen's terms", "what does this PR do", "thoughts on this PR", "take a look at this PR", "what do you make of #N", "draft review comments for this PR", "draft inline comments for this PR", "help me review this", or hands over multiple PR URLs/numbers in one message. Also fires on "review these together", "look at these in conjunction", or when the user is reviewing PRs from the cdt-daily-pr-digest. Handles multi-PR scenarios by grouping related PRs (shared Jira ticket, explicit cross-PR dependency, shared API contract) and splitting unrelated ones. A lightweight alternative to the heavy `intech-tools:code-review` skill — no specialist sub-agents, no citation gate, no SemVer audits, no auto-posting. Do NOT use for deep multi-agent audits (use `intech-tools:code-review` for those), drafting PR descriptions (use `issei-voice`), drafting comments on Confluence docs or Jira tickets (use `issei-voice`), or reviewing code that hasn't been raised as a PR yet. Composes with `issei-voice` and the voice rules at `knowledge-vault/voice/code-review.md`.
---

# Turbo PR Review

Walk a GitHub PR end-to-end at Issei's pace: pull the PR, explain it in plain English with jargon unpacked, flag what's worth raising, draft inline comments in voice, surface drafts, post only on explicit confirmation. A lighter-weight companion to `intech-tools:code-review` — that skill spawns nine specialist agents and auto-posts; this one is a single pass that keeps the human in the loop at every step.

The skill is shaped around the reviewer not being deeply close to every PR they review. Issei sits across CDT and needs to land thoughtful comments on backend, infra, frontend, and shared-library PRs — often without having written the surrounding code. So the explainer phase is genuinely load-bearing: it unpacks acronyms, unpacks why-this-matters, and only then moves to issue analysis.

## When to use

Fires when the user:

- Pastes a PR URL or `<repo>#<n>` reference and asks for a review, walkthrough, or explainer.
- Hands over multiple PRs and asks to review them together or in conjunction.
- Asks to draft comments in their voice for a specific PR.
- Is working through the daily CDT PR digest and starts picking PRs to review.

Do NOT fire when:

- The user wants a comprehensive multi-agent audit — route to `intech-tools:code-review`.
- The user wants to draft a PR *description* (not review comments) — route to `issei-voice` or `blog-voice`.
- The code isn't in a PR yet (no `gh` lookup target).

## Process

### 1. Intake — fetch the PR(s)

Always clear `GITHUB_TOKEN` before `gh` commands (the env var conflicts with the gh CLI's keychain auth):

- Bash: `unset GITHUB_TOKEN`
- PowerShell: `$env:GITHUB_TOKEN=$null` or `Remove-Item Env:GITHUB_TOKEN`

For Curve work use `gh auth switch --user Issei-curve` before any read; for personal use `--user ikuzuki`.

For each PR, pull title, body, additions/deletions, files, head OID, author, existing reviews, and inline-comment threads. Cache the head OID — you'll need it for posting. Don't paginate the diff yet; the per-file additions/deletions list is enough to decide which files matter.

If multiple PRs are in scope, fetch all in parallel (single `gh` call per PR, batched in one tool message).

### 2. Group or split decision

Output a one-line verdict before any analysis. Group PRs together when they share:

- A Jira ticket (same `CDT-NNN`).
- An explicit cross-PR dependency (e.g. PR body says "needs #252 to land first").
- A shared API contract or envelope shape (the CDT-228 trio is the canonical example: extract → adopt in repo A → adopt in repo B).
- A merge train that has to land in order.

Split into separate reviews when they share none of the above — even if the same author raised them. Don't force unrelated PRs into one writeup; the reviewer's eyes get worse, not better.

If grouping, do one combined writeup with per-PR sections. If splitting, run each PR through the full process independently.

### 3. Plain-English explainer

This is the part the heavy review skill skips. For each PR (or group):

- **What is the PR doing?** One paragraph, no jargon. Imagine explaining to a teammate from a different sub-domain who knows the platform but not this corner of it.
- **Why does it matter?** Where does it sit in the wider architecture? What was broken / missing before?
- **What does it touch?** File-by-file, one line each. Group test files separately so they don't dominate the list.

**Unpack jargon inline, every time.** Don't assume the reader remembers earlier explanations. If a PR touches IDOR, TOCTOU, envelopes, GSI, ULID, `TransactWriteItems`, permission boundaries, prefix lists, or any other term that wouldn't be obvious to someone outside the immediate domain, unpack it inline in the explainer. Better to over-explain than land a comment the user doesn't fully understand. Prefer the analogy that ties the term to something the user already knows (e.g. "envelope = the wrapper every response carries, like an HTTP envelope around a letter").

If the PR references another PR for context (e.g. "depends on #252", "follows on from CDT-228"), fetch that PR's status and short summary too. Pull cross-repo context only when it's explicitly referenced — don't go fishing.

### 4. Analyse for issues

Read the actual diff now. Categorise findings into three buckets:

- **Real bugs.** Security holes, race conditions, broken contracts, silent failures, missing validation. These get raised firmly.
- **Design questions.** Worth asking but not blocking. Question form, frames the trade-off, leaves the decision with the author.
- **Nits.** Style, naming, low-stakes. Get the `nit:` prefix in the comment.

Cross-reference earlier reviews on the same PR — if Sean or Adele has already raised a point, don't re-raise. If the team has actioned a fix, acknowledge or skip. If a prior comment was raised AND the author pushed back, only re-raise if you have genuinely new reasoning — repeating the same argument doesn't add value. Same with same-author patterns: if you've reviewed three of Adele's DynamoDB PRs already, you know the conventions she follows; don't re-litigate things that have already been agreed.

For multi-PR groups, look for issues that span PRs (e.g. "the lockfile in #23 is out of sync because the hub release in #252 hasn't been cut yet"). Cross-PR findings live in the group writeup, not in individual PR sections.

### 5. Draft comments in voice

Use the canonical voice rules at `~/Knowledge Base/knowledge-vault/voice/code-review.md`. Conversational mode is the default — short, direct, lowercase fine, British English, no em dashes (` - ` instead), no apology, no "happy to discuss", no preamble, no summary at the bottom.

For each comment, produce three things:

- **Target:** `path/to/file.py:LINE` where LINE must be inside one of the PR's diff hunks (GitHub rejects line numbers outside changed regions — verify against `gh api repos/.../pulls/N/files | jq '.patch'` before drafting).
- **Body:** the comment text. Conversational shape. `nit:` prefix if low-stakes. Question form if ~80% sure. Concrete fix proposal when the answer's obvious.
- **Rationale:** one line for the user, NOT for posting — why this matters, severity, expected response.

For top-level comments (model-level questions, scope concerns, PR-body asks) use a single review body string rather than an inline anchor.

### 6. Surface for confirm

Show all drafted comments to the user in this conversation. Group them by category (real bugs first, design questions next, nits last). For each: target, body, rationale. Total count at the top.

**Wait for explicit confirmation before posting.** Default is "always confirm" — even for trivial acks. The confirm step is cheap and keeps the user in the loop.

If the user asks to revise specific comments, redraft those only and re-surface. Don't redraft the whole batch unless asked.

### 7. Post via gh CLI

When the user gives the go:

- `event=COMMENT` only. Never `APPROVE` or `REQUEST_CHANGES` unless the user explicitly asks (Issei lets the team self-approve after reading the comments).
- Submit as a single review via `gh api -X POST repos/<owner>/<repo>/pulls/<n>/reviews` with `commit_id` (the head OID cached at step 1), `event`, `body` (top-level), and `comments` (inline array of `{path, line, side: "RIGHT", body}`).
- If GitHub returns 422 "Line could not be resolved", the line isn't in a diff hunk. Re-fetch the patch via `gh api .../files`, pick the nearest line that IS in a hunk (usually a newly-added line in the same logical block), and retry.
- Return the review URL to the user when posted.

For multi-PR groups, post one review per PR but mention the group in the top-level body so reviewers see the cross-PR context.

## Voice shape — the bits that recur

The patterns below mostly come from `knowledge-vault/voice/code-review.md`. A few (em-dash ban, British English) are inherited from the broader `issei-voice` skill rather than the PR-review voice doc specifically — flagged inline where that's the case so attribution stays honest.

- **Short corrective:** when the fix is obvious, just say it. "Think this should be `category_context=category_context`" — no preamble.
- **Question form when ~80% sure:** "we probably dont need this check?" softens the verdict without weakening the argument. Use when the author may have context you don't.
- **Concrete reasoning + path:** for architectural calls, state the position, the reasoning, AND what it means for the PR. "Ok actually after pondering for a bit, I think we should X. So what this means for this PR — we can drop Y." Never leave architecture opinions hanging without a PR-shaped follow-up.
- **"X scares me":** plain language for "this looks risky". Makes the concern land without dressing it up.
- **`nit:` prefix:** low-stakes style notes. Convention is shared across the team; if you're not prefixing, the comment is meant to matter.
- **"Same here" / "Same comment here":** for batch-same-comment patterns (e.g. the same diff region across multiple files). Write the full comment once on the most representative line, drop "Same here" on the rest.
- **Acknowledge when pushed back on:** "Ah true yeah good point" — three words, no caveats. If you're sticking with your position, re-state briefly rather than apologising for repeating yourself.

Anti-patterns to avoid:

- Em dashes (`—`). Use hyphens with spaces (` - `). *From `issei-voice`, not `voice/code-review.md` — but applies across all Issei comms including PR comments.*
- "Just a thought", "feel free to ignore", "happy to discuss" — wishy-washy when the comment was a clear request.
- "I think" every time. It's a tic. Once or twice per review max.
- Previewing the comment ("Wanted to flag a concern here:"). Just make the point.
- Summary at the bottom of a review ("Overall this looks good!"). Approvals say that already.

## Multi-PR handling — the bit `voice/code-review.md` doesn't cover

The voice doc covers single-PR comments. Multi-PR handling is novel territory the skill needs to define:

- **Group writeup structure:** one combined explainer covering the *theme* across PRs (e.g. "this trio collapses accidental drift between control-plane and data-plane"), then per-PR sections with each PR's own findings, then a cross-PR findings section if relevant.
- **Comment scope:** comments still post per-PR (GitHub's API doesn't support cross-PR review threads). But the top-level body of each review can reference the others ("this is one of the CDT-228 trio; see also #252 and #11").
- **Merge order callout:** if PRs depend on each other, surface the implied merge order to the user in the explainer ("#252 first, then #23, then #11 — the hub release has to be cut before the consumers can pin to it").
- **Token budget:** for very large groups (5+ PRs), summarise non-substantive PRs (mechanical migrations, tiny IAM additions) in one paragraph each rather than running the full process. Spend the explainer budget on the architecturally meaty ones.

## Posting safely — gotchas to remember

- **`unset GITHUB_TOKEN` first.** The env var interferes with gh CLI auth. Every `gh` command in this skill gets it as a prefix.
- **`gh auth switch --user Issei-curve` before Curve work**, `--user ikuzuki` for personal. Check current account via `gh auth status` if unsure.
- **Line must be in a diff hunk.** `path:LINE` with LINE inside an unchanged region returns 422. Verify by reading the `.patch` field on `gh api .../files`.
- **`side: "RIGHT"` for additions, `"LEFT"` for deletions.** Default to RIGHT for almost everything — you're commenting on the new code, not the removed code.
- **`event=COMMENT` by default.** APPROVE/REQUEST_CHANGES need explicit user consent.
- **No auto-retry on 422.** Re-surface the failing comment to the user with the resolved hunk lines and ask which line to land it on. Silent retries can land comments on the wrong line.

## Self-check before delivering

- [ ] Is the explainer in plain English with jargon unpacked?
- [ ] Have I cross-referenced earlier reviews to avoid duplicating points already raised?
- [ ] Are comments categorised (real bug / design Q / nit) with `nit:` prefixes where they apply?
- [ ] Conversational-mode voice — short, no em dashes, no "happy to discuss", British spellings?
- [ ] For each inline comment, is the target line inside a diff hunk?
- [ ] For multi-PR groups, is there a single cross-PR explainer plus per-PR sections?
- [ ] On post, `event=COMMENT` unless user explicitly asked otherwise?

## Scope

This skill is the lightweight, human-in-the-loop PR walkthrough for cases where the reviewer wants context first, comments second, and explicit control over what gets posted. It does NOT:

- Spawn specialist sub-agents (use `intech-tools:code-review` for that scale of review).
- Apply confidence-scored citation gates against coding-standards anchors.
- Run SemVer / breaking-change / type-design audits automatically.
- Post comments without confirmation.
- Issue APPROVE or REQUEST_CHANGES verdicts without explicit user instruction.

If the user wants any of the above, route to `intech-tools:code-review` instead.

## References

- `~/Knowledge Base/knowledge-vault/voice/code-review.md` — canonical voice rules for PR comments (conversational mode, structured mode, batch-same-comment, release-please-adjacent calls). Read on every invocation.
- `~/Knowledge Base/knowledge-vault/voice/explaining-code.md` — sibling note for the explainer phase (how to write "behaviour" sections, self-explainer prompts vs team-facing explainers).
- `intech-tools:code-review` — the heavy alternative. Worth knowing what it does so this skill can stay clearly out of its lane.
- `issei-voice` — the broader async-comms voice skill. Composes with this one — turbo-pr-review handles the workflow, `issei-voice` handles the rendering of any non-PR-comment text (e.g. Slack message about the review, Jira ticket summary).
