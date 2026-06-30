# Phase 1: Triage and Select

**Skill:** Proxy decision (no superpowers skill). Uses `vulcan.scoring`.

**Do:** Build a `Candidate` for each idea and score it with `vulcan.scoring.score` on {novelty, adjacency, buildability, oss_value}. Set `needs_gpu` honestly. Call `vulcan.scoring.select` to pick the highest-scoring qualified candidate. Anything GPU-required is disqualified here by `disqualified` (C1). Write the winner and its rationale to `ledger/<NNNN-slug>/idea.md`.

**Gate command:** C1 is enforced in code by `vulcan.scoring.disqualified`; a GPU-required idea scores `-inf` and cannot win.

**Proxy prompt:** "Per the charter, score each candidate on novelty, ledge-adjacency, CPU-verifiability, one-cycle buildability, and OSS value. Disqualify anything that needs a GPU to be real. Pick one. Log the rationale. Prefer a narrow fully-real deliverable over a broad partly-simulated one."

**Done condition:** one qualified candidate selected, with `idea.md` holding the choice, the score, and the source links.
