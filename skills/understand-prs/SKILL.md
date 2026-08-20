---
name: understand-prs
description: Work through PRs someone has sent Issei to review - per PR a one-sentence what-it-is, a short placement block (where it lands in the platform, what component it adds, what share of the epic it closes, what it depends on and unblocks), a one-line review-state line, and then the part bots can't do: the architectural calls only he can make - does this PR need to exist, is the feature built the right way, should it be split, does it belong in the shared hub, is it at the right layer - each with the cross-check already done and a drafted comment ready to post. Use when the user pastes one or more PR URLs or `<repo>#<n>` refs, or a whole handover message ("here's today's PRs", "comments have been addressed, please take a look"), and says review this / take a look / have a crack / walk me through / explain this PR / in laymen's terms / what does this do / thoughts on this / brief me on these / draft comments for this / where do you need me on this / does this even need to exist / should this be split / does this belong in hub. Also fires on re-review phrases ("they pushed back", "they replied, take another look", "draft replies to these comments", "post with approval") and when picking PRs off `cdt-daily-pr-digest` or `my-open-prs`. Supersedes the former `turbo-pr-review` skill. Drafts inline comments in Issei's voice and posts only on explicit confirmation; never approves or merges without being told. Distinct from `pr-review-loop` / `pr-review-loop-lite` (unattended, automated, posts a bot verdict), `intech-tools:code-review` (heavy multi-agent audit), and `share-prs` (outbound - Issei's own PRs going to a reviewer).
---

# Understand PRs

Issei reviews across the whole of CDT - backend, infra, shared libraries,
frontend - usually without having written the surrounding code, and usually after
`pr-review-loop-lite` has already left an automated pass. Four things follow, and
the skill exists for all four.

**He arrives with no context.** The bot review is on the PR; he hasn't read it. A
session opening with "the automated pass said looks good, what do you want to
add?" starts from context he does not have. Reconstruct it.

**The mechanical review is largely solved.** Bots read diffs well and get better
every month. Null checks, missing tests, broad excepts, weak types - those are
covered, and re-doing them by hand is where this skill wastes its keep.

**What isn't solved is everything upstream of the diff.** Does this PR need to
exist. Is the feature built the right way, or a way that merely passes. Should it
be two PRs. Should this live in `intech-hub` rather than here. Does this layer
even own the concept. Nothing in the diff answers those, no bot asks them, and
they are the only questions where his judgement is irreplaceable. **Surfacing
them is this skill's primary output.** A brief with no shape findings and no
account of the lenses that came back clean has failed, however good the explainer
was.

**The way to make that possible is placement, not teaching.** He can only answer
"should this exist" if he knows what it is, what it adds, what already existed,
and what it is part of. So the brief's job is to put the PR on the map as fast as
possible and then get out of the way. Every word spent teaching him a mechanism
is a word not spent placing the change. The budgets below are real.

Read [`references/judgment-lenses.md`](references/judgment-lenses.md) on every
invocation - it is how step 7 is executed, and its Tier A is the point of this
skill. Read `~/Knowledge Base/knowledge-vault/voice/code-review.md` before
drafting any comment. Do not read `voice/explaining-code.md` unless he asks for a
teaching-shaped writeup; the brief format below supersedes it here.

## When to use

Fires when PRs arrive *for Issei to review*: a pasted URL, a set of refs, or a
handover message from Adele, Sean, Nikhil, Luke or an offshore contributor. Also
for re-review passes, and for author-side replies on his own PRs.

Do NOT fire for: unattended batch review (`pr-review-loop-lite`), a deep
multi-agent audit (`intech-tools:code-review`), drafting a PR description or Jira
comment (`issei-voice`), handing his *own* PRs to someone else (`share-prs`), or
code not yet in a PR.

## Process

### 1. Intake

`gh` needs `GITHUB_TOKEN` cleared - it fights the CLI's keychain auth - and the
right account selected:

```bash
unset GITHUB_TOKEN
gh auth switch --user Issei-curve
```

