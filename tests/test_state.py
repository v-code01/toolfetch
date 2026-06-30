import json
from pathlib import Path

from vulcan.state import PHASES, State, advance, ledger_dir, load, log_event, save


def test_load_fresh(tmp_path: Path):
    s = load(tmp_path)
    assert s == State(None, "scout", "idle", 0)

def test_save_then_load_roundtrip(tmp_path: Path):
    s = State("0001-foo", "build", "running", 2)
    save(tmp_path, s)
    assert load(tmp_path) == s

def test_advance_walks_phases(tmp_path: Path):
    s = State("0001-foo", "scout", "running", 0)
    for expected in PHASES[1:]:
        s = advance(s)
        assert s.phase == expected

def test_advance_wraps_and_clears_project(tmp_path: Path):
    s = State("0001-foo", "ledger", "running", 3)
    s2 = advance(s)
    assert s2.phase == "scout" and s2.current_project is None and s2.attempt == 0

def test_log_event_appends_ndjson(tmp_path: Path):
    log_event(tmp_path, {"phase": "scout", "msg": "start"})
    log_event(tmp_path, {"phase": "triage", "msg": "pick"})
    lines = (tmp_path / "log.ndjson").read_text().strip().splitlines()
    assert len(lines) == 2 and json.loads(lines[1])["msg"] == "pick"

def test_ledger_dir_path(tmp_path: Path):
    assert ledger_dir(tmp_path, "0001-foo") == tmp_path / "ledger" / "0001-foo"

def test_load_recovers_from_garbage_state(tmp_path: Path):
    # M-4: a corrupt state.json recovers to fresh idle and logs the recovery.
    (tmp_path / "state.json").write_text("{not valid json")
    s = load(tmp_path)
    assert s == State(None, "scout", "idle", 0)
    log = (tmp_path / "log.ndjson").read_text()
    assert "state_recovery" in log

def test_load_recovers_from_missing_keys(tmp_path: Path):
    (tmp_path / "state.json").write_text('{"phase": "build"}')
    assert load(tmp_path) == State(None, "scout", "idle", 0)
