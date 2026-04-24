---
description: Hybrid-search the personal knowledge vault via knowledge-mcp.
---

Run `mcp__knowledge__search` with the user's query, `mode="hybrid"`, `limit=5`.

Format each hit as:

- **{path}** — {heading_path joined by " › "} (score {score:.2f})
  > {first ~200 chars of content}

If no hits, say so plainly. Do not fabricate results.

Query: $ARGUMENTS
