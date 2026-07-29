---
name: share-prs
description: Turn a batch of Issei's open PRs into a single share-ready message for a reviewer - one bullet per PR with the PR link, the Jira ticket link, a plain-English what-it-does, a why-look-here steer, its review state, and a scope note. Use when the user says "share these PRs", "write up these PRs for Adele/Sean/Nikhil", "message for review", "hand these over", "draft the PR handover", "ask for a re-review on these", "/share-prs", or pastes a set of their own PR URLs and asks for a message to send. Renders in Issei's voice (composes with `issei-voice`) and Teams-safe markdown. Distinct from `understand-prs` (inbound - PRs someone else sent to Issei), `my-open-prs` (private status table, not for sending), `cdt-daily-pr-digest` and `pr-review-loop` (team-wide automated digests). Does not review code and never posts to GitHub.
---

# Share PRs

One job: take N of Issei's PRs and produce the message he pastes into Teams to
hand them to a reviewer. The failure mode this skill exists to kill is the
three-iteration loop - a first draft that's too uniform (every PR written at the
same length), too coy about priority, and missing the state context the reviewer
needs to know whether they're looking at something fresh or something they've
already seen.

Read [`references/templates.md`](references/templates.md) on every invocation.
That file holds the bullet anatomy, the two registers, and the worked examples.

## When to use

Fires when the user has a batch of **their own** PRs and wants them handed over -
for a first review, a re-review, or an approve-and-merge nudge. Also fires for a
single PR when they explicitly want a share message rather than just a link.

Do NOT fire for: PRs someone sent *to* Issei (`understand-prs`), a private
status view of his own queue (`my-open-prs`), the team-wide daily digest
(`cdt-daily-pr-digest`), or a PR *description* (`issei-voice`).

## Process

### 1. Resolve the batch

Accept PR URLs, `<repo>#<n>` refs, "the CDT-544 chain", "everything I raised
today", or nothing at all (then take every open PR authored by Issei - reuse
`my-open-prs`' discovery call).

```bash
unset GITHUB_TOKEN && gh auth switch --user Issei-curve
gh search prs --owner curveanalytics --author @me --state open \
  --limit 60 --json number,title,repository,isDraft,url,updatedAt
```

Then per PR, in one batched tool message:

```bash
gh pr view <n> --repo curveanalytics/<repo> \
  --json number,title,body,headRefName,isDraft,url,additions,deletions,files,reviewDecision,reviews,comments,mergeable,mergeStateStatus
```

**Ask before including a draft.** A draft in a share message is usually a
mistake; if the user wants it in (for early eyes on direction), say so in the
bullet.

### 2. Resolve the ticket per PR

Parse `CDT-NNN` / `INTECH-NNN` from `headRefName` first (free), then the PR body
or title as fallback.

**The ticket must be a link, not bare text.** `CDT-544` written as plain text
makes the reader go and search for it; it is often the identifier they most want
to open. Render it as a markdown link to
`https://curve-analytics.atlassian.net/browse/CDT-NNN`, the same way PR
references are linked.

Fetch the ticket only when the PR's own title and body don't make the *why*
legible - the ticket summary is often the missing sentence. Use the Atlassian
MCP (`getJiraIssue`). If a PR has no ticket, leave the ticket link out of that
bullet rather than inventing one, and flag it to the user (an untracked PR is
worth knowing about).

Where several PRs share one ticket, put the ticket link once in the opening line
("all CDT-544") instead of repeating it on every bullet.

### 3. Check the premise before you repeat it

Issei's framing of the batch is written from memory, often hours old, and the
message goes out over his name - so a stale claim in it is his mistake, not the
reader's. Before repeating any dependency he asserts, verify it:

- "hub needs to merge and release first" → is that PR still open? `gh release list`
  on the repo, and does the consumer's lock still point below the released
  version?
- "waiting on X to land" → is X actually unmerged?
- "comments have been addressed" → is there a commit *after* the latest review?

If the premise has moved, say so in the Claude-to-Issei note and write the
message to what is true now. Do not quietly send a message asserting a blocker
that cleared two hours ago.

### 4. Establish review state per PR

This is the context the reviewer needs and the thing first drafts always miss.
For each PR work out which of these it is, from `reviews` + `comments` +
whether commits sit past the latest review:

- **Fresh** - no reviews yet. Nothing to say beyond what it does.
- **Back for a re-review** - reviewed, comments addressed, commits pushed since.
  Say what changed: "the nit is fixed and the two judgment calls are answered
  inline".
- **Reviewed and approved, needs the click** - `reviewDecision == APPROVED`, or a
  human left "looks good" without formally approving. Say so plainly: "this just
  needs the approve click".
- **Automated pass only** - the newest review carries the
  `<!-- pr-review-loop: reviewed-at=... -->` marker and no human has looked.
  Never present a bot review as a review. Either say nothing about state or say
  "not had human eyes yet".
- **Blocked** - showing conflicts, or waiting on another PR in the batch to land
  and release first. Say which, and why.

