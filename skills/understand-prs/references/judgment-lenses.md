# Judgment lenses

Where a human reviewer beats an automated pass. The bot reads the diff; every
lens below needs something the diff doesn't contain - the domain model, the
product's behaviour, the other consumers, the live data, the decision history.

Run each lens. **Do the cross-check yourself.** Bring findings, not homework.

---

## 1. Completeness against the model

**The highest-yield lens.** A PR handles the cases in front of it. The model
defines more.

**Cross-check:** identify the modelled concept the PR touches (entity
resolution, dispatch contract, serving version, ingestion outcome, capacity
pool). Find its design doc or ADR - Atlassian MCP `search`, then
`getConfluencePage`. Enumerate the *full* set of operations, states or variants
the model defines. Map the PR's handling against each one, individually.

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

## 2. Product behaviour

The code is internally consistent and still wrong about how the product works.

**Cross-check:** read the ticket *and its comments*, and any linked doc. Then ask
what an operator or the BFF actually does with this. Does the change alter what
someone sees, in a way nobody signed off? Is an edge case being handled in a way
that's technically defensible and behaviourally surprising - a silent default, a
fallback that hides a real state, an error surfaced as an empty result?

**Question for Issei:** is that actually how it behaves / how we want it to
behave?

---

## 3. Blast radius

Who else consumes this, and did the PR check them?

**Cross-check:** for a shared contract (`intech-hub` schemas, dispatch payloads,
serving response shapes, ClickHouse table definitions), grep the other repos for
consumers. `gh search code` across `curveanalytics`, or the local checkouts. For
Terraform and IAM: what does the widened policy now permit that it didn't, and
does anything else assume the narrower version? Watch for the two-buckets-per-
plane trap - resolve *which* bucket or table before claiming a writer is
affected.

Merge order counts here too: a consumer pinned to an unreleased library version
is a real finding, but it's a merge-order note rather than a defect.

**Question for Issei:** does this need the consumers moved in the same window, or
is it safely additive?

---

## 4. Migration and live data

New code, existing rows.

**Cross-check:** does the change alter a schema, a partition key, a tag
requirement or a default? What happens to data written before it? Is there a
backfill, and if the answer is "dev only, nothing to migrate", is that still true
of staging and prod? Anything hand-seeded per environment (secrets, policies,
credentials) is a classic silent breakage on promotion.

**Question for Issei:** is there existing data this doesn't cover, and does
staging or prod differ from dev here?

---

## 5. Operability

If this breaks at 3am, does anyone find out?

**Cross-check:** new failure paths - are they observable? A new external
dependency, a new queue, a new table: is there an alarm, and does the failure
show up as a metric or only as a log line nobody reads? A fail-closed default is
usually right and it needs to be loud when it fires.

**Question for Issei:** does this need an alarm, or is it covered by what's
already there?

---

## 6. Second consumer / premature abstraction

The YAGNI-flagged observation. Not a request - a marker for the future.

**Cross-check:** does this diff establish a pattern that a second config type,
entity type or pipeline will obviously want? Note it *without* asking for the
extraction now.

**Comment frame:**

> Separate point: this <pattern> would be useful for <other cases> down the line
> too. Not suggesting we extract a base class now (YAGNI), just flagging it as a
> natural second-consumer refactor whenever that need actually shows up.

**Question for Issei:** worth flagging, or noise?

---

## 7. Scope boundary

Did the PR do what the ticket asked - and only that?

**Cross-check:** ticket intent versus the diff. Scope creep matters less than
scope *miss*: an acceptance criterion in the ticket with no corresponding change,
or a deferral agreed in the ticket comments that the PR quietly re-implements.
Read the comments.

**Question for Issei:** is the missing piece deliberate, or has it been lost?

---

## 8. Decision archaeology

Has this been settled before?

**Cross-check:** the ticket comments, prior PR threads on the same files, and the
owning ADR. A change that reverses a documented decision without saying so is a
finding; so is one that re-litigates something the team agreed two sprints ago.
Where the decision holds and the code diverges, the ADR needs the update - not a
new doc.

**Question for Issei:** does this need the ADR updating, or is the decision
genuinely changing?

---

## Grading what comes out

| Grade | Meaning | Framing |
|---|---|---|
| Blocker | The PR is wrong as written | Firm, concrete, direct |
| In-scope gap | Inside what the ticket asked for, and missing | Ask for it |
| Out-of-scope gap | Real, outside this PR's remit | Name it, "not asking now", suggest the ticket, leave timing with the author |
| Marker | Future consideration, no action | One line, explicitly YAGNI-flagged |

Most step 5 output is the bottom two rows. Grading everything as a blocker is how
this lens loses its credibility.

## When nothing lands

Say which lenses ran and came back clean. "Ran completeness against the entity
model, blast radius across the three consumers, and migration - nothing needing
your input, the bot's read holds" is a real answer. Inventing a judgment call to
fill the section is worse than an empty section.
