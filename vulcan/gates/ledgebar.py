"""C4 gate: enforce the ledge quality bar — lint-clean, tests-green, LICENSE present."""
from __future__ import annotations

import subprocess
from pathlib import Path

_CMDS = {
    "rust": {
        "lint": ["cargo", "clippy", "--all-targets", "--all-features", "--", "-D", "warnings"],
        "test": ["cargo", "test", "--workspace"],
    },
    "python": {
        "lint": ["ruff", "check", "."],
        "test": ["pytest", "-q"],
    },
}


def detect_kind(repo: str) -> str:
    root = Path(repo)
    if (root / "Cargo.toml").exists():
        return "rust"
    if (root / "pyproject.toml").exists():
        return "python"
    return "unknown"


def has_license(repo: str) -> bool:
    return any((Path(repo) / name).exists() for name in ("LICENSE", "LICENSE.md", "LICENSE.txt"))


def _run_ok(run, cmd: list[str], repo: str) -> bool:
    """Run a quality command, treating any failure-to-run as a failure (fail
    closed). A missing toolchain (cargo/ruff/pytest absent) is NOT a pass."""
    try:
        return run(cmd, cwd=repo, capture_output=True, text=True).returncode == 0
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return False


def check(repo: str, run=subprocess.run) -> dict:
    kind = detect_kind(repo)
    commands: list[str] = []
    lint_ok = tests_ok = False
    if kind in _CMDS:
        lint = _CMDS[kind]["lint"]
        test = _CMDS[kind]["test"]
        commands += [" ".join(lint), " ".join(test)]
        lint_ok = _run_ok(run, lint, repo)
        tests_ok = _run_ok(run, test, repo)
    return {
        "kind": kind,
        "license": has_license(repo),
        "lint_ok": lint_ok,
        "tests_ok": tests_ok,
        "commands": commands,
    }


def passes(result: dict) -> bool:
    return bool(result["license"] and result["lint_ok"] and result["tests_ok"])
