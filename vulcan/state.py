"""Durable on-disk state machine for the Vulcan driver.

The driver advances one phase per step and persists after each, so any
context loss or restart resumes from `state.json` alone.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

PHASES = ["scout", "triage", "brainstorm", "plan", "build", "verify", "review", "finish", "ledger"]


@dataclass
class State:
    current_project: str | None
    phase: str
    status: str
    attempt: int


def _state_path(home: Path) -> Path:
    return home / "state.json"


def load(home: Path) -> State:
    """Load state, or a fresh idle state at the scout phase if none exists."""
    p = _state_path(home)
    if not p.exists():
        return State(None, "scout", "idle", 0)
    d = json.loads(p.read_text())
    return State(d["current_project"], d["phase"], d["status"], d["attempt"])


def save(home: Path, state: State) -> None:
    """Persist state atomically (write-temp-then-rename)."""
    home.mkdir(parents=True, exist_ok=True)
    tmp = _state_path(home).with_suffix(".json.tmp")
    tmp.write_text(json.dumps(asdict(state), indent=2))
    tmp.replace(_state_path(home))


def advance(state: State) -> State:
    """Return the next phase. `ledger` wraps to `scout`, clearing the project."""
    idx = PHASES.index(state.phase)
    if PHASES[idx] == "ledger":
        return State(None, "scout", "idle", 0)
    return State(state.current_project, PHASES[idx + 1], "running", state.attempt)


def log_event(home: Path, event: dict) -> None:
    """Append one JSON line to the durable event log."""
    home.mkdir(parents=True, exist_ok=True)
    with (home / "log.ndjson").open("a") as f:
        f.write(json.dumps(event) + "\n")


def ledger_dir(home: Path, project: str) -> Path:
    return home / "ledger" / project
