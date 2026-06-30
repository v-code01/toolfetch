"""Publisher: the C3 attribution gate, then a private GitHub push under v-code01."""
from __future__ import annotations

import subprocess

from vulcan.gates import attribution

OWNER = "v-code01"


class VaporError(Exception):
    """Raised when a repo fails a publish gate (e.g. AI attribution present)."""


def publish(repo: str, name: str, description: str,
            run=subprocess.run, clean=attribution.is_clean) -> str:
    """Gate on attribution, then create a private repo and push. Returns the URL."""
    if not clean(repo):
        raise VaporError(f"AI attribution found in {repo} history — refusing to publish")
    run(
        ["gh", "repo", "create", f"{OWNER}/{name}", "--private",
         "--source", repo, "--description", description, "--push", "--remote", "origin"],
        check=True, capture_output=True, text=True,
    )
    return f"https://github.com/{OWNER}/{name}"
