# Driver: the master loop

The Claude `/loop` driver runs this each wake. State lives on disk, not in context. Any restart resumes from `state.json` alone.

## Each wake

1. **Read state.** Run `vulcan status` and read `phase` and `current_project`.
2. **Run that phase's playbook.** Open `playbooks/NN-<phase>.md` for the current phase. Invoke its named superpowers skill with the Skill tool. Spawn the Opus Proxy with the Agent tool for every gate, seeding it with `charter.md`.
3. **Persist artifacts.** Write the phase output to `ledger/<project>/`. Append one event to `log.ndjson` with the phase, decision, and evidence.
4. **Advance.** Move the state machine one phase forward. When the phase was `finish`, run the publisher (attribution gate then `gh repo create --private` push) before advancing to `ledger`. The `ledger` phase wraps back to `scout` and clears `current_project`.
5. **Block or continue.** On a true block (missing secret, irreversible action), write `BLOCKED.md` with the exact unblock requirement and stop. Otherwise schedule the next wake.

## Routing rules (from spec §8)

- Idea needs a GPU or is unverifiable without mocks: disqualify and pick the next candidate. Not a halt.
- Build fails after 5 distinct approaches: shelve the project in `outcome.md`, pick the next candidate. Not a halt.
- Missing secret, key, or credential: halt. Write `BLOCKED.md`.
- Irreversible or catastrophic action required: halt and surface to a human.
- Anything else: route around it and keep building.
