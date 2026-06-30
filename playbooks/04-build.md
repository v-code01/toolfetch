# Phase 4: Build

**Skill:** `superpowers:executing-plans` with `superpowers:test-driven-development` and `superpowers:systematic-debugging`.

**Do:** Execute the plan task by task. For each task write the failing test, confirm it fails, write the minimal implementation, confirm it passes, then commit. Real code only, red to green to refactor. Apply the 5-approaches rule before declaring any task blocked. The project repo lives at `ledger/<project>/build/`.

**Gate command:** `vulcan gate antivapor ledger/<project>/build` as a running check that no stubs creep in.

**Proxy prompt:** "Per the charter, hold the build to no-mocks and no-stubs. If a task cannot be made real after 5 distinct approaches, shelve it with notes. Do not let a stub stand in for an implementation."

**Done condition:** all plan tasks are green and committed with a clean conventional-commit history.
