"""C3 gate: refuse any AI attribution in a repo's git history."""
from __future__ import annotations

import subprocess

AI_PATTERNS = (
    "claude",
    "anthropic",
    "co-authored-by",
    "generated with",
    "noreply@anthropic",
)

# A non-zero `git log` (empty/non-git repo, exit 128) means the history is
# unscannable. An unscannable repo is NOT clean: emit this sentinel so
# `is_clean` fails closed rather than crashing or passing silently.
_UNSCANNABLE = "<unscannable>"

# ASCII record/field separators keep multi-line commit bodies parseable.
# Committer identity (%cn/%ce) is scanned too: a clean author with a dirty
# committer (e.g. GIT_COMMITTER_* set to Claude) must still be caught.
_FMT = "%H%x00%an%x00%ae%x00%cn%x00%ce%x00%B%x1e"


def scan_history(repo: str) -> list[str]:
    """Return commit hashes whose author/committer identity or body match an
    AI-attribution pattern. On an unscannable repo, return a fail-closed
    sentinel so the gate aborts rather than passing open."""
    # --no-use-mailmap: a checked-in .mailmap must not relabel a dirty identity
    # into a clean one and slip past the gate.
    proc = subprocess.run(
        ["git", "-C", repo, "log", "--no-use-mailmap", f"--format={_FMT}"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return [_UNSCANNABLE]
    offenders: list[str] = []
    for record in proc.stdout.split("\x1e"):
        record = record.strip()
        if not record:
            continue
        fields = record.split("\x00")
        h, an, ae, cn, ce, body = (fields + ["", "", "", "", "", ""])[:6]
        haystack = f"{an}\n{ae}\n{cn}\n{ce}\n{body}".lower()
        if any(p in haystack for p in AI_PATTERNS):
            offenders.append(h)
    return offenders


def is_clean(repo: str) -> bool:
    return not scan_history(repo)
