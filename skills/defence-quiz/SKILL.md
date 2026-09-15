---
name: defence-quiz
description: Retrieval practice over Issei's defence cards (knowledge-vault/cards/) - the ten-line cards on the CDT mechanisms, decisions and fundamentals he should be able to defend out loud. Four modes. quiz (default) asks the three most-due cards one at a time with nothing shown, grades his answer against the card, writes confidence and next-due back, and appends what he missed. mock plays interviewer for twenty minutes over three system- or integration-level cards with follow-ups. own walks unreviewed cards so he rewrites the Claim and Why in his own words and flips reviewed_by_me. refresh checks pinned code against origin/main and marks moved cards stale. Use when Issei says "quiz me", "defence quiz", "cards", "test me on X", "mock interview", "let me own some cards", "which cards are stale", "/defence-quiz", or when morning-brief prompts it on a Tuesday or Thursday. Never shows the card before he answers; never inflates a mark. Distinct from aws-saa-revision (exam drilling from a fixed bank) and weekly-vault-review (read-only report).
user-invocable: true
---

# Defence quiz

Retrieval, not reading. Issei's failure mode is skimming a summary and feeling
he knows it. This skill only ever asks; it shows a card after he has answered,
never before. The grade is honest and specific, because an inflated
`whiteboard` pushes the card out ninety days and he meets the gap in an
interview instead.

Cards live in `C:\Users\IsseiKuzuki\Knowledge Base\knowledge-vault\cards\`.
The schema, the confidence marks and the scheduling rule are in that folder's
`README.md`; read it once per session. All frontmatter writes go through
`cards.py` in this skill's folder, never by hand.

```bash
python "C:\Users\IsseiKuzuki\Knowledge Base\issei-plugin\skills\defence-quiz\cards.py" due --n 3
```

The thin UI (`ui.py`, Streamlit) is for browsing, filtering, the heatmap, and
a self-quiz without Claude. It reads and writes the same files. It runs from a
venv beside it, because `uv run` under `Knowledge Base` resolves the wrong
project and the global Python has no Streamlit:

```bash
"C:\Users\IsseiKuzuki\Knowledge Base\issei-plugin\skills\defence-quiz\.venv\Scripts\python" -m streamlit run "C:\Users\IsseiKuzuki\Knowledge Base\issei-plugin\skills\defence-quiz\ui.py"
```

If the venv is missing: `uv venv --seed .venv` in that folder, then
`.venv\Scripts\python -m pip install --index-url https://pypi.org/simple streamlit pyyaml`
(the explicit index because pip is otherwise pointed at CodeArtifact).

## Modes

Pick from how he asked. Default is quiz.

**quiz.** "quiz me", "cards", "three cards", "/defence-quiz". Optional bias:
"quiz me on tenancy" is `--area multi-tenancy`, "high level ones" is
`--level system`, "my own code" is `--level mechanism`. Area names are the
`area:` values in the README's topic map.

**mock.** "mock interview", "interview me", "defend the platform". Twenty
minutes, three cards biased to `--level system` or `--level integration`,
run as a conversation not a quiz: ask the question, follow up from the card's
Trade-off line and from whatever he says, push once when an answer is vague.
Grade all three at the end, not after each.

**own.** "let me own some cards", "rewrite cards in my words", "review the
generated cards". `due --unreviewed --n 3`. For each: show the card in full,
ask him to restate the Claim and the Why in his own words in chat, and to
say whether the Rejected line is a real alternative or a straw man. Replace
those lines in the file with his wording (Edit tool), keep everything else,
then `set <id> reviewed_by_me=true`. If he says the card is wrong, fix it
from the sources it cites or, if the source is not to hand, `set <id>
stale=true` with a note and move on. This is the pass that does the learning;
never do it for him.

**refresh.** "which cards are stale", "refresh the cards". `refresh` compares
every pinned repo sha against main and flags cards whose Where paths moved.
Report the flagged cards with the files that changed. Re-verifying a stale
card is a human act: he reads the diff, decides whether the card still holds,
edits if not, and then `repin <id>`. Do not repin unprompted.

## Quiz process

1. `due` with the bias, `--n 3`. If nothing is due say so and offer `own` or
   a forced pick with `--only-overdue` off.
2. For each card in turn: print the `question` only. Nothing else, no hint,
   no area label. Wait for his answer. If he says "skip" or "I don't know",
   that is a `no`; show the card and move on.
3. Grade against the body. `whiteboard`: the Claim is right and the Why
   holds, and he named either the Rejected alternative or the Trade-off
   without prompting. `shaky`: the shape is right but the Why is thin or
   wrong, or he could not say what was rejected or what it costs. `no`:
   wrong mechanism, wrong direction, or nothing. Do not round up. A confident
   wrong answer is `no`.
4. Show the card, then in two or three sentences say what he had right and
   exactly what was missing or wrong. Be specific: "you said the row policy
   filters on the JWT; it filters on the session setting the composer sets
   from the JWT, which is why the superuser is exempt." Not "close".
5. `record <id> --mark <mark> --miss "<one line>"`. The miss line is what
   goes under Misses on the card; write it as the thing to remember, not a
   grade.
6. After three, one line: marks, and the one area that looks weakest across
   recent sessions if `stats` shows it.

## Rules

- Never show a card before he has answered or explicitly given up.
- Never accept "yeah I know this one" as an answer. Ask for the three
  sentences.
- One card at a time. No batch of questions.
- If he disputes a grade with a reason, hear it, check the card's sources if
  needed, and change the mark only if the card was wrong. Then fix the card.
- Time-box. Quiz is fifteen minutes, mock is twenty. Say when it is up.
- Do not read the pattern or decision note behind a card during the quiz;
  the card is the bar. The note is for `own` mode and for fixing cards.
- Tuesday and Thursday mornings are the default cadence via `morning-brief`;
  any other time he asks is fine. Never suggest Friday afternoon.
- British English, terse. No praise inflation; a `whiteboard` is stated
  flatly.

## Scheduling arithmetic (for reference; the script owns it)

`whiteboard` doubles `interval_days` (minimum two, cap ninety). `shaky`
halves it (minimum one). `no` resets it to one. `next_due` is today plus the
interval. `due` orders by `next_due` then by fewest times tested, so new
cards surface early and mastered cards drift out to months.

## Scope

This skill asks and grades. It does not generate cards (that is the fan-out
described in `cards/README.md`), does not run the weekly review, and does not
touch any vault file outside `cards/`.
