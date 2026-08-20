# Judgment lenses

Where a human reviewer beats an automated pass. The bot reads the diff; every
lens here needs something the diff doesn't contain - the ticket's premise, the
platform's layering, the domain model, the other consumers, the live data, the
decision history.

**Two tiers, and the order matters.**

**Tier A - shape.** Should this PR exist, in this form, in this repo, at this
layer, and what does it lock us into. These are the questions no bot asks and the
ones Issei is uniquely placed to answer, because answering them needs the
platform's direction in your head, not just its code. A Tier A finding usually
reframes or moots the Tier B ones, which is why it comes first.

Tier A splits again:

- **A1-A8, the core - run on every PR, including small ones.** A 40-line PR in
  the wrong repo is still in the wrong repo. None of these costs an extra fetch:
  A1-A6 fall out of the placement work in step 4, A7-A8 out of reading the diff.
- **A9-A11, gated - run when the PR touches the trigger named on the lens.**
  Cost, tenancy and rollout only bite on some changes, and running them on a
  docstring fix is theatre. Say which gated lenses the PR triggered.

**Tier B - correctness and completeness.** Is the thing it's doing right and
finished. Still valuable, still frequently where the concrete bugs are, but
partially covered by the automated pass. Spend the second half of your effort
here, and skip re-stating anything the bot already found.

**Do the cross-check yourself. Bring findings, not homework.**

Most output from both tiers is a follow-up ticket or a marker, not a blocker.
Grade honestly (table at the bottom) - grading everything as a blocker is how
these lenses lose their credibility.

---

# Tier A - shape

## A1. Necessity

Does this need to exist at all?

**Cross-check:** read the ticket *and its comments* and the parent epic's
siblings. Then ask: is the outcome already available somewhere - in `intech-hub`,
in another plane, in a helper written for a neighbouring feature? Has a later
decision made the ticket's premise stale, so the PR faithfully implements
something the platform no longer needs? Was this work deliberately parked in a
design doc or an ADR, with the parking now silently reversed? Does an adjacent
sibling ticket make this redundant, or vice versa?

The commonest live version: the ticket was written three sprints ago, the model
moved underneath it, and the PR is correct against the ticket and wrong against
the platform.

**Question for Issei:** is this still the work we want, or has the ticket gone
stale?

---

## A2. Shape - is the feature built the right way?

The code passes and the mechanism is wrong.

**Cross-check:** find what the design doc or ADR says the mechanism should be
(Atlassian MCP `search`, then `getConfluencePage`), and compare. Then look for
the tells that a shape is off independent of any doc: a hand-rolled version of
something the platform already has a pattern for; state kept in a second place
rather than derived from the first; a config value read at a point that can't see
the whole config; polling where the platform uses events, or the reverse;
behaviour encoded in a name or a string rather than a type; a change whose
correctness can only be established against a deployed environment.

Ask whether this is the mechanism you'd choose knowing the next three tickets on
the epic, or the one that was reachable from where the author was standing.

**Question for Issei:** is that the mechanism we want here, or is it a local
workaround that happens to pass?

---

## A3. Splitting

Should this be two PRs, or two tickets?

**Cross-check:** the "one sentence" test from the brief is the detector - if the
change can't be stated in one sentence without an "and", it's doing two things.
Then decide whether the two things are genuinely coupled (one is unusable without
the other) or merely adjacent (a refactor bundled with a feature, a schema change
bundled with the reader that uses it, an unrelated drive-by fix).

Two adjacent things in one PR costs review quality and costs revert granularity.
Say which of the two is the risky half - that's usually the real point, because
it's the half that a bundled PR hides.

**Question for Issei:** worth asking them to split it, or fine to review as one?

---

## A4. Ownership - where does this belong?

The right code in the wrong home.

**Cross-check:** three separate questions. **Repo:** is this logic specific to
this service, or will the next consumer want it - a schema, a client, a contract,
a validation rule all point at `intech-hub`. Check whether a second consumer is
already visible in another repo (`gh search code` across `curveanalytics`, or the
local checkouts). **Plane:** does control plane, data plane, transform or compute
own this concept - a config the control plane owns being written by the data
plane is a boundary violation even when it works. **Layer:** within the repo, is
this at the layer that owns the concern, or has it landed in the nearest file to
where the author was working? **Maintenance:** does this add something on-call
now has to know about - a new dependency, a new runtime, a vendored fork, a
bespoke component only its author understands? Adding to what the team carries is
itself a decision, and it is usually made silently.

Watch the two-buckets-per-plane trap: resolve *which* bucket or table before
claiming a writer is affected.

Where the second consumer is real but not yet here, this is a marker, not a
request - do not ask for the extraction now:

> Separate point: this <pattern> would be useful for <other cases> down the line
> too. Not suggesting we lift it into hub now (YAGNI), just flagging it as the
> natural second-consumer refactor whenever that need actually shows up.

**Question for Issei:** does this belong in hub / in the other plane, or is here
right for now?

---

## A5. Depth of fix

Fixed where the problem is, or where the symptom showed up?

