# Phase 0: Scout

**Skill:** `deep-research` (WebSearch fan-out).

**Do:** Sweep the last 7 days for systems and AI-infra breakthroughs. Cover arXiv (cs.DC, cs.OS, cs.DB, cs.PF, cs.DS), Hacker News, lobste.rs, lab and engineering blogs, and GitHub trending. Use `vulcan.scout.SOURCES` for the channel list and `arxiv_query` for the arXiv window. Dedupe titles with `vulcan.scout.dedupe`. Emit candidate ideas with source links to `research/<YYYY-WW>.md`.

**Gate command:** none (this phase produces candidates, it does not score them). The next phase applies C1.

**Proxy prompt:** "Per the charter, is this set of candidates strong enough to proceed? Each must be CPU-verifiable and ledge-adjacent. If fewer than 3 viable candidates surface, widen the window and rescan."

**Done condition:** at least 3 viable candidates written to `research/<YYYY-WW>.md`, or the window has been widened and the rescan recorded.
