# Vulcan — Autonomous Breakthrough → OSS Infra Factory

**Date:** 2026-06-30
**Status:** Design approved (autonomous mode — Opus Principal Proxy stands in for human gates)
**Author:** Vansh Verma

---

## 1. Mission

Continuously, with no human in the critical path:

1. **Scout** real breakthroughs from the **past 7 days** in systems / AI-infrastructure.
2. **Select** the single best, CPU-verifiable, ledge-adjacent idea.
3. **Build** it end-to-end at **ledge quality** — real implementation, no mocks, no vapor, real tests + property tests + formal models where warranted, benchmarks that emit real numbers measured on *this* machine.
4. **Ship** it as a **private** GitHub repo under `v-code01`, with a clean conventional-commit history and **zero AI attribution**.
5. **Loop.** One project at a time, in depth. Stop only when genuinely blocked.

This is not a code generator. It is a disciplined research-to-production engineer that happens to never get tired.

---

## 2. The Central Mechanism: Full Superpowers Flow, Opus Decider Substitutes for the Human

The superpowers workflow has human-approval gates by design (brainstorming design approval, plan review, code-review triage, finish decision). Vulcan **skips none of them**. Instead, every gate that normally waits on a human is routed to a dedicated **Opus "Principal Proxy" agent** seeded with the *Standards Charter* (§5).

