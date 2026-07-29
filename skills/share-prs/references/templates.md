# Bullet anatomy, registers, worked examples

> **The examples below are illustrations of shape, not source material.** Their
> repos, PR numbers, tickets and claims are deliberately fictional so they can't
> be mistaken for live state. Derive every bullet from the PR and ticket you
> actually fetched. If an example ever looks like it matches the batch in front of
> you, that is a coincidence to ignore, not a shortcut to take - paraphrasing an
> example ships its claims, and they are made up.

## The bullet, part by part

Full form:

```
* [<plain-English what-it-does> (<repo> #<n>)](<pr-url>) ([CDT-NNN](<jira-url>)). <What it does, one sentence, outcome-shaped.> <Why look here / where it sits / merge order.> <Review state and what changed.> (<Scope note>)
```

Terse form:

```
* [<repo> #<n>](<pr-url>) ([CDT-NNN](<jira-url>)) - <what it is, one clause>. <optional one-clause steer>
```

The parts:

**Link text.** In full form the link text *is* the description - a short
plain-English clause plus the repo and number, so the bullet reads as a sentence
before the reader touches the URL. In terse form it's just `<repo> #<n>` and the
clause follows after a hyphen. Never use the PR title verbatim if it's a
conventional-commit string.

**Ticket link.** Immediately after the PR link, in brackets. Omit when the whole
batch is one ticket (say it once in the opening line) or when the PR genuinely
has no ticket.

**What it does.** One sentence, present tense, framed as the outcome for the
system rather than the mechanism in the code. "Reads the configured cap for a
shared external API and stamps each dispatched step with its slice of it" - not
"adds a `CapacityResolver` to the assembler".

**Why look here.** The steer. Which of these applies:
- Position in a chain: "this is the one everything else hangs off, so worth
  starting here", "goes in after #86", "needs that release in first".
- Where the risk is: "small but it's the one with teeth, so worth a proper look".
- What it unblocks: "Rad is waiting on this landing before he rebases".
- Nothing, for a mechanical change. Say nothing rather than padding.

**Review state.** Only when it isn't a fresh first review. Concrete about what
changed: "back for a re-review: the nit is fixed and the two judgment calls are
answered inline with reasoning", "already reviewed and marked looks good, so this
just needs the approve click", "showing conflicts for now".

**Scope note.** Parenthetical, at the end, and it must be informative about
*shape* not just count. Include: source vs test split, infrastructure and whether
it carries new IAM, whether tests are green, and anything that makes a big file
count less scary. "(18 files: 12 source and infra, 6 tests; the 2 Terraform files
are documentation only, no new IAM)" is the standard to hit.

**Length.** Terse bullets land at 25 words or under. Full bullets land at 60 or
under and never exceed 70 - count if you're unsure. **Count the link text too**,
since it's part of what the reader reads; only the bare URL inside the parentheses
is free. The ceiling is what keeps the message a handover rather than a review;
detail beyond it goes in the PR body or the note to Issei.

## Register: which form per PR

Not two templates - one template with per-PR weight. Both registers routinely
appear in the same message.

| PR shape | Register |
|---|---|
| New contract, new package, anything downstream depends on | Full, 3-4 sentences, scope note |
| Real logic change with a judgment call in it | Full, 2-3 sentences, scope note |
| Wiring an already-agreed contract through one repo | Terse plus a merge-order clause |
| Pure deletion, rename, single-line permission widen | Terse, one clause, no scope note |
| Infrastructure only (alarms, dashboards, policies) | Terse, plus who it mirrors if relevant |
| Frontend / UI | Terse - the reviewer's lens there is behaviour, not code |

## Worked example - full register, re-review batch

Illustrative only. Note the bullets sit at roughly 45-60 words, not 130.

