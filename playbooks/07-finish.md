# Phase 7: Finish

**Skill:** `superpowers:finishing-a-development-branch` plus the Attribution Gate.

**Do:** Confirm a conventional-commit linear history, a real LICENSE file, and green CI on a fresh checkout. Run the C3 attribution scan over the whole history. Then publish with `vulcan.publisher.publish`, which gates on attribution and runs `gh repo create v-code01/<name> --private --source <repo> --push`. Write the result to `ledger/<project>/outcome.md`.

**Gate command:** `vulcan gate attribution ledger/<project>/build` must exit 0 (C3) before publish. The publisher re-checks attribution and raises `VaporError` on any hit.

**Proxy prompt:** "Per the charter, decide the finish as Vansh would. Zero AI attribution anywhere in the history. LICENSE present. CI green on a fresh checkout. Publish private under v-code01 only when all three hold."

**Done condition:** `vulcan gate attribution` passes (C3), the private repo is created and pushed, and `outcome.md` records the URL.
