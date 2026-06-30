# Phase 2: Brainstorm

**Skill:** `superpowers:brainstorming`.

**Do:** Run the full brainstorming Q&A on the selected idea. The skill asks one question at a time. The Opus Proxy answers each as Vansh would, per the charter. The output is a design spec written to `ledger/<project>/spec.md`.

**Gate command:** none scriptable here; the gate is the Proxy's design approval.

**Proxy prompt:** "Per the charter, answer each brainstorming question as Vansh would. Keep the scope CPU-verifiable and no-mocks. Approve the design only when it can be built fully real on this hardware. Use Bader voice in the spec: no em-dashes, no self-bragging, no hedge phrases."

**Done condition:** the Proxy approves the design and `spec.md` is written.