```
Morning Adele, these are back for a re-review with the comments addressed. In merge order, and the first one is the chunky one.

* [Working out a step's share of a shared rate limit (example-control-plane #401)](https://github.com/example-org/example-control-plane/pull/401) ([EXP-101](https://curve-analytics.atlassian.net/browse/EXP-101)). Reads the configured cap for a shared external API and stamps each dispatched step with its slice of it, failing closed if a pool has no cap configured. Everything else in the capacity chain sits behind this one, so it's the big one. The nit is fixed and both judgment calls are answered inline. (New four-file capacity package plus assembler and handler wiring, Terraform for one table, tests across four modules)
* [Actually taking and giving back capacity in the router (example-compute-plane #402)](https://github.com/example-org/example-compute-plane/pull/402) ([EXP-102](https://curve-analytics.atlassian.net/browse/EXP-102)). Makes the caps real: the router claims a lease before running work and releases it on completion, sweep or cancellation, so we stop hammering rate-limited third party APIs. Goes in after #401. Previous round's changes are made. (One new module plus wiring through five existing ones, Terraform for the leases table and three IAM policies, two new test modules, all green)
* [S3 client no longer needs bucket-wide list permission (example-hub #403)](https://github.com/example-org/example-hub/pull/403) ([EXP-103](https://curve-analytics.atlassian.net/browse/EXP-103)). The connection check used to list a whole bucket just to prove it could reach it, forcing every consumer onto a broader role than it needed. Now opt-in and bounded. Reviewed and marked looks good, and Rad's rebase is waiting on it landing. (One source file, one README line, its tests)

Whenever you get a window.
```

## Worked example - mixed register, one ticket

Ticket linked once in the opening line, so the bullets carry no ticket link.
Illustrative only.

```
Afternoon Sean, the widget-ingest chain is up, all [EXP-200](https://curve-analytics.atlassian.net/browse/EXP-200). In merge order - the hub one first since the rest pin to its release. Mostly small, one worth a proper look.

* [example-hub #410](https://github.com/example-org/example-hub/pull/410) - the producer contract, widget_id addressing and the object tagging. Everything else hangs off this so worth starting here
* [example-data-plane #411](https://github.com/example-org/example-data-plane/pull/411) - deletes the dead 501 stub, pure removal
* [example-compute-plane #412](https://github.com/example-org/example-compute-plane/pull/412) - addresses ingest input by widget_id
* [example-control-plane #413](https://github.com/example-org/example-control-plane/pull/413) - carries widget_id on the dispatch source config refs
* [example-data-plane #414](https://github.com/example-org/example-data-plane/pull/414) - requires the widget_id object tag on the data buckets. Small but it's the one with teeth, so worth a proper look
* [example-data-plane #415](https://github.com/example-org/example-data-plane/pull/415) - CloudWatch alarms and a dashboard, mirrors what you did on the control plane
* [example-data-plane #416](https://github.com/example-org/example-data-plane/pull/416) - partitions gold by version plus a rebuild script

No rush on any of them.
```

## Opening line patterns

Whatever you pick, it has to read as a sentence someone would type. A link needs a
phrase around it: "the widget-ingest chain is up, all under [EXP-200](url)" reads
fine; "quick one on the EXP-200 chain, all [EXP-200](url)" is a dumped link and a
repeated key, and it looks careless in something pasted straight to a colleague.
Read the opener back before you hand it over.

Pick by what the batch is:

- First review, mixed weight: "Morning <name>, here's today's PRs. They're in order of priority as some are a bit chunky."
- Re-review: "Morning <name>, these are back for a re-review with the comments addressed."
- Approve nudge: "<name> - these three have been reviewed and are just waiting on the approve click."
- A chain: "The <thing> chain is up, all CDT-NNN. In merge order - the hub one first since the rest pin to its release."

## Closing line patterns

One line, no recap, no questions-invitation:

- "Whenever you get a window."
- "No rush on any of them."
- "The first two are the ones blocking, rest can wait."
- Nothing at all, if the opening line already set expectations.

## Hard formatting rules

Teams is the target surface. It renders bullets, bold, links and emoji reliably;
tables, headings and code fences inconsistently. So: bullets and links only.
British English. No em dashes - ` - ` instead. No "just", no "feel free to", no
"happy to discuss", no "let me know if". Lowercase-friendly is fine in the
wrapper prose but the bullets read better sentence-cased.