- Brainstorming asks its questions one at a time → the Proxy answers each as Vansh would.
- writing-plans produces a plan → the Proxy reviews and approves/redlines it.
- requesting-code-review surfaces findings → the Proxy triages (receiving-code-review rigor: verify, don't rubber-stamp).
- finishing-a-development-branch presents options → the Proxy decides.

Full discipline, zero human bottleneck. The Proxy is **Opus** (user directive: "an opus agent makes the decision instead of me").

---

## 3. Hard Constraints (the guardrails that keep it REAL)

These are non-negotiable gates. Violating any one fails the project before publish.

### C1 — No-GPU / CPU-verifiable only
Any idea that requires a GPU, CUDA, or a discrete accelerator **to be real** is **disqualified at triage**. Rationale (proven by the nemesis audit): GPU infra with no GPU degenerates into a simulator with engineered numbers. The substrate is **Apple-Silicon CPU + unified memory**. AI-infra is in scope, but only its CPU-verifiable parts: schedulers, caches, memory/IO, content-addressed storage, consensus, runtimes, tokenizers, CPU quantization, RAG plumbing, coherence protocols, WALs, allocators.

### C2 — No mocks, no stubs, no vapor
A pre-publish **Anti-Vapor Gate** (§6, Phase 5) statically and dynamically enforces:
- No `todo!()`, `unimplemented!()`, `unreachable!()`-as-stub, `panic!("not implemented")`, or `bail!("not yet implemented")` in any critical path.
- No mock framework usage outside `#[cfg(test)]` / test modules.
- **No README/doc claim that grep cannot find in code.** (nemesis sin: "seqlock" existed only in prose; "Alibaba Cluster Trace" appeared nowhere in code.) Every named technique, dataset, or mechanism in the README must resolve to an implementing symbol.
- **No strawman benchmarks.** (nemesis sin: `17.17x` = `600/25` hardcoded constants.) Baselines must be a real, defensible alternative system or algorithm, run on the same hardware, same inputs.
- **No tautological datasets.** (nemesis sin: healthy≈0 vs failing-ramp-to-10 → trivially separable → F1=0.98 meaningless.) Any benchmark dataset must be adversarial or drawn from a real distribution, with the generation method documented and the separability honestly characterized.
- **No `#[cfg(feature)]` code paths claimed as "real" that never compile in CI.** Everything load-bearing compiles and runs in CI on this hardware.
- **No dangling references.** Every `docs/...` path referenced in README/source must exist. `docs/` is never empty-with-references.

### C3 — Zero AI attribution
- Build git identity = `Vansh Verma <vanshverma.code@gmail.com>`.
- No `Co-Authored-By`, no "Generated with", no "Claude", no "Anthropic", no `noreply` author anywhere.
- A pre-push **Attribution Gate** greps the entire history (`git log --format='%an|%ae|%B'` + trailers) and **aborts the push** on any hit. (All three audited repos pass this today; Vulcan must too, every time.)

### C4 — Ledge quality bar (calibrated from the three audits)
- Lint-clean at `-D warnings` (clippy for Rust; the project's native linter otherwise). **CI must be green on a fresh checkout** (phantom was docked for a red clippy gate — Vulcan verifies CI green before push).
- Typed errors (`thiserror`/`anyhow` boundary discipline). `unwrap()` only in tests or with a documented infallibility SAFETY note.
- `unsafe` only where justified, every block carrying a SAFETY rationale; prefer none.
- Real tests: unit + **property tests** for every untrusted-byte parser + integration/E2E against real clients + **TLA+ formal models** wherever consensus, concurrency, or a non-trivial state machine exists. CI gates the formal models too (ledge was docked for offline-only TLA+).
- Honest README **with a "Status & limitations" section** that survives contact with the code (the nemesis README was honest at the top level but not in specifics — Vulcan's must be honest *to the specifics*).
- Conventional commits, linear history, a real **LICENSE** file (nemesis shipped none).

---

## 4. Domain Scope

"Same field as ledge," refined by the user: **infra — systems & AI-infra — that does NOT need GPUs**, novel, derived from real recent breakthroughs.

In scope: content-addressed/versioned storage, Git internals, object stores, dedup/CoW, distributed consensus (Raft/Paxos/CRDT), WALs, lock-free data structures, schedulers, caches & coherence protocols, memory allocators, IO engines, tokenizers, CPU quantization/sparsity, RAG/agent-memory plumbing, serving control planes (CPU side), observability/tracing infra.

Out of scope: anything whose core value is GPU kernels, training throughput, or accelerator-bound numbers (would force C1 disqualification).

---

## 5. Standards Charter (seed for the Opus Principal Proxy)

The Proxy decides every gate by this charter:
- **Quality bar:** ledge (A) — the reference. Match its discipline.
- **Reject vapor harder than you reject bugs.** A working-but-overclaimed artifact (nemesis) is worse than an honest smaller one. Prefer a narrow, fully-real deliverable over a broad, partly-simulated one.
- **No-mocks is sacred.** If it can't be verified for real on this hardware, cut the claim or cut the feature.
- **Bader voice** for all prose: no em-dashes, no self-bragging, no hedge phrases; numbers do the bragging. (See [[feedback_bader_voice]].)
- **Zero AI attribution**, always. (See [[feedback_git_commits]].)
- **Honesty is a senior signal.** A "Status & limitations" section that names real gaps beats a flawless-sounding README.
- **Default to the recommended/strongest option and proceed** (see [[feedback_default_to_recommended]]); only halt for true blockers.

---

## 6. The Loop (one iteration = one shipped private repo)

Each phase invokes the named superpowers skill; the Proxy answers its gates.

| Phase | Skill | What happens | Gate |
|---|---|---|---|
| **0 · Scout** | `deep-research` / WebSearch fan-out | Sweep last 7 days: arXiv (cs.DC, cs.OS, cs.DB, cs.PF, cs.DS), Hacker News, lobste.rs, lab/eng blogs, GitHub trending. Emit N candidate ideas with source links. | ≥3 viable candidates or widen window |
| **1 · Triage & Select** | (Proxy decision) | Score each on {novelty, ledge-adjacency, **CPU-verifiability**, one-cycle buildability, OSS value}. Disqualify GPU-required/unverifiable. Proxy picks one, logs rationale. | C1 applied here |
| **2 · Brainstorm** | `superpowers:brainstorming` | Full Q&A; Proxy answers → design spec. | Design approved by Proxy |
| **3 · Plan** | `superpowers:writing-plans` | TDD task breakdown, file ownership, verification per task. | Plan reviewed by Proxy |
| **4 · Build** | `superpowers:executing-plans` + `test-driven-development` + `systematic-debugging` | Real code, red→green→refactor per task. 5-approaches rule before declaring blocked. | All tasks green |
| **5 · Verify** | `superpowers:verification-before-completion` + **Anti-Vapor Gate** | Clean build (zero warnings), tests green, benchmarks emit real numbers, formal models check, C2 scan passes. Evidence required, not assertions. | C2 + C4 pass |
| **6 · Review** | `superpowers:requesting-code-review` → `code-reviewer` agent → `receiving-code-review` | Multi-lens review; Proxy triages findings; fixes land; re-verify. | No unaddressed high-severity findings |
| **7 · Finish** | `superpowers:finishing-a-development-branch` + **Attribution Gate** | Conventional-commit history, LICENSE present, CI green, C3 scan passes, `gh repo create --private`, push. | C3 pass + push succeeds |
| **8 · Ledger & Loop** | (driver) | Append outcome to ledger, return to Phase 0. | — |

---

## 7. Continuity Engine — How It Never Stops (survives context compaction)

**The source of truth is on disk, not in context.** Context is disposable; the ledger is durable. Any compaction, crash, or restart resumes exactly where it left off.

```
~/vulcan/
  state.json                 # state machine: {current_project, phase, status, attempt_count}
  charter.md                 # Standards Charter (Proxy seed)
  ledger/
    <NNNN-slug>/
      idea.md                # selected breakthrough + source links + score
      spec.md                # Phase 2 output
      plan.md                # Phase 3 output
      build/                 # the actual project repo (becomes the published repo)
      review.md              # Phase 6 findings + resolutions
      outcome.md             # shipped | shelved | blocked + evidence
  research/
    <YYYY-WW>.md             # weekly scan + scoring table
  BLOCKED.md                 # written ONLY on a true halt, with exact unblock requirement
  log.ndjson                 # append-only event log (phase transitions, decisions, evidence)
```

**Driver model:** the main agent advances the state machine **one phase per step**, persists `state.json` + `log.ndjson` after each, then self-wakes (`/loop` self-paced, or `ScheduleWakeup`) to continue. The **Workflow** engine runs the parallel-heavy phases internally (Scout fan-out, multi-task Build, multi-lens Review). Reload-from-disk is always possible from `state.json` alone.

---

## 8. "Blocked" Semantics (only true stops halt the factory)

| Situation | Action |
|---|---|
| Idea needs a GPU / hardware to be real, or unverifiable without mocks | **Disqualify** idea, pick next (C1). Not a halt. |
| Build won't pass after **5 distinct approaches** (CLAUDE.md rule) | **Shelve** project with notes in `outcome.md`, pick next. Not a halt. |
| Needs a secret / API key / credential not available | **Halt.** Write `BLOCKED.md` with the exact requirement. |
| Requires an irreversible / catastrophic action (drop prod, force-push main) | **Halt** and surface to human (CLAUDE.md). |
| Anything else | Route around it and keep building. |

The factory is resilient by design: dead ideas are *routed around*, not fatal. A true halt is rare and always actionable.

---

## 9. Components (each independently testable)

1. **Scout** — research fan-out producing scored candidates. Input: date window + domain filter. Output: `research/<week>.md`. Dependency: WebSearch/deep-research, network.
2. **Selector** — Opus Proxy applying the scoring rubric + C1. Input: candidates. Output: `ledger/<id>/idea.md`. Pure decision.
3. **Builder** — the superpowers cycle (Phases 2–6) over the selected idea. Input: `idea.md`. Output: a verified `build/` repo. Dependency: cargo/toolchains, the named skills.
4. **Gates** — Anti-Vapor (C2), Attribution (C3), Ledge-bar (C4) as scriptable checks. Pure functions over the repo. Independently unit-testable with fixture repos.
5. **Publisher** — Attribution Gate → `gh repo create --private` → push. Input: verified repo. Output: private GitHub repo + `outcome.md`. Dependency: gh (authed as v-code01).
6. **Driver** — the on-disk state machine + self-wake loop tying it together. Input: `state.json`. Output: advanced state. Pure orchestration.

Each communicates through files in `~/vulcan/`, so each can be tested in isolation with a fixture directory.

---

## 10. Decisions Locked

- **Autonomy:** fully hands-off; Opus Proxy answers every superpowers gate.
- **Domain:** infra / systems & AI-infra, **no-GPU**, novel, ledge-adjacent.
- **Publish:** auto `gh repo create --private` under `v-code01` (already authed). No human gate.
- **Concurrency:** one project at a time, in depth.
- **Proxy & builder model:** Opus.
- **Framework home:** `~/vulcan` (working name; renameable).

---

## 11. Out of Scope (YAGNI)

- Multi-project parallelism (chose depth).
- Public publishing (private only; human flips later).
- A web UI / dashboard (the `log.ndjson` + ledger files are the interface).
- Self-modification of Vulcan's own code by the factory.
- Anything GPU-bound.
