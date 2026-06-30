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

# ASCII record/field separators keep multi-line commit bodies parseable.
_FMT = "%H%x00%an%x00%ae%x00%B%x1e"


def scan_history(repo: str) -> list[str]:
    """Return commit hashes whose author, email, or body match an AI-attribution pattern."""
    out = subprocess.run(
        ["git", "-C", repo, "log", f"--format={_FMT}"],
        capture_output=True, text=True, check=True,
    ).stdout
    offenders: list[str] = []
    for record in out.split("\x1e"):
        record = record.strip()
        if not record:
            continue
        fields = record.split("\x00")
        h, an, ae, body = (fields + ["", "", "", ""])[:4]
        haystack = f"{an}\n{ae}\n{body}".lower()
        if any(p in haystack for p in AI_PATTERNS):
            offenders.append(h)
    return offenders


def is_clean(repo: str) -> bool:
    return not scan_history(repo)