Run that as its own short command, once. Do not staple `unset GITHUB_TOKEN` onto
later commands: the `secrets-block` hook reads a long scratchpad path or a
40-char SHA sitting near the word TOKEN as a leaked credential and refuses the
call. Auth persists, so once is enough. Use `--user ikuzuki` for personal repos.

Inbound messages vary wildly - a prioritised list, bare URLs with `- BFF` /
`- UI` labels, a Teams paste with mangled links. Parse per PR: the ref, and
anything the sender asserted (priority order, "comments addressed", merge or
release dependencies). **Carry the sender's stated order through** unless you
find it wrong, and say so if you do.

### 2. Gather everything in one batch

One message, one call each, in parallel. Do not serialise this - the placement
work in step 4 needs the ticket and the epic, and fetching them after the diff
doubles the round trips.

```bash
gh pr view <n> --repo curveanalytics/<repo> \
  --json number,title,body,headRefName,author,url,additions,deletions,files,reviewDecision,reviews,comments,mergeable,mergeStateStatus
gh api repos/curveanalytics/<repo>/pulls/<n>/comments
gh api repos/curveanalytics/<repo>/pulls/<n>/reviews
gh pr diff <n> --repo curveanalytics/<repo>
```

`gh pr diff` **not** `--patch`: the latter repeats files per-commit and reports
wrong line numbers. The `comments` endpoint carries the inline threads including
author replies; `reviews` carries review bodies and verdicts.

Plus the Jira side: the linked ticket **with its comments**, and its parent epic
with siblings. One JQL call gets the epic's children -
`searchJiraIssuesUsingJql` with `parent = CDT-880`, or `key in (CDT-1, CDT-2)`
for a known set. Never one `getJiraIssue` per sibling; it returns the whole
description regardless of the fields you ask for and burns the context you need
for the diff.

Cache each head OID - posting needs it. Pull file context on demand with
`gh api repos/curveanalytics/<repo>/contents/<path>?ref=<head-oid>`. For batches
of five or more, gather metadata and reviews for all of them first, then stage
the diffs as you work through.

### 3. Read the review state

**Classify by marker first, author second.** `pr-review-loop` posts its reviews
**under Issei's own GitHub account**, so login alone tells you nothing:

- Body carries `<!-- pr-review-loop: reviewed-at=<oid> -->` → **automated**,
  whoever it appears to be from. Its verdict (`Looks good` / `Minor comments` /
  `Needs Changes` / `Needs Judgment`) is advisory. `Needs Judgment` is an
  explicit handoff - those lines go into step 7.
- No marker, author is a teammate → **human**. Never re-raise a point a human
  already made.
- No marker, and the reviewer **is the PR's own author** → a self-review.
  Legitimate, but not independent scrutiny, so don't let it stand in for a review
  when judging how much this PR has been looked at. Say so plainly: "the two
  substantive passes are hers on her own PR". If you can't tell a genuine
  self-review from automation on that person's token, say that rather than
  picking one.
- No marker, author is Issei → **his own earlier review**, so this is a
  re-review. "His last review" means the most recent *unmarkered* review by his
  account; picking the most recent review by login grabs a bot pass and computes
  the wrong delta.

**An approval doesn't close later threads.** He may have approved and another
reviewer then left open items on the same head. His approval stands; the open
items are the author's to action, not his to re-raise. Say whose court each is
in.

Per thread record who raised it, the author's reply, and whether it is settled
(concrete reason given - drop it), fixed (verify in the diff), or open. If the
marker's OID is behind the current head, the bot reviewed an older commit - that
delta is unreviewed and it goes in the status line.

This whole step compresses to **one line** in the output. A large amount of
reading producing a small amount of text is the correct shape here.

### 4. Place it - the puzzle fit

The step that makes the shape questions answerable. Four things, each cheap:

- **Layer.** Which repo, plane and layer the change lands in, named in system
  terms - silver load, serving composer, dispatch contract, hub schema, IAM root
  - not module paths.
- **Components.** What this PR adds or completes as a named piece of the system,
  and what it builds on that already existed. "Adds the rollup reader; the specs
  and the loader landed in #87."
