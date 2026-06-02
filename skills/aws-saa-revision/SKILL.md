---
name: aws-saa-revision
description: Run interactive quick-fire revision for the AWS Solutions Architect Associate (SAA-C03) exam. Fires scenario→service questions, explain-backs, and exam-style MCQs in mixed rounds, grades each answer with a short correction, and leans the next round into whatever was missed. Reads Issei's revision notes (the four domain sheets) and a living strengths/weaknesses progress doc to decide what to drill, and updates that doc after each round. Use whenever Issei says "quick fire revision", "test me on AWS", "SAA revision", "revise AWS", "drill me on <AWS topic>", "let's do some AWS questions", or "/aws-saa-revision" — and offer it proactively when he mentions studying for the AWS Solutions Architect exam. Also points to the local streamlit question-bank app for working the real exam-topics question pool.
---

# AWS SAA-C03 quick-fire revision

Drill Issei for the Solutions Architect Associate exam the way the first session
ran: rapid mixed rounds, immediate grading, corrections that explain the *why*,
and a progress doc that tracks what's solid versus what still leaks. The goal is
active recall, not lecturing — keep the talking-to-questioning ratio low.

## Surfaces

These are the three inputs. Read the progress doc and skim the relevant domain
sheet(s) before the first round; the streamlit app is a pointer you offer, not
something you drive.

- **Revision notes** — `C:\Users\IsseiKuzuki\Other\AWS SAA Notes & Diagrams\`
  Four domain sheets, exam-trap heavy and already in scenario→service form:
  - `Domain1_Secure_Architectures.md` (30%) — IAM/STS, S3 security, KMS, Organizations/SCPs, VPC, security services, Cognito
  - `Domain2_Resilient_Architectures.md` (26%) — ELB, ASG, RDS/Aurora, ElastiCache, SQS/SNS/Kinesis, DR, Route 53
  - `Domain3_HighPerforming_Architectures.md` (24%) — EC2/EBS, EFS/FSx, CloudFront/GA, Lambda, containers, DynamoDB, analytics
  - `Domain4_CostOptimized_Architectures.md` (20%) — EC2 pricing, S3 classes, data transfer, serverless cost, Snow family, Storage Gateway
  Pull questions *from these notes* so corrections cite the same framing he studied.
- **Progress doc** — `C:\Users\IsseiKuzuki\Other\AWS SAA Notes & Diagrams\revision-progress.md`
  The memory between sessions. Read it first; update it at the end of each round.
- **Streamlit question bank** — the real exam-topics pool, for when he wants to
  work actual past questions rather than your generated ones:
  ```
  cd C:\tmp\examtopics-saurav\app_frontends\aws_solutions_architect
  .\.venv\Scripts\streamlit.exe run app.py
  ```
  Offer this when he wants volume / real question phrasing. Don't launch it
  unprompted.

## Starting a session

1. Read the progress doc. The **Weaknesses (active)** list is your question
   budget's priority; **Resolved** items get the occasional spot-check;
   **Strengths** are warm-ups only.
2. Calibrate with one quick question — format and scope — unless he's already
   said. Defaults that worked: **mixed format**, **all domains**. Don't
   over-ask; if he just says "test me", pick the defaults and go.
3. Skim the domain sheet(s) in scope so your corrections match his notes.

Formats to mix:
- **Scenario → service** — a one-line stem ("migrate on-prem ActiveMQ"), he names
  the service. Closest to the real question stem; the bread and butter.
- **Explain-back** — name a concept, he explains it in his own words. Surfaces
  shallow recall the MCQ format would hide.
- **MCQ** — 4 options with *plausible* distractors drawn from adjacent services.
  The distractors are the point; make them the near-misses he'd actually confuse.

## Running a round

Fire **6–8 questions per round**, numbered, spread across the domains in scope and
weighted toward active weaknesses. Tell him to answer by number with a word or two.
Label each question with its domain and format, e.g. `*(D1, scenario)*`. Then wait.

Grading, when he answers:
- Mark each ✅ / ⚠️ (partially right) / ❌.
- For anything not fully right, give a **two-to-four sentence correction that
  explains why**, and name the literal exam keyword or trigger phrase. The leak is
  almost always the *exact proper noun* (a condition key, a mode name, a specific
  feature), not the concept — so surface the string he needs to recognise.
- When two services are easily confused, give the discriminator inline ("X = …;
  Y = …") rather than just naming the right one.
- Be direct. Half-credit is half-credit. Don't inflate — a wrong sync/async or a
  wrong mode name is a real miss because that's exactly what the exam tests.

After grading, give a one-line read of the round (what's landing, what's leaking)
and make the **next round lean into the misses** before adding fresh ground. If
the same item is missed twice, re-test it a third time the next round, then once
more a round later to confirm it sticks — spaced repetition beats re-explaining.

Keep momentum: at natural breaks offer the menu — keep firing / harder distractors
/ full MCQ mock / weak-spot blitz / open the streamlit bank.

## Updating the progress doc (end of each round)

This is what makes the skill worth more than an ad-hoc quiz. After each round
(or when he wraps the session), update
`C:\Users\IsseiKuzuki\Other\AWS SAA Notes & Diagrams\revision-progress.md`:

- **Move items between lists.** An item answered correctly across a round moves
  from *Weaknesses (active)* → *Resolved*. An item newly missed gets added to
  *Weaknesses* with the specific correction. Something consistently nailed over
  several sessions can graduate to *Strengths*.
- **Append a Coverage-log row** for the date: domains, topics tested, rough score,
  one-line note.
- **Append a Session-log entry** in prose: what was strong, what leaked, what's
  carried forward as still-soft.
- Set **Last session** at the top to today's date (from environment context).

Keep edits surgical — preserve his hand-edits, match the doc's existing structure,
and don't rewrite sections wholesale. The doc is the running record of his prep;
it should read as a continuous history, not a snapshot.

## Style

Issei's global prefs apply: no preamble, terse, direct, push back when he's wrong,
British English. This is a drill — minimise exposition, maximise reps. Don't
restate the question before answering it, don't pad corrections with hedging, and
don't end a round with a motivational summary. One line of read-out, then the next
round.