**Cross-check:** trace the failure back past the changed line. Is the guard added
in the consumer because the producer emits something it shouldn't? Is the
defensive default masking a state that ought to be impossible? Is the test
asserting the workaround rather than the behaviour? A fix one layer downstream of
the cause works, ships, and leaves the cause live for the next consumer.

This is the lens that catches the fix that will be re-applied three more times in
three more places.

**Question for Issei:** fix it here, or push it back to where it originates?

---

## A6. Done-ness

Is the feature usable, or just present?

**Cross-check:** follow the new code to a caller. A component with no caller, a
route with no consumer, a table with no writer, a flag nobody reads: each is
legitimate as a deliberate step in an epic and a problem when it's mistaken for a
finished feature. Establish which from the epic position (placement, step 4). If
it *is* a deliberate step, the finding is about sequencing - what has to land next
for this to do anything, and is that ticket open.

The related smell is a feature complete in code and incomplete in operation - no
way to configure it, no way to see it working, no way to turn it off.

**Question for Issei:** is the follow-on tracked, or does this sit inert until
someone notices?

---

## A7. Conceptual integrity

A third way of doing something, or a second meaning for a word.

**Cross-check:** the vocabulary first. Does the PR introduce a new term for a
concept the platform already names, or reuse an existing term for a different
thing - two meanings of *version*, *snapshot*, *publish*, *tenant*, *entity*?
Then the patterns: is this the second or third mechanism for the same concern - a
second config loader, a second HTTP client, a second convention for naming
ClickHouse partitions, a second way of passing a window?

No single PR is guilty of divergence; it accumulates, and the person reading
across repos is the only one positioned to see it. Two patterns for one concern
is worse than either pattern on its own.

Naming is the cheapest thing to fix before merge and among the most expensive
after, because the name propagates out into tickets, docs and other people's
code.

**Question for Issei:** is that the name and the pattern we want, or is it
colliding with one we already have?

---

## A8. Reversibility

Which parts of this are one-way doors?

**Cross-check:** sort the change into two piles. Cheap to rewrite next sprint:
internal functions, private helpers, log lines, anything with one caller inside
the repo. Expensive or impossible to undo once it has been used: a response shape
the BFF adopts, an event contract a consumer subscribes to, a partition or
sorting key, a column written in a format you would have to migrate, a published
artefact's name, a permission granted, a table that has started taking writes.

Then spend the rest of the review on the second pile and let the first go.

This lens also tells you when *not* to spend judgement: a large PR with no
one-way doors deserves a lighter review than its line count suggests, and a
20-line PR that fixes a sorting key deserves far more.

**Question for Issei:** anything here we can't cheaply undo, and is that bit
right?

---

## A9. Cost and scale envelope

*Triggers on:* a query, a loop over rows, entities or tenants, a fan-out, or new
always-on infrastructure.

**Cross-check:** what does this do at production volume rather than dev's? A
per-row query inside a loop, an unbounded fan-out across tenants, a scan where
the sorting key isn't used, a join whose right side grows with entities, a
response that pages nothing. Dev row counts lie systematically and the automated
pass has no idea what the real ones are.

Money counts as a finding too: a new always-on task, a shard, a replica,
cross-AZ transfer, or a query pattern that keeps a cluster warm that used to
idle.

**Question for Issei:** does this hold at prod volume, or does it need a
different access pattern?

---

## A10. Trust and tenancy boundary

*Triggers on:* auth, tenant scoping, row policies, IAM, a cross-plane call, or
user-supplied input reaching a query, a path or a template.

**Cross-check:** trace the tenant identity from where it enters the request to
where it is enforced, and **count the layers**. The platform's model is defence
in depth - the serving composer's own `tenant_id` filter plus the per-tenant row
policy beneath it - so the finding is rarely "this is unfiltered". It is "this is
now the only layer", or "this path bypasses one of the two", or "the claim is
trusted one hop earlier than it's verified". Same shape for IAM: what does the
widened grant permit that it didn't, and is the boundary still where the doc says
it is?

Multi-hop reasoning across a request path is precisely what a diff-reading bot
cannot do, which makes this the highest-stakes lens on the list.

**Question for Issei:** is that still two layers, or has this become the only
thing standing between two tenants?

---

## A11. Rollout and rollback

*Triggers on:* a schema change, a contract or event shape, a cross-repo version
pin, or infrastructure.

**Cross-check:** can this deploy on its own, or does it need a lockstep release
with a consumer? Is it expand-contract, or do the old and new code fail to
coexist during the deploy window - which they must, because both are live at
once. And the part almost everyone skips: after this has run in prod for a day
and written data in the new shape, what does rolling back actually do to that
data?

A8 asks whether the door is one-way. This asks whether you can get through it
safely at all.

**Question for Issei:** can this go out on its own, and can we roll it back once
it has written data?

---

# Tier B - correctness and completeness

## B1. Completeness against the model

**The highest-yield Tier B lens.** A PR handles the cases in front of it; the
model defines more.

**Cross-check:** identify the modelled concept the PR touches (entity resolution,
dispatch contract, serving version, ingestion outcome, capacity pool). Find its
design doc or ADR. Enumerate the *full* set of operations, states or variants the
model defines, and map the PR against each one individually.

