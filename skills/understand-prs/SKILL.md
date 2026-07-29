---
name: understand-prs
description: Work through PRs someone has sent Issei to review - a tight scannable brief per PR (one plain-English sentence, a few things worth learning, where the review actually stands including whatever the automated pass said) and then the part bots can't do: an explicit shortlist of where Issei's own judgement, product knowledge or completeness sense is needed, each with the cross-check already done and a drafted comment ready to go. Use when the user pastes one or more PR URLs or `<repo>#<n>` refs, or a whole handover message ("here's today's PRs", "comments have been addressed, please take a look"), and says review this / take a look / have a crack / walk me through / explain this PR / in laymen's terms / what does this do / thoughts on this / brief me on these / draft comments for this / where do you need me on this. Also fires on re-review phrases ("they pushed back", "they replied, take another look", "draft replies to these comments", "post with approval") and when picking PRs off `cdt-daily-pr-digest` or `my-open-prs`. Supersedes the former `turbo-pr-review` skill. Drafts inline comments in Issei's voice and posts only on explicit confirmation; never approves or merges without being told. Distinct from `pr-review-loop` / `pr-review-loop-lite` (unattended, automated, posts a bot verdict), `intech-tools:code-review` (heavy multi-agent audit), and `share-prs` (outbound - Issei's own PRs going to a reviewer).
---

# Understand PRs

Issei reviews across the whole of CDT - backend, infra, shared libraries,
frontend - usually without having written the surrounding code, and usually after
`pr-review-loop-lite` has already left an automated pass on the PR. Three things
follow from that, and this skill exists for all three.

**He arrives with no context.** The bot review is on the PR; he hasn't read it.
So a session that opens with "the automated pass said looks good, what do you
want to add?" starts from context he doesn't have. Always reconstruct it.

**The bot is a bot.** It reads the diff. It doesn't know the entity resolution
model, doesn't know which product operations exist beyond the ones this PR
touches, doesn't know that this pattern will want a base class the third time it
appears. Those are the comments only Issei can land, and today he only lands them
because he goes looking himself. **Surfacing them is this skill's primary output.**
A brief with no judgment shortlist and no account of why there isn't one has
failed, however good the explainer was.

**He is delegating the reading.** That is the whole point - he does not want to
go through the diff line by line. A brief that sprawls hands the reading cost
straight back to him and defeats the exercise. Brevity here is not politeness,
it is the feature. Budgets are given below and they are real.

Read [`references/judgment-lenses.md`](references/judgment-lenses.md) on every
invocation - it is how step 5 is actually executed. Read
`~/Knowledge Base/knowledge-vault/voice/code-review.md` before drafting any
comment. Do not read `voice/explaining-code.md` unless the user asks for a
teaching-shaped writeup; the brief format below supersedes it here.

## When to use

Fires when PRs arrive *for Issei to review*: a pasted URL, a set of refs, or a
whole handover message from Adele, Sean, Nikhil, Luke or an offshore contributor.
Also for re-review passes, and for author-side replies on his own PRs.

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
gh auth switch --user Issei-curve   # --user ikuzuki for personal
```

Run that as its own short command, once, at the start. Do not staple
`unset GITHUB_TOKEN` onto later commands: the `secrets-block` hook reads a long
scratchpad path or a 40-char commit SHA sitting near the word TOKEN as a leaked
credential and refuses the call. Auth persists, so once is enough.

Inbound messages vary wildly - a rich prioritised list, bare URLs with `- BFF` /
`- UI` labels, a Teams paste with mangled links. Parse out per PR: the ref, and
anything the sender asserted (priority order, "comments addressed", merge or
release dependencies). **Carry the sender's stated order through** unless you
find it wrong, and say so if you do.

Fetch every PR in parallel, one call each, batched in one message:

```bash
gh pr view <n> --repo curveanalytics/<repo> \
  --json number,title,body,headRefName,author,url,additions,deletions,files,reviewDecision,reviews,comments,mergeable,mergeStateStatus
```

Cache each head OID - posting needs it. Don't pull the diff yet.

### 2. Ingest the prior review - mandatory, never skipped

This is what fixes "Claude assumes I already have the context".

```bash
gh api repos/curveanalytics/<repo>/pulls/<n>/comments   # inline threads incl. author replies
gh api repos/curveanalytics/<repo>/pulls/<n>/reviews    # review bodies and verdicts
```

**Classify by marker first, author second.** `pr-review-loop` posts its reviews
**under Issei's own GitHub account**, so login alone tells you nothing:

- Body carries `<!-- pr-review-loop: reviewed-at=<oid> -->` → **automated**,
  whoever it appears to be from. Its verdict (`Looks good` / `Minor comments` /
  `Needs Changes` / `Needs Judgment`) is advisory. `Needs Judgment` is an explicit
  handoff - those lines go straight into step 5.
- No marker, author is a teammate → **human**. Never re-raise a point a human
  already made.
- No marker, and the reviewer **is the PR's own author** → a self-review. Common
  and legitimate (people walk their own diff before handing it over), but it is
  not independent scrutiny, so don't let it stand in for a review when judging
  how much this PR has actually been looked at. Say so plainly: "the two
  substantive passes are hers on her own PR". If you can't tell a genuine
  self-review from automation running on that person's token, say that too rather
  than picking one - it bears on how much confidence the existing review earns.
- No marker, author is Issei → **his own earlier review**, so this is a
  re-review. "His last review" means the most recent *unmarkered* review by his
  account; picking the most recent review by login will grab a bot pass and
  compute the wrong delta.

**An approval doesn't close later threads.** Issei may have approved, and another
reviewer may then have left open items on the same head. His approval stands; the
open items are the author's to action, not his to re-raise. Say whose court each
one is in, and don't let a stale approval read as "this PR is done".

Per thread record: who raised it, the author's reply, and whether it is settled
(concrete reason given - drop it), fixed (verify in the diff), or open. If the
marker's OID is behind the current head, the bot reviewed an older commit - say
so, because the delta is unreviewed.

### 3. Group or split

One line, before any analysis. Group on a shared ticket, an explicit cross-PR
dependency, an API contract, or a merge train. Split otherwise, even from the
same author. Surface the implied merge order when there is one.

### 4. The brief - one per PR, and it has to be scannable

Read the diff now: `gh pr diff <n>` (**not** `--patch` - that repeats files
per-commit and reports wrong line numbers). Pull context on demand with
`gh api repos/curveanalytics/<repo>/contents/<path>?ref=<head-oid>`.

Use this shape, with these headings, because it is the one Issei can read at a
glance. **Lead with it** - `### One sentence` is the first thing on the page. If
you need to correct the sender's premise or note that he has already reviewed the
PR, that goes in a single line *above* the heading or inside **Where the review
stands**; a three-paragraph preamble in front of the summary defeats the format,
because the one sentence he wanted is now below the fold.

```
### One sentence
<what changes for the system or the user. One sentence. No class, module or
field names. If it needs two sentences the PR is doing two things - say that,
it's a finding.>

### Worth knowing
- <3-5 bullets, ONE LINE each, ~25 words max>

### Where the review stands
- <what the automated pass said, what the author replied, which threads are
  settled / fixed / open. 1-3 lines on a simple history; scale up to ~6 bullets
  when the PR genuinely has several passes, a dismissed approval or a red build>

### Where you're needed
- <step 5; the only section allowed to run long>
```

**Budgets, and they bind - on the explainer, not on the facts.** Bullets, not
prose; prose is what makes these unreadable. **One sentence** and **Worth
knowing** are hard budgets: one sentence, and 3-5 bullets of one line each.

One line means about 25 words. When a point genuinely needs more - an off-diff
fix, a mechanism with a real subtlety - **split it into two bullets rather than
running one to 50-odd words**. Two scannable lines carry the same content and
survive a skim; one long line is the thing that makes him stop reading.

**Budget the words per finding, never the number of findings.** The tempting way
to hit a budget is to drop the second and third things you found and keep the
headline - and that is the one move that makes this skill worthless, because the
secondary findings are exactly what he cannot get anywhere else. A live edge case
nobody has hit yet, a test that only passes through mock leakage, a scoping
insight that changes how a follow-up ticket should be written: those are the
output. If four things are worth knowing, write four tight bullets. If three gaps
are real, list three. Shorten the prose, split long bullets, cut the padding and
the restatement - never cut a finding to make the brief look tidy. A short brief
that dropped a real finding has failed worse than a long one that kept it.

**Where the review stands** scales with the review history, because compressing a
genuinely tangled state (two bot passes, a dismissed approval, one of his own
earlier reviews, a red build) into three lines drops facts he needs. Prefer six
honest bullets to three lossy ones. What you must not do is pad a simple history
to look thorough.

**Worth knowing** is for his learning: the mechanism and why that one, any
technology or protocol feature he may not have met, the non-obvious constraint
being worked around, the bit easy to get wrong. Unpack every acronym inline every
time, even repeats within one session - IDOR, TOCTOU, GSI, ULID,
`TransactWriteItems`, permission boundary, prefix list, row policy, projection.
Prefer an analogy anchored in something he knows. Never "adds tests", "follows
existing patterns", "uses type hints" - that is filler.

**Two independent dials for frontend, do not collapse them.** On
`intech-experience-ui` and similar, thin **Worth knowing** to a single line - he
is a high-level reviewer there by choice and does not want UI internals taught to
him. Keep **Where you're needed** at *full strength*: correctness, product
behaviour and completeness matter just as much on the frontend, and real defects
live there (a validation effect that can never fire, tests green only through
mock leakage, a ticket premise the API can't support). Shallow teaching, full
scrutiny.

Backend, infra, shared libraries, data and schema work: **Worth knowing** earns
its space. Terraform and IAM always do - blast radius is the learning.

Name the bot as a bot. "The automated pass said looks good" - never present it as
review cover.

### 5. Surface the judgment calls

Run the lenses in [`references/judgment-lenses.md`](references/judgment-lenses.md).
**Do the cross-check yourself before surfacing anything** - the value is arriving
with the work done, not handing him a list of things to go and check.

So: when the PR touches a modelled concept, go and read the model. Fetch the
design doc or ADR via the Atlassian MCP (`search`, then `getConfluencePage`) and
the linked ticket **including its comments** - deferrals and decisions live in the
comments, not the body. Enumerate the cases the model defines and map the PR
against each one. The canonical example: a PR improved a pre-publish impact
preview for re-parent and deprecation, the bot said looks good, and the real
finding was that four *other* entity operations either produced no signal or
collapsed into a generic bucket. Nothing in the diff says that. Only the model
does.

Each item takes this shape - separate lines, question last:

```
- <what you checked it against> - <the gap, in a sentence or two>.
  <In scope for this PR, or a follow-up.>
  <The question he is being asked.>
  Draft: "<the comment, in voice, ready to post>"
```

**Keep each item to about 80 words across those lines, and never write it as one
paragraph.** A 200-word block has to be read twice to find the question at the
end, which is precisely the cost this section is supposed to save him. The
reasoning that earned the finding belongs in the draft comment, where the author
will read it - not in the summary he is skimming to decide what to do.

**End on the question, not your conclusion.** Landing on "my read: cut the
ticket" or "marker only" quietly takes the decision off him, which is the one
thing this section must not do. Have a view and put it in the body if it helps -
but the closing line is his call to make: "in scope or follow-up ticket?", "is
that actually how the product behaves?", "hold the merge for this?"

Where the honest answer is "the scope was these two cases, so this is a follow-up
not a blocker", draft it that way - name the gap, say you're not asking now,
suggest the ticket, leave timing with the author. That framing is what stops it
reading as scope creep.

**If nothing survives the lenses, say so and name the lenses you ran.** "Ran
completeness against the model doc, blast radius across the three consumers, and
migration - nothing needing your input, the bot's read holds" is a good answer.
Silence is not.

### 6. Draft comments in voice

Conversational mode by default - short, direct, lowercase fine, British English,
no em dashes (` - ` instead), no apology, no "happy to discuss", no preamble, no
summary at the bottom.

Per comment: **target** (`path/file.py:LINE`, the line inside a diff hunk,
verified by matching the code the finding refers to rather than trusting a
remembered number - model-level, scope or product points go in the top-level body
instead), **body** (`nit:` prefix if low-stakes; question form when ~80% sure;
concrete fix when obvious), and **rationale** (one line for Issei, not posted).

Categorise: real bugs, then design and judgment questions, then nits. Don't
re-raise what a human already raised or re-litigate settled conventions.

### 7. Surface for confirm

Every draft in chat, grouped by category, count at the top. **Wait for explicit
confirmation before posting**, always. On a revise request, redraft only those.

### 8. Post

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

When Issei has already reviewed and the author has pushed or replied - or it's his
own PR with reviewer comments waiting - review only the **delta** and reply *into*
existing threads.

**Delta detect.** Take the most recent *unmarkered* review by his account (see
step 2); its `commit_id` is the head he last saw. Diff that against current head
and review only the new lines plus enough context to judge them. Pull threaded
replies from `.../pulls/<n>/comments` and find threads he started that now carry a
newer reply.

**When the delta is empty or trivial** - a pure `main` merge, a lockfile bump,
formatting - say so in one line and make the *open threads* the lead: "nothing to
review in the delta, it's a main merge. What's actually outstanding is your
completeness comment from the 24th, still unanswered." An empty delta is a
common and useful outcome, not a dead end; don't pad it into a fresh review.

**Reviewer mode (someone else's PR).** Fixed → brief acknowledgement ("ah true
yeah good point") or resolve silently. Pushed back → re-engage only with genuinely
new reasoning, engaging their argument explicitly. Fix claimed but not in the
delta → "has this landed? not seeing it in the latest push". New issues → fresh
comments per step 6. Re-run step 5: a judgment gap can appear in the delta.

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
- **The deferral frame** for step 5: what you checked, what's missing, "not
  asking for this now given the PR's scope was X", suggest a ticket, "now or
  later, your call".

Avoid: em dashes; "just a thought" / "feel free to ignore" / "happy to discuss";
"I think" more than once or twice; previewing a comment before making it; a
summary at the bottom.

## Multi-PR handling

One short theme paragraph, then a brief per PR, then cross-PR findings (a
lockfile pinned to an unreleased hub version, a contract adopted inconsistently).
Comments post per-PR - GitHub has no cross-PR threads - but each top-level body
can reference the others. For 5+ batches, compress the mechanical ones to two
lines each and spend the budget on the meaty ones; say which you compressed.

## Environment notes

- **Two Atlassian MCP servers are configured.** The one under `intech-tools`
  times out at 300s fairly often. When it does, fall back to the other configured
  Atlassian server rather than giving up on the cross-check - the cross-check is
  the point of step 5. Its `cloudId` has to be discovered via
  `getAccessibleAtlassianResources`, not passed as the site hostname.
- `getJiraIssue` returns the whole description even when you ask for two fields.
  For several tickets at once, `searchJiraIssuesUsingJql` with a key-set filter
  (`key in (CDT-1, CDT-2)`) is one call and far terser.
- Keep the `unset GITHUB_TOKEN` line short and separate (step 1) so the
  `secrets-block` hook doesn't reject it.

## Self-check before delivering

- [ ] Did I read the prior automated review and the author's replies, and say
      where each thread stands?
- [ ] Did I classify reviews by **marker first**, not by author login?
- [ ] Do the first three sections of each brief fit on one screen, in bullets?
- [ ] One sentence, plain English, no class names?
- [ ] Acronyms unpacked inline, even repeats?
- [ ] Frontend: thinned **Worth knowing** but kept **Where you're needed** at
      full strength?
- [ ] **Lenses run, cross-checks done by me, findings surfaced - or the clean
      lenses named?**
- [ ] Does every judgment item END on a question rather than my verdict?
- [ ] Comments categorised, `nit:` where it applies, nothing re-raised?
- [ ] Every inline anchor verified against a hunk by matching code?
- [ ] Nothing posted without explicit confirmation; `event=COMMENT`; no merge?

## Anti-patterns

- **Opening as if he has read the bot review.** Step 2 is not optional.
- **Skipping the judgment shortlist because the bot said looks good.** That is
  the case this skill exists for.
- **Sprawl.** A brief he has to *read* rather than skim has failed, no matter how
  accurate. Bullets, one line, budgets held.
- **Hitting the budget by dropping findings.** Shorten the prose, keep the
  finding. Dropping the second and third thing you found is the worst possible
  way to be brief.
- **A preamble in front of `### One sentence`.**
- **A judgment item written as one long paragraph with the question buried.**
- **Listing things for him to check instead of checking them.** "You might want
  to verify this against the entity model" is the failure mode.
- **Reading frontend as "review it shallowly".** Teach less, scrutinise the same.
- **Closing a judgment item on your own verdict.**
- **Turning every judgment item into a blocker.** Most are follow-up tickets.
- **Re-raising a settled point.** A concrete rebuttal - especially "that API
  doesn't exist in the pinned version" - wins.
- **Reading the Jira body but not its comments.**
- **Classifying reviews by author login** when the bot posts as Issei.
- **Trusting remembered line numbers.**
- **Auto-approving, bundling APPROVE with comments, or merging.**

## Scope

The human-in-the-loop review companion: reconstruct context, teach briefly,
surface where the human is needed, draft in voice, post on confirmation. No
specialist sub-agent panels, no citation gates, no SemVer or breaking-change
audits (CDT is pre-1.0 - no MAJOR-bump recommendations), nothing posted
unprompted, no approving or merging. Specialist fan-out audit →
`intech-tools:code-review`; unattended batch review → `pr-review-loop-lite`.

## References

- [`references/judgment-lenses.md`](references/judgment-lenses.md) - the lenses
  for step 5, each with its cross-check and comment frame. Read every invocation.
- `~/Knowledge Base/knowledge-vault/voice/code-review.md` - canonical PR comment
  voice. Read before drafting.
- `share-prs` - the outbound counterpart.
- `pr-review-loop-lite` - what left the automated pass this skill ingests; its
  marker and verdict vocabulary are shared.
- `intech-tools:coding-standards` - the standards a finding can cite.
- Supersedes `turbo-pr-review`.
