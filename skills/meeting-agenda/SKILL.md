---
name: meeting-agenda
description: Use when the user wants to draft a meeting invite agenda note, schedule a meeting, or write a calendar invite description. Also use when user says /meeting-agenda.
user-invocable: true
---

# Meeting Agenda Drafter

Draft a short, punchy meeting invite agenda note based on the user's input: $ARGUMENTS

If the user mentions a Jira ticket key (e.g. INTECH-1234), fetch the ticket details using the Atlassian MCP tools to understand the context, then draft the agenda from that context.

## Style Guide

- **Greeting:** "Hi all," or "Hey [name]," (use name only if the meeting is with a specific person)
- **Framing line:** One sentence explaining the purpose/context of the meeting
- **Topics:** A short bulleted list of discussion points — concise, conversational, phrased as questions or open topics (not actions or decisions)
- **Sign-off:** "Thanks,\nIssei"

## Tone

- Brief and to the point — no fluff
- Discussion-oriented, not prescriptive
- Casual but professional
- No emojis, no markdown formatting in the output — plain text suitable for pasting into a calendar invite

## Examples

Example 1:

Hi all,

A follow up to the session last week where we discussed CDT human review flows for FoDI NLP (FoDI Human Review Flow - Ideation)

Along with the data model, we now want to finalise a solution for DDT on the entity human in the loop flow:

What storage systems do we have
Do we have both a entity bank and cache?
What tech is used for these systems
How do analysts interact
Entity review process
What's in scope vs for CDT
How do we maximise automation while allowing analysts to add newly discovered entities
What can/can't analysts update
The monthly refresh process

Thanks,
Issei

Example 2:

Hi all!

As we're setting up configurations for FoDI NLP in the context of Danone and planning the engineering of the solution, it would be great to discuss how configuration files (entities/topics) and FoDI outputs fit into the DDT data model.

Some topics that would be useful to cover:
Consolidating entity bank for Search and Social
The potential impact of entity linkage on outputs and the data model

This is strictly in the context of DDT to allow us to build the first version of the NLP engine.

Thanks,
Issei

Example 3:

Hey James,

Some time to discuss developments in the AI-First plan:

Prioritise Figma
Consider some real user journeys for different user types (designer, business, techy)
Feed the above two bullet into the plan and rejig immediate next steps
+ how we prepare for the AI-first go-live

Thanks,
Issei

## Instructions

1. Understand the topic from the user's input (and Jira ticket if provided)
2. Draft ONE agenda note matching the style above
3. Output the plain text agenda only — no commentary, no preamble, no markdown code blocks
4. Keep it short — if it's more than ~15 lines, trim it down
