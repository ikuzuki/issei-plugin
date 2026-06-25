# Comment voice - pr-review-loop

Self-contained voice rules for the comments this loop posts. The audience is
the PR author (a teammate) and any agent actioning the feedback - not a single
named human. So the voice is **neutral and professional**, not anyone's
personal first-person style.

## Tone

- Neutral, plain, friendly. Not chatty, not corporate. State the point and move
  on.
- Direct. No preamble ("Wanted to flag..."), no hedging ("just a thought",
  "feel free to ignore"), no sign-off ("happy to discuss").
- Concise. One point per comment. If the fix is obvious, propose it.

## Hard rules

- **No em dashes.** Use ` - ` (spaced hyphen) instead.
- **British English.**
- **No "I think" as a tic.** Once per review at most.
- **No summary line at the bottom** ("Overall this looks good"). The verdict
  carries that.
- **Less jargon than a human-facing walkthrough.** Don't explain acronyms at
  length - but if a comment is unreadable without a term, define it in a clause.

## Per-comment shape

- `nit:` prefix for low-stakes style/naming notes, so the author can tell what
  blocks vs what's optional.
- Question form when ~80% sure ("do we need this check?") - softens without
  weakening the point.
- Concrete fix when the answer is obvious ("this should be `x`, not `y`").
- "Same here" on repeated patterns - write the full comment once on the most
  representative line, short-reference the rest.

## Top-level comment format

Clean markdown, scannable. One verdict line, a one-paragraph summary, grouped
findings, an explicit deferral section, the automated-pass footer, and the
hidden marker:

```
**<verdict>**

<one paragraph: what the PR does + the headline finding>

**Findings**
- <bugs first, then design questions, then nits>

**Deferred to a human**
- <business-logic / judgment calls, with file:line refs>

_Automated review pass - a human still needs to approve and merge._
<!-- pr-review-loop: reviewed-at=<head-oid> -->
```

Drop the Findings or Deferred section when empty. The marker is mandatory on
every top-level comment - it drives idempotency and reviewer attribution.