**When the ask itself isn't supported by the PRs, don't write it anyway.** Issei
may ask for a re-review on a batch where two are already approved and two have had
no commit since the reviewer's last round - so "back for a re-review with the
comments addressed" would be a false claim to the person who left those comments,
and it damages his credibility with them. Write those PRs as what they are
("coming back to you on this one", "still owe you an answer on the docstring
question") and put the discrepancy in the Claude-to-Issei note so he can decide.
Never assert work was done that wasn't.

### 5. Order the batch

Order is the message's most useful signal. Pick one axis and apply it:

- **Merge order** when the PRs form a chain (contract PR first, then consumers).
  Say it: "goes in after #86", "needs that release in first".
- **Priority / effort** when they're independent - chunky and architecturally
  meaty first, mechanical last, so a reviewer with 20 minutes spends it well.

Never order by repo name or PR number. If the batch has both a chain and some
independents, lead with the chain in merge order and trail the independents.

### 6. Write the bullets

Per `references/templates.md`. Two rules matter most, and they pull against each
other on purpose.

**Weight each bullet to the PR, not to the batch.** A contract change everything
hangs off earns the full treatment plus a scope note. A pure deletion earns one
clause. A message where every bullet is the same length is the tell that the
drafting was mechanical, and it's why drafts get sent back.

**But hold the ceiling: 60 words per bullet, and never past 70.** Terse bullets
sit at 25 or under. "Weight it to the PR" is licence to be *longer*, not licence
to be unbounded - past about 60 words the bullet stops being a handover line and
becomes the per-PR analysis this message exists to replace, and a 130-word bullet
is not paste-ready however good the prose is. If a PR genuinely needs more, that
detail belongs in the PR body or the Claude-to-Issei note. The reviewer is
deciding what to open first, not reading the review.

### 7. Frame the message

An opening line (who, what this is, the ordering axis, and the honest headline -
"a couple are chunky", "all small"), the bullets, and a one-line close. No
headings, no bold sprinkled through prose, no closing recap of what was already
said in the bullets.

Compose with `issei-voice` for the wrapper prose. If drafting to a specific
person, read `knowledge-vault/people/<name>.md` first - it changes how much
context to front-load.

### 8. Surface, don't send

Print the message as a fenced block for clean copy-paste, then a short
Claude-to-Issei note (outside the block) for anything he should know but that
shouldn't go in the message: a PR with no ticket, a draft included, a conflict
he may not have noticed, a bullet where the *why* was guessed and needs a check.

Never post to GitHub, Teams, or anywhere else. Output is text for Issei to send.

## Self-check before delivering

- [ ] Is the ordering axis explicit in the opening line?
- [ ] Does every bullet carry a PR link and (where one exists) a ticket link,
      both as real links rather than bare text?
- [ ] Is each bullet's length matched to the PR's weight - short things short?
- [ ] Is every bullet under 60 words, with at least one at 25 or under?
- [ ] Did I verify any dependency or "comments addressed" claim rather than
      repeating Issei's framing?
- [ ] Does each non-fresh PR say what state it's in and what changed?
- [ ] Is at least one bullet carrying a steer ("start here", "this is the one
      with teeth", "small but load-bearing")?
- [ ] Plain English, jargon unpacked, no internal class or module names?
- [ ] British English, no em dashes, no "just", no "feel free to"?
- [ ] Teams-safe: bullets, bold and links only - no tables, no headings, no
      code fences inside the message?
- [ ] Is anything asserted about a PR that you didn't read off the PR or ticket?

## Anti-patterns

- **Uniform bullets.** The single biggest cause of a re-draft.
- **A bullet that outgrows the message.** Past ~60 words it belongs elsewhere.
- **A bare ticket key.** `CDT-544` as plain text makes the reader go searching.
- **Repeating Issei's premise unchecked.** The message goes out over his name.
- **Conventional-commit titles.** `feat(dispatch): carry the pre-enriched
  output_id on source config refs` is a commit message, not a description.
  Rewrite as what it does for the system.
- **Internal identifiers in the prose.** No `DispatchAssembler`, no
  `output_id` unless the reviewer's job is that field specifically - and then
  unpack it.
- **Silent priority.** If the reviewer has to infer where to start, the message
  failed.
- **Presenting the automated review as a review.** "Already reviewed" means a
  human reviewed it.
- **Inventing the why.** If the PR body and ticket don't say why it matters,
  ask - don't fabricate a rationale that a reviewer will quote back.
- **A scope note that's just a file count.** "(6 files)" tells nobody anything.
  "(One source module plus wiring through five existing ones, Terraform for the
  leases table, two new test modules, all green)" does.
- **Closing recaps.** "Let me know if you have any questions!" adds nothing.
- **Tables or headings.** Teams renders them inconsistently.

## References

- [`references/templates.md`](references/templates.md) - bullet anatomy, the two
  registers, worked examples. Read every time.
- `~/Knowledge Base/knowledge-vault/voice/team-chat.md` - async comms voice.
- `issei-voice` - renders the wrapper prose.
- `understand-prs` - the inbound counterpart; its per-PR brief and this skill's
  bullet are deliberately the same shape seen from opposite ends.
- `my-open-prs` - shares the discovery call; use it when the ask is a status
  view rather than a message.