- **Epic position.** The parent epic, and which siblings are already merged.
  "Fourth of six on CDT-880: loader and schema in, this is the reader, the
  backfill and the alarm still open."
- **Edges.** What it depends on (an unreleased hub version, an unmerged PR, a
  hand-seeded secret) and what it unblocks.

Where the PR is genuinely standalone - a dependency bump, a one-off fix - say so
in a line and move on. Inventing an epic narrative for a lockfile pin is padding.

**Most Tier A findings come out of this step, not out of the diff.** A component
with no caller, a layer that doesn't own the concept, an epic whose remaining
tickets this PR quietly makes redundant, two unrelated components in one PR.
Notice them here, carry them into step 7 rather than resolving them here.

### 5. Group or split

One line, before any analysis. Group on a shared ticket, an explicit cross-PR
dependency, an API contract, or a merge train. Split otherwise, even from the
same author. Surface the implied merge order when there is one.

### 6. The brief - one per PR

Exactly this shape, these headings, this order:

```
## <repo>#<n> - <title>
<status line: one line - bot verdict, thread state and whose court, build, and
whether the head has moved past the reviewed OID>

**One sentence.** <what changes for the system or the user. No class, module or
field names. If it needs two sentences the PR is doing two things - that is a
Tier A finding, say it here and again in Where you're needed.>

**Where it sits**
- **<claim>.** <detail>   (3-4 bullets covering layer, components, epic position, edges)

**Worth knowing**
- <0-3 bullets, one line each>

**Where you're needed**
- <step 7; the only section allowed to run long>
```

**Bold the claim, not a label.** `**Layer.**` is a category heading wearing a
bullet's clothes. `**Lands in the silver load, the append-only layer under the
gold tables.**` is a claim. Skimming only the bold text should give him the
placement; the plain text after it is for when he wants the why. Cover the four
placement things without labelling them.

**Budgets, and they bind - on the words per finding, never on the number of
findings.**

| Section | Budget |
|---|---|
| Status line | One line. Bullets only when the history is genuinely tangled - two bot passes, a dismissed approval, a red build. Never pad a simple history. |
| One sentence | One sentence. |
| Where it sits | 3-4 bullets, one line each (~25 words). |
| Worth knowing | Up to 3 one-liners. **One** on frontend. **Zero is a valid answer** - omit the heading. |
| Where you're needed | Unbounded in total; ~80 words per item, across separate lines. |

Everything above **Where you're needed** fits one screen. Bullets, not prose;
prose is what makes these unreadable. When a point genuinely needs more than 25
words, split it into two bullets rather than running one to fifty.

**Never hit a budget by dropping a finding.** The tempting move is to keep the
headline and drop the second and third things you found - and those are exactly
what he cannot get anywhere else. A live edge case nobody has hit, a test green
only through mock leakage, a scoping insight that changes how a follow-up gets
written: those are the output. Shorten the prose, split long bullets, cut
restatement. A short brief that dropped a real finding has failed worse than a
long one that kept it.

**Worth knowing has been deliberately cut back.** It is now only for a
technology or protocol feature he may genuinely not have met, or a non-obvious
constraint being worked around - unpacked inline every time, even on repeats:
IDOR, TOCTOU, GSI, ULID, `TransactWriteItems`, permission boundary, prefix list,
row policy, projection. Prefer an analogy anchored in something he knows. Never
"adds tests", "follows existing patterns", "uses type hints", and never a
mechanism walkthrough he could infer from the placement bullets. If nothing
qualifies, drop the section - that is the expected outcome on a routine PR, not a
gap in your work.

**Two independent dials for frontend, do not collapse them.** On
`intech-experience-ui` and similar, **Worth knowing** goes to a single line or
none - he is a high-level reviewer there by choice. **Where you're needed** stays
at *full strength*: real defects live there (a validation effect that can never
fire, tests green only through mock leakage, a ticket premise the API can't
support), and the shape questions apply just as hard. Shallow teaching, full
scrutiny.

Backend, infra, shared libraries, data and schema work: placement earns its
space. Terraform and IAM always do - blast radius is the placement.

Name the bot as a bot. "The automated pass said looks good" - never present it as
review cover. No preamble in front of the status line; a correction to the
sender's premise goes *in* the status line or as a single line under it.

### 7. Surface the judgment calls

Run the lenses in [`references/judgment-lenses.md`](references/judgment-lenses.md).
**Tier A - shape - runs first**, because a PR that shouldn't exist or belongs in
hub makes every Tier B finding moot. Its core eight run on every PR and cost no
extra fetches; three more are gated on what the PR touches (cost and scale,
tenancy boundary, rollout and rollback) and you say which of those the PR
triggered. Tier B is the correctness and completeness set.

**Do the cross-check yourself before surfacing anything.** The value is arriving
with the work done, not handing him a list of things to check. So: read the model
doc, fetch the ADR, grep the other repos for consumers, read the ticket comments
where the deferrals live. When the intech-tools Atlassian MCP times out (it does,
at 300s, fairly often) fall back to the other configured server - the cross-check
is the point of this step, not an optional extra.

Each item takes this shape - separate lines, question last:

```
- <what you checked it against> - <the gap, in a sentence or two>.
  <In scope for this PR, or a follow-up.>
  <The question he is being asked.>
  Draft: "<the comment, in voice, ready to post>"
