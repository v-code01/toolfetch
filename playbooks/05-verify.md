# Phase 5: Verify

**Skill:** `superpowers:verification-before-completion` plus the Anti-Vapor Gate.

**Do:** Build clean with zero warnings, run the full test suite green, run benchmarks that emit real numbers measured on this machine, and check any formal models. Run the C2 scan. Evidence is required, not assertions.

**Gate command:** `vulcan gate antivapor ledger/<project>/build` and `vulcan gate ledgebar ledger/<project>/build`. Both must exit 0 (C2 and C4).

**Proxy prompt:** "Per the charter, verify with evidence. Reject vapor harder than bugs. Every README claim must grep to code. Every benchmark baseline must be a real alternative on the same hardware and inputs. No strawman numbers, no tautological datasets."

**Done condition:** `vulcan gate antivapor` and `vulcan gate ledgebar` both pass (C2 and C4), with the evidence appended to `log.ndjson`.

**Proxy-adjudicated C2 clauses (NOT mechanized by the gate):** The anti-vapor gate mechanizes stub/mock/dangling-ref/unbacked-claim detection, but two C2 clauses are genuinely dynamic and grep cannot decide them. The Opus Proxy MUST manually adjudicate both here, in addition to the gate exit codes:

- **Strawman benchmarks.** Confirm every benchmark baseline is a real, defensible alternative system or algorithm, run on *this* hardware with the *same* inputs — not a hardcoded constant. (Nemesis sin: `17.17x == 600/25`.) If the baseline is not a real competitor, reject.
- **Tautological datasets.** Confirm any benchmark dataset is adversarial or drawn from a real distribution, with the generation method documented and separability honestly characterized — not trivially separable. (Nemesis sin: healthy≈0 vs failing-ramp-to-10 → meaningless F1=0.98.) If separability is trivial, reject.

This delegation is a stated decision: `vulcan/gates/antivapor.py` documents the same boundary in its module docstring. A green gate is necessary but not sufficient; these two judgements are required before declaring verify done.