Ask of each unhandled case: does it produce no signal at all, or does it collapse
into a generic bucket with nothing to discriminate it? Both are findings, and the
second is the sneakier one - it looks handled.

**Worked example.** A pre-publish impact preview PR covered re-parent and
deprecation; the bot approved it. Reading the entity resolution model gave the
full operation set, and four fell through: cache correction produced no signal
(it touches none of the fields the diff keys on), re-type landed in the same
generic "changed" bucket as rename with nothing to tell them apart, approve was
indistinguishable from a plain add, and merge carried only the loser's
`status_changed` with no survivor information. None of that is visible in the
diff.

**Comment frame:**

> Checked this against the <model> doc - a few operations aren't distinctly
> represented: <case> produces no signal at all (<why>), <case> falls through to
> the same generic bucket as <other> with nothing to discriminate them, <case>
> looks identical to <other>. Not asking for this now given the PR's scope was
> specifically <the two in scope>, but worth a follow-up ticket for the rest
> whenever those flows get built out - now or later, your call.

**Question for Issei:** follow-up ticket now, or leave it until those flows get
built?

---

## B2. Product behaviour

Internally consistent and still wrong about how the product works.

**Cross-check:** the ticket and its comments, plus any linked doc. Then ask what
an operator or the BFF actually does with this. Does the change alter what
someone sees, in a way nobody signed off? Is an edge case handled in a way that's
technically defensible and behaviourally surprising - a silent default, a
fallback that hides a real state, an error surfaced as an empty result?

**Question for Issei:** is that actually how it behaves, and how we want it to?

---

## B3. Blast radius

Who else consumes this, and did the PR check them?

**Cross-check:** for a shared contract (`intech-hub` schemas, dispatch payloads,
serving response shapes, ClickHouse table definitions), grep the other repos for
consumers - `gh search code` across `curveanalytics`, or the local checkouts. For
Terraform and IAM: what does the widened policy now permit that it didn't, and
does anything else assume the narrower version?

Merge order counts here: a consumer pinned to an unreleased library version is a
real finding, but it's a merge-order note rather than a defect.

**Question for Issei:** does this need the consumers moved in the same window, or
is it safely additive?

---

## B4. Migration and live data

New code, existing rows.

**Cross-check:** does the change alter a schema, a partition key, a tag
requirement or a default? What happens to data written before it? Is there a
backfill, and if the answer is "dev only, nothing to migrate", is that still true
of staging and prod? Anything hand-seeded per environment (secrets, policies,
credentials) is a classic silent breakage on promotion.

**Question for Issei:** is there existing data this doesn't cover, and does
staging or prod differ from dev here?

---

## B5. Operability

If this breaks at 3am, does anyone find out?

**Cross-check:** new failure paths - are they observable? A new external
dependency, a new queue, a new table: is there an alarm, and does the failure
show up as a metric or only as a log line nobody reads? A fail-closed default is
usually right and it needs to be loud when it fires.

Then degradation: when the new dependency is down, does the request fail, degrade
or serve stale - and was that chosen, or is it whatever the code happened to do?

**Question for Issei:** does this need an alarm, or is it covered by what's
already there?

---

## B6. Scope boundary

Did the PR do what the ticket asked, and only that?

**Cross-check:** ticket intent versus the diff. Scope creep matters less than
scope *miss*: an acceptance criterion with no corresponding change, or a deferral
agreed in the ticket comments that the PR quietly re-implements. Read the
comments.

**Question for Issei:** is the missing piece deliberate, or has it been lost?

---

## B7. Decision archaeology

Has this been settled before?

**Cross-check:** the ticket comments, prior PR threads on the same files, and the
owning ADR. A change that reverses a documented decision without saying so is a
finding; so is one that re-litigates something agreed two sprints ago. Where the
decision holds and the code diverges, the ADR needs updating - not a new doc.

**Question for Issei:** does this need the ADR updating, or is the decision
genuinely changing?

---

# Grading what comes out

| Grade | Meaning | Framing |
|---|---|---|
| Blocker | The PR is wrong as written | Firm, concrete, direct |
| In-scope gap | Inside what the ticket asked for, and missing | Ask for it |
| Out-of-scope gap | Real, outside this PR's remit | Name it, "not asking now", suggest the ticket, leave timing with the author |
| Marker | Future consideration, no action | One line, explicitly YAGNI-flagged |

Tier A findings skew towards the top two rows more often than Tier B ones do -
"this belongs in hub" or "this should be two PRs" is cheap to act on before merge
and expensive after. But most output across both tiers is still the bottom two
rows.

# When nothing lands

Name the lenses that ran and came back clean, and name the gated ones the PR
triggered. "Ran the core - it's hub-shaped but there's no second consumer yet so
that's a marker at most, and nothing here is a one-way door. Triggered tenancy
because it touches the row policy: still two layers. Plus completeness against
the entity model and blast radius across the three consumers. Nothing needing
your input, the bot's read holds" is a real answer.

Inventing a judgment call to fill the section is worse than an empty section. So
is claiming a gated lens ran when its trigger never fired - say it didn't apply.