```

**About 80 words per item, never one paragraph.** A 200-word block has to be read
twice to find the question, which is the cost this section exists to save. The
reasoning that earned the finding belongs in the draft comment where the author
will read it, not in the summary he is skimming to decide what to do.

**End on the question, not your conclusion.** Landing on "my read: cut the
ticket" quietly takes the decision off him, which is the one thing this section
must not do. Have a view, put it in the body if it helps, but the closing line is
his call: "in scope or follow-up ticket?", "is that how the product behaves?",
"hold the merge for this?", "does this belong in hub instead?"

Where the honest answer is "the scope was these two cases, so this is a follow-up
not a blocker", draft it that way - name the gap, say you're not asking now,
suggest the ticket, leave timing with the author. That framing is what stops it
reading as scope creep.

**Order items by altitude, not severity.** Tier A first even when a Tier B bug is
the more urgent fix, because "should this be split" changes what happens to the
bug. Within Tier B, blockers before follow-ups.

**If nothing survives the lenses, say so and name the lenses you ran.** "Ran
necessity and ownership, completeness against the model doc, and blast radius
across the three consumers - nothing needing your input, the bot's read holds" is
a good answer. Silence is not, and inventing a judgment call to fill the section
is worse than an empty one.

### 8. Draft comments in voice

Conversational by default - short, direct, lowercase fine, British English, no em
dashes (` - ` instead), no apology, no "happy to discuss", no preamble, no
summary at the bottom.

Per comment: **target** (`path/file.py:LINE`, a line inside a diff hunk, verified
by matching the code the finding refers to rather than trusting a remembered
number - Tier A points, model-level and scope points go in the top-level body
instead), **body** (`nit:` prefix if low-stakes; question form when ~80% sure;
concrete fix when obvious), and **rationale** (one line for Issei, not posted).

Categorise: shape and design questions, then real bugs, then nits. Don't re-raise
what a human already raised or re-litigate settled conventions.

### 9. Surface for confirm

Every draft in chat, grouped by category, count at the top. **Wait for explicit
confirmation before posting**, always. On a revise request, redraft only those.

### 10. Post

- `event=COMMENT` only. `APPROVE` / `REQUEST_CHANGES` need an explicit
  instruction; merging never happens here.
- One review per PR: `gh api -X POST repos/curveanalytics/<repo>/pulls/<n>/reviews`
  with `commit_id`, `event=COMMENT`, `body`, and `comments` as
  `{path, line, side: "RIGHT", body}`. Build the payload as a file, pass
  `--input`, confirm it reads back `state: COMMENTED` not `PENDING`.
- **The reviews API is atomic** - one unresolvable anchor 422s the whole review
  and loses every other comment. Pre-validate all anchors offline.
- On 422 "Line could not be resolved", don't silently retry: re-surface with the
  resolved hunk lines and ask which line to land on.
- Never probe-post a throwaway review to find a line. Return the review URL.

## Re-review mode

When he has already reviewed and the author has pushed or replied - or it's his
own PR with reviewer comments waiting - review only the **delta** and reply *into*
existing threads.

**Delta detect.** Take the most recent *unmarkered* review by his account (step
3); its `commit_id` is the head he last saw. Diff that against current head and
review only the new lines plus enough context to judge them. Pull threaded
replies from `.../pulls/<n>/comments` and find threads he started that now carry
a newer reply.

**Skip placement on a re-review** unless the delta changed the PR's shape - a new
component, a new dependency, scope that grew. He already has the map; re-drawing
it is the sprawl this format exists to avoid. Lead with the threads.

**When the delta is empty or trivial** - a pure `main` merge, a lockfile bump,
formatting - say so in one line and make the *open threads* the lead: "nothing to
review in the delta, it's a main merge. What's outstanding is your completeness
comment from the 24th, still unanswered." An empty delta is a common and useful
outcome, not a dead end.

**Reviewer mode (someone else's PR).** Fixed → brief acknowledgement ("ah true
yeah good point") or resolve silently. Pushed back → re-engage only with genuinely
new reasoning, engaging their argument explicitly. Fix claimed but not in the
delta → "has this landed? not seeing it in the latest push". New issues → fresh
comments per step 8. Re-run step 7: a shape finding can appear in the delta,
especially when a fix was applied at the wrong depth.

**Author mode (his own PR).** One reply per thread: confirm the fix ("done,
pushed in `<short-sha>`"), push back with reasoning where he disagrees, or ask a
clarifying question. Flag which threads need a *code change* versus just a reply.

**Reply into a thread** with
`gh api -X POST repos/curveanalytics/<repo>/pulls/<n>/comments/<comment_id>/replies -f body='...'`
- a different endpoint from the reviews API. Approval stays separate: only on an
explicit "post with approval" does `... -f event=APPROVE` run. Never bundle it
with comments. Never merge.

## Voice shape - the bits that recur

- **Short corrective** when the fix is obvious. "Think this should be
  `category_context=category_context`" - no preamble.
- **Question form when ~80% sure.** "we probably dont need this check?"
- **Position, reasoning, and what it means for the PR.** Never leave an
  architectural opinion hanging without a PR-shaped path.
- **"X scares me"** for "this looks risky", in plain language.
- **`nit:`** for low-stakes. Unprefixed means it's meant to matter.
- **"Same here"** for a repeated pattern - full comment once, "same here" after.
- **"Ah true yeah good point"** when pushed back on successfully.
- **The deferral frame** for step 7: what you checked, what's missing, "not asking
  for this now given the PR's scope was X", suggest a ticket, "now or later, your
  call".

Avoid: em dashes; "just a thought" / "feel free to ignore" / "happy to discuss";
"I think" more than once or twice; previewing a comment before making it; a
summary at the bottom.

## Multi-PR handling

One short theme paragraph, then a brief per PR, then cross-PR findings - and this
is where the shape lenses pay best, because splitting and ownership problems are
visible across a batch in a way they aren't in one diff. A contract adopted
inconsistently across two PRs, the same helper written twice in two repos, a
lockfile pinned to an unreleased hub version: all cross-PR.

Comments post per-PR - GitHub has no cross-PR threads - but each top-level body
can reference the others. For 5+ batches, compress the mechanical ones to two
lines each and spend the budget on the meaty ones; say which you compressed.

## Environment notes

- **Two Atlassian MCP servers are configured.** The `intech-tools` one times out
  at 300s fairly often; fall back to the other rather than abandoning the
  cross-check. Its `cloudId` must be discovered via
  `getAccessibleAtlassianResources`, not passed as the site hostname.
- `getJiraIssue` returns the whole description even when you ask for two fields.
  For several tickets, `searchJiraIssuesUsingJql` with a key-set or `parent =`
  filter is one call and far terser.
- Keep the `unset GITHUB_TOKEN` line short and separate (step 1) so the
  `secrets-block` hook doesn't reject it.

## Self-check before delivering

- [ ] **Tier A core run - or the clean ones named?** Necessity, shape, splitting,
      ownership, depth, done-ness, conceptual integrity and reversibility, not
      just diff-level gaps?
- [ ] **Gated lenses:** did I check whether cost, tenancy or rollout triggered,
      and say which did?
- [ ] Does the brief place the PR - layer, component, epic position, edges - in
      3-4 bullets?
- [ ] Does skimming only the bold text give him the placement?
- [ ] Is the review state one line, not a section?
- [ ] Is **Worth knowing** three bullets or fewer, and dropped entirely where
      nothing qualified?
- [ ] Everything above **Where you're needed** on one screen?
- [ ] One sentence, plain English, no class names?
- [ ] Judgment items ordered by altitude, each ~80 words, each ending on a
      question rather than my verdict?
- [ ] Cross-checks done by me, not handed to him as homework?
- [ ] Reviews classified by **marker first**, not author login?
- [ ] Frontend: teaching thinned, scrutiny full strength?
- [ ] Every inline anchor verified against a hunk by matching code?
- [ ] Nothing posted without explicit confirmation; `event=COMMENT`; no merge?

## Anti-patterns

- **Re-doing the bot's work.** Restating diff-level findings a bot already
  covers, instead of asking whether the PR should exist in this shape at all.
- **Skipping Tier A because the PR is small.** A 40-line PR in the wrong repo is
  still in the wrong repo.
- **Skipping the judgment shortlist because the bot said looks good.** That is
  the case this skill exists for.
- **Teaching instead of placing.** A mechanism walkthrough he didn't ask for,
  spending the budget placement needed.
- **Padding Worth knowing to fill the heading.** Zero bullets is a valid answer.
- **Expanding the review state back into a section** on a PR with a simple
  history.
- **Sprawl.** A brief he has to *read* rather than skim has failed, no matter how
  accurate.
- **Hitting the budget by dropping findings.** Shorten the prose, keep the
  finding.
- **A preamble in front of the status line.**
- **A judgment item written as one paragraph with the question buried.**
- **Listing things for him to check instead of checking them.** "You might want
  to verify this against the entity model" is the failure mode.
- **Reading frontend as "review it shallowly".** Teach less, scrutinise the same.
- **Closing a judgment item on your own verdict.**
- **Turning every judgment item into a blocker.** Most are follow-up tickets.
- **Re-raising a settled point.** A concrete rebuttal - especially "that API
  doesn't exist in the pinned version" - wins.
- **Re-placing the PR on a re-review** when the delta didn't change its shape.
- **Reading the Jira body but not its comments.**
- **Classifying reviews by author login** when the bot posts as Issei.
- **Trusting remembered line numbers.**
- **Auto-approving, bundling APPROVE with comments, or merging.**

## Scope

The human-in-the-loop review companion: reconstruct context, place the change,
surface where his judgement is needed - architecture first - draft in voice, post
on confirmation. No specialist sub-agent panels, no citation gates, no SemVer or
breaking-change audits (CDT is pre-1.0 - no MAJOR-bump recommendations), nothing
posted unprompted, no approving or merging. Specialist fan-out audit →
`intech-tools:code-review`; unattended batch review → `pr-review-loop-lite`.

## References

- [`references/judgment-lenses.md`](references/judgment-lenses.md) - Tier A shape
  lenses and Tier B correctness lenses, each with its cross-check and comment
  frame. Read every invocation.
- `~/Knowledge Base/knowledge-vault/voice/code-review.md` - canonical PR comment
  voice. Read before drafting.
- `exec-summary` - the extraction discipline the brief format borrows: bold the
  claim, one bullet one point, cut rather than compress.
- `share-prs` - the outbound counterpart.
- `pr-review-loop-lite` - what left the automated pass this skill ingests; its
  marker and verdict vocabulary are shared.
- `intech-tools:coding-standards` - the standards a finding can cite.
- Supersedes `turbo-pr-review`.
