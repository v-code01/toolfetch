# Phase 5: Verify

**Skill:** `superpowers:verification-before-completion` plus the Anti-Vapor Gate.

**Do:** Build clean with zero warnings, run the full test suite green, run benchmarks that emit real numbers measured on this machine, and check any formal models. Run the C2 scan. Evidence is required, not assertions.

**Gate command:** `vulcan gate antivapor ledger/<project>/build` and `vulcan gate ledgebar ledger/<project>/build`. Both must exit 0 (C2 and C4).

**Proxy prompt:** "Per the charter, verify with evidence. Reject vapor harder than bugs. Every README claim must grep to code. Every benchmark baseline must be a real alternative on the same hardware and inputs. No strawman numbers, no tautological datasets."

**Done condition:** `vulcan gate antivapor` and `vulcan gate ledgebar` both pass (C2 and C4), with the evidence appended to `log.ndjson`.
