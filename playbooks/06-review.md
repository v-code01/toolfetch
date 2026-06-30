# Phase 6: Review

**Skill:** `superpowers:requesting-code-review` to a `code-reviewer` agent, then `superpowers:receiving-code-review`.

**Do:** Run a multi-lens review of the build. Spawn the `code-reviewer` agent to surface findings. The Opus Proxy triages each finding with receiving-code-review rigor: verify, do not rubber-stamp. Land the fixes, then re-run Phase 5 verification. Write findings and resolutions to `ledger/<project>/review.md`.

**Gate command:** re-run `vulcan gate antivapor ledger/<project>/build` and `vulcan gate ledgebar ledger/<project>/build` after fixes land.

**Proxy prompt:** "Per the charter, triage each review finding as Vansh would. Verify the claim before acting on it. Do not perform agreement. Address every high-severity finding before this phase can close."

**Done condition:** no unaddressed high-severity findings, fixes verified, `review.md` written.
