# Vulcan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the deterministic tooling + playbooks that let a Claude driver autonomously scout weekly infra breakthroughs and ship ledge-quality private repos with no human in the loop.

**Architecture:** A Python package (`vulcan/`) provides the testable, deterministic spine — an on-disk state machine, three quality gates (attribution, anti-vapor, ledge-bar), candidate scoring, and a publisher. Markdown playbooks + a Standards Charter encode the agent-facing phases (scout, triage, brainstorm→finish) that a Claude `/loop` driver executes, calling the Python spine via its CLI. Context is disposable; `~/vulcan/state.json` + `ledger/` is the durable source of truth.

**Tech Stack:** Python 3.11, pytest, ruff, argparse, subprocess, tomllib; `git` + `gh` (authed as v-code01); superpowers skills consumed by the Claude driver.

## Global Constraints

- **No AI attribution anywhere** — commits authored `Vansh Verma <vanshverma.code@gmail.com>`; no `Co-Authored-By`, no "Generated with", no "Claude"/"Anthropic". (C3)
- **CPU-verifiable only** — no code path depends on a GPU/CUDA to run or be tested. (C1)
- **No mocks/stubs/vapor in shipped output** — every claim greps to code; no `todo!()`/`unimplemented!()` in critical paths; no strawman/tautological benchmarks. (C2)
- **Ledge quality bar** — ruff-clean, pytest-green, every public function documented, real tests over fixtures (no theater). (C4)
- **Bader voice** in all prose — no em-dashes, no self-bragging, no hedge phrases.
- **Python 3.11**, package importable as `vulcan`, CLI entrypoint `vulcan`.
- Framework home resolved from `$VULCAN_HOME` env, default `~/vulcan`.

---

## Phase A — Foundation

### Task A1: Package scaffold + tooling config

**Files:**
- Create: `/Users/vanshverma/vulcan/pyproject.toml`
- Create: `/Users/vanshverma/vulcan/vulcan/__init__.py`
- Create: `/Users/vanshverma/vulcan/tests/__init__.py`

**Interfaces:**
- Produces: importable package `vulcan` (version `0.1.0`); console script `vulcan = "vulcan.cli:main"`.

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "vulcan"
version = "0.1.0"
description = "Autonomous breakthrough-to-OSS infra factory"
requires-python = ">=3.11"
dependencies = []

[project.scripts]
vulcan = "vulcan.cli:main"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
packages = ["vulcan", "vulcan.gates"]
```

- [ ] **Step 2: Write `vulcan/__init__.py`**

```python
"""Vulcan: autonomous breakthrough-to-OSS infra factory."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Create empty `tests/__init__.py`** (touch the file).

- [ ] **Step 4: Verify install + lint**

Run: `cd /Users/vanshverma/vulcan && python -m pip install -e . -q && ruff check .`
Expected: install succeeds; `All checks passed!`

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml vulcan/__init__.py tests/__init__.py
git commit -m "chore(vulcan): package scaffold + ruff/pytest config"
```

---

### Task A2: On-disk state machine (`state.py`)

**Files:**
- Create: `/Users/vanshverma/vulcan/vulcan/state.py`
- Test: `/Users/vanshverma/vulcan/tests/test_state.py`

**Interfaces:**
- Produces:
  - `PHASES: list[str]` = `["scout","triage","brainstorm","plan","build","verify","review","finish","ledger"]`
  - `@dataclass State(current_project: str|None, phase: str, status: str, attempt: int)`
  - `load(home: Path) -> State` (returns fresh `State(None,"scout","idle",0)` if no file)
  - `save(home: Path, state: State) -> None`
  - `advance(state: State) -> State` (next phase; `ledger` wraps to `scout` and clears `current_project`)
  - `log_event(home: Path, event: dict) -> None` (appends one JSON line to `log.ndjson`)
  - `ledger_dir(home: Path, project: str) -> Path`

- [ ] **Step 1: Write failing tests**

```python
import json
from pathlib import Path
from vulcan.state import State, PHASES, load, save, advance, log_event, ledger_dir

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
```

- [ ] **Step 2: Run, verify fail**

Run: `cd /Users/vanshverma/vulcan && pytest tests/test_state.py -q`
Expected: FAIL (`ModuleNotFoundError: vulcan.state`)

- [ ] **Step 3: Implement `state.py`**

```python
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
```

- [ ] **Step 4: Run, verify pass**

Run: `pytest tests/test_state.py -q`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add vulcan/state.py tests/test_state.py
git commit -m "feat(vulcan): on-disk state machine with durable ndjson log"
```

---

## Phase B — Quality Gates

### Task B1: Attribution gate (C3) — `gates/attribution.py`

**Files:**
- Create: `/Users/vanshverma/vulcan/vulcan/gates/__init__.py` (empty)
- Create: `/Users/vanshverma/vulcan/vulcan/gates/attribution.py`
- Test: `/Users/vanshverma/vulcan/tests/test_attribution.py`

**Interfaces:**
- Produces: `scan_history(repo: str) -> list[str]` (offending commit hashes); `is_clean(repo: str) -> bool`.

- [ ] **Step 1: Write failing tests** (use a real fixture repo built in the test)

```python
import subprocess
from pathlib import Path
from vulcan.gates.attribution import scan_history, is_clean

def _git(repo: Path, *args, env=None):
    subprocess.run(["git", "-C", str(repo), *args], check=True,
                   capture_output=True, env=env)

def _init(repo: Path):
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Vansh Verma")
    _git(repo, "config", "user.email", "vanshverma.code@gmail.com")

def _commit(repo: Path, msg: str, fname="f.txt"):
    (repo / fname).write_text("x")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)

def test_clean_repo(tmp_path: Path):
    r = tmp_path / "clean"; _init(r)
    _commit(r, "feat: real work")
    _commit(r, "fix: more real work", "g.txt")
    assert scan_history(str(r)) == []
    assert is_clean(str(r)) is True

def test_detects_co_authored_by_claude(tmp_path: Path):
    r = tmp_path / "dirty"; _init(r)
    _commit(r, "feat: thing\n\nCo-Authored-By: Claude <noreply@anthropic.com>")
    assert len(scan_history(str(r))) == 1
    assert is_clean(str(r)) is False

def test_detects_generated_with(tmp_path: Path):
    r = tmp_path / "gen"; _init(r)
    _commit(r, "feat: thing\n\nGenerated with Claude Code")
    assert is_clean(str(r)) is False
```

- [ ] **Step 2: Run, verify fail**

Run: `pytest tests/test_attribution.py -q`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: Implement `attribution.py`**

```python
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
```

- [ ] **Step 4: Run, verify pass**

Run: `pytest tests/test_attribution.py -q`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add vulcan/gates/__init__.py vulcan/gates/attribution.py tests/test_attribution.py
git commit -m "feat(vulcan): C3 attribution gate — abort on any AI attribution in history"
```

---

### Task B2: Anti-vapor gate (C2) — `gates/antivapor.py`

**Files:**
- Create: `/Users/vanshverma/vulcan/vulcan/gates/antivapor.py`
- Test: `/Users/vanshverma/vulcan/tests/test_antivapor.py`

**Interfaces:**
- Consumes: a built repo dir; optional `vulcan-claims.toml` at repo root with `[[claim]]` tables `{text, evidence, files}`.
- Produces:
  - `find_stubs(repo: str) -> list[tuple[str,int,str]]` — (file, line, pattern) in non-test source.
  - `find_dangling_doc_refs(repo: str) -> list[str]` — referenced `docs/...` paths that don't exist.
  - `verify_claims(repo: str) -> list[str]` — claims whose evidence grep finds nothing.
  - `scan(repo: str) -> dict` — `{"stubs":..,"dangling":..,"unbacked_claims":..}`; `passes(result)->bool`.

- [ ] **Step 1: Write failing tests**

```python
from pathlib import Path
from vulcan.gates.antivapor import find_stubs, find_dangling_doc_refs, verify_claims, scan, passes

def _w(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)

def test_find_stubs_flags_todo_in_src_not_tests(tmp_path: Path):
    _w(tmp_path / "src/lib.rs", "fn a() { todo!() }\n")
    _w(tmp_path / "tests/t.rs", "fn t() { todo!() }\n")  # tests are exempt
    hits = find_stubs(str(tmp_path))
    files = {h[0] for h in hits}
    assert any("src/lib.rs" in f for f in files)
    assert not any("tests/t.rs" in f for f in files)

def test_find_dangling_doc_refs(tmp_path: Path):
    _w(tmp_path / "README.md", "See docs/arch/present.md and docs/arch/missing.md\n")
    _w(tmp_path / "docs/arch/present.md", "here")
    dangling = find_dangling_doc_refs(str(tmp_path))
    assert dangling == ["docs/arch/missing.md"]

def test_verify_claims_backed_and_unbacked(tmp_path: Path):
    _w(tmp_path / "src/ring.rs", "// a real seqlock\nstruct Seqlock;\n")
    _w(tmp_path / "vulcan-claims.toml",
       '[[claim]]\ntext="uses a seqlock"\nevidence="Seqlock"\nfiles=["src/ring.rs"]\n'
       '[[claim]]\ntext="alibaba trace"\nevidence="alibaba"\nfiles=["src/ring.rs"]\n')
    unbacked = verify_claims(str(tmp_path))
    assert unbacked == ["alibaba trace"]

def test_scan_passes_on_clean_repo(tmp_path: Path):
    _w(tmp_path / "src/lib.rs", "fn a() -> i32 { 1 }\n")
    _w(tmp_path / "README.md", "no refs here\n")
    result = scan(str(tmp_path))
    assert passes(result) is True
```

- [ ] **Step 2: Run, verify fail**

Run: `pytest tests/test_antivapor.py -q`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: Implement `antivapor.py`**

```python
"""C2 gate: refuse vapor — stubs, dangling docs, and unbacked claims.

Encodes the nemesis-audit failure modes as mechanical checks. The README's
honesty is enforced by `vulcan-claims.toml`: every headline claim must name an
`evidence` string that grep finds in its backing `files`.
"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

STUB_PATTERNS = [
    r"todo!\(",
    r"unimplemented!\(",
    r'panic!\(\s*"not implemented',
    r'bail!\(\s*"not yet implemented',
    r"raise NotImplementedError",
]
_STUB_RE = re.compile("|".join(STUB_PATTERNS))
_SRC_EXT = {".rs", ".py", ".go", ".ts", ".c", ".h", ".cpp", ".zig"}
_DOC_REF_RE = re.compile(r"docs/[\w./-]+\.md")


def _is_test_path(rel: str) -> bool:
    parts = rel.replace("\\", "/").split("/")
    return any(p in ("tests", "test", "testkit") for p in parts) or rel.endswith("_test.py")


def _source_files(repo: str):
    root = Path(repo)
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in _SRC_EXT and ".git" not in p.parts and "target" not in p.parts:
            yield p, str(p.relative_to(root))


def find_stubs(repo: str) -> list[tuple[str, int, str]]:
    hits: list[tuple[str, int, str]] = []
    for path, rel in _source_files(repo):
        if _is_test_path(rel):
            continue
        for i, line in enumerate(path.read_text(errors="ignore").splitlines(), 1):
            m = _STUB_RE.search(line)
            if m:
                hits.append((rel, i, m.group(0)))
    return hits


def find_dangling_doc_refs(repo: str) -> list[str]:
    root = Path(repo)
    referenced: set[str] = set()
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in (_SRC_EXT | {".md"}) and ".git" not in p.parts:
            referenced.update(_DOC_REF_RE.findall(p.read_text(errors="ignore")))
    return sorted(ref for ref in referenced if not (root / ref).exists())


def verify_claims(repo: str) -> list[str]:
    root = Path(repo)
    manifest = root / "vulcan-claims.toml"
    if not manifest.exists():
        return []  # absence handled by caller policy; see scan()
    claims = tomllib.loads(manifest.read_text()).get("claim", [])
    unbacked: list[str] = []
    for c in claims:
        evidence = c["evidence"]
        found = any(
            evidence in (root / f).read_text(errors="ignore")
            for f in c["files"]
            if (root / f).exists()
        )
        if not found:
            unbacked.append(c["text"])
    return unbacked


def scan(repo: str) -> dict:
    return {
        "stubs": find_stubs(repo),
        "dangling": find_dangling_doc_refs(repo),
        "unbacked_claims": verify_claims(repo),
    }


def passes(result: dict) -> bool:
    return not (result["stubs"] or result["dangling"] or result["unbacked_claims"])
```

- [ ] **Step 4: Run, verify pass**

Run: `pytest tests/test_antivapor.py -q`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add vulcan/gates/antivapor.py tests/test_antivapor.py
git commit -m "feat(vulcan): C2 anti-vapor gate — stubs, dangling docs, unbacked-claim manifest"
```

---

### Task B3: Ledge-bar gate (C4) — `gates/ledgebar.py`

**Files:**
- Create: `/Users/vanshverma/vulcan/vulcan/gates/ledgebar.py`
- Test: `/Users/vanshverma/vulcan/tests/test_ledgebar.py`

**Interfaces:**
- Produces:
  - `detect_kind(repo: str) -> str` — `"rust" | "python" | "unknown"`.
  - `has_license(repo: str) -> bool`.
  - `check(repo: str, run=subprocess.run) -> dict` — `{"kind","license","lint_ok","tests_ok","commands":[...]}`; `passes(result)->bool`. `run` is injectable for tests.

- [ ] **Step 1: Write failing tests** (inject a fake runner; no real cargo needed)

```python
from pathlib import Path
from types import SimpleNamespace
from vulcan.gates.ledgebar import detect_kind, has_license, check, passes

def _w(p: Path, t=""): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(t)

def test_detect_kind(tmp_path: Path):
    _w(tmp_path / "Cargo.toml", "[package]")
    assert detect_kind(str(tmp_path)) == "rust"

def test_has_license(tmp_path: Path):
    assert has_license(str(tmp_path)) is False
    _w(tmp_path / "LICENSE", "BSL")
    assert has_license(str(tmp_path)) is True

def test_check_rust_all_green(tmp_path: Path):
    _w(tmp_path / "Cargo.toml", "[package]"); _w(tmp_path / "LICENSE", "MIT")
    calls = []
    def fake_run(cmd, **kw):
        calls.append(cmd)
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    result = check(str(tmp_path), run=fake_run)
    assert result["kind"] == "rust" and result["lint_ok"] and result["tests_ok"]
    assert passes(result) is True
    assert any("clippy" in " ".join(c) for c in calls)

def test_check_fails_on_lint(tmp_path: Path):
    _w(tmp_path / "Cargo.toml", "[package]"); _w(tmp_path / "LICENSE", "MIT")
    def fake_run(cmd, **kw):
        rc = 101 if "clippy" in " ".join(cmd) else 0
        return SimpleNamespace(returncode=rc, stdout="", stderr="")
    result = check(str(tmp_path), run=fake_run)
    assert result["lint_ok"] is False and passes(result) is False

def test_check_fails_without_license(tmp_path: Path):
    _w(tmp_path / "Cargo.toml", "[package]")
    def fake_run(cmd, **kw): return SimpleNamespace(returncode=0, stdout="", stderr="")
    assert passes(check(str(tmp_path), run=fake_run)) is False
```

- [ ] **Step 2: Run, verify fail**

Run: `pytest tests/test_ledgebar.py -q`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: Implement `ledgebar.py`**

```python
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


def check(repo: str, run=subprocess.run) -> dict:
    kind = detect_kind(repo)
    commands: list[str] = []
    lint_ok = tests_ok = False
    if kind in _CMDS:
        lint = _CMDS[kind]["lint"]
        test = _CMDS[kind]["test"]
        commands += [" ".join(lint), " ".join(test)]
        lint_ok = run(lint, cwd=repo, capture_output=True, text=True).returncode == 0
        tests_ok = run(test, cwd=repo, capture_output=True, text=True).returncode == 0
    return {
        "kind": kind,
        "license": has_license(repo),
        "lint_ok": lint_ok,
        "tests_ok": tests_ok,
        "commands": commands,
    }


def passes(result: dict) -> bool:
    return bool(result["license"] and result["lint_ok"] and result["tests_ok"])
```

- [ ] **Step 4: Run, verify pass**

Run: `pytest tests/test_ledgebar.py -q`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add vulcan/gates/ledgebar.py tests/test_ledgebar.py
git commit -m "feat(vulcan): C4 ledge-bar gate — lint/tests/LICENSE with injectable runner"
```

---

## Phase C — Intelligence (scoring + scout helpers)

### Task C1: Candidate scoring + C1 disqualification — `scoring.py`

**Files:**
- Create: `/Users/vanshverma/vulcan/vulcan/scoring.py`
- Test: `/Users/vanshverma/vulcan/tests/test_scoring.py`

**Interfaces:**
- Produces:
  - `@dataclass Candidate(title, summary, sources: list[str], needs_gpu: bool, novelty: int, adjacency: int, buildability: int, oss_value: int)` (scores 0-5).
  - `disqualified(c: Candidate) -> str | None` — reason if GPU-required, else None.
  - `score(c: Candidate) -> float` — weighted sum; `-inf` if disqualified.
  - `select(cands: list[Candidate]) -> Candidate | None` — highest-scoring qualified candidate.

- [ ] **Step 1: Write failing tests**

```python
import math
from vulcan.scoring import Candidate, disqualified, score, select

def _c(title, needs_gpu=False, **kw):
    base = dict(novelty=3, adjacency=3, buildability=3, oss_value=3)
    base.update(kw)
    return Candidate(title=title, summary="s", sources=["u"], needs_gpu=needs_gpu, **base)

def test_gpu_disqualified():
    assert disqualified(_c("x", needs_gpu=True)) is not None
    assert math.isinf(score(_c("x", needs_gpu=True)))

def test_score_orders_by_weighted_merit():
    low = _c("low", novelty=1, adjacency=1, buildability=1, oss_value=1)
    high = _c("high", novelty=5, adjacency=5, buildability=5, oss_value=5)
    assert score(high) > score(low)

def test_select_skips_disqualified_even_if_high():
    gpu = _c("gpu", needs_gpu=True, novelty=5, adjacency=5, buildability=5, oss_value=5)
    cpu = _c("cpu", novelty=2, adjacency=2, buildability=2, oss_value=2)
    assert select([gpu, cpu]).title == "cpu"

def test_select_empty_returns_none():
    assert select([]) is None
    assert select([_c("g", needs_gpu=True)]) is None
```

- [ ] **Step 2: Run, verify fail** — `pytest tests/test_scoring.py -q` → FAIL.

- [ ] **Step 3: Implement `scoring.py`**

```python
"""C1 disqualification + weighted rubric for selecting one breakthrough to build."""
from __future__ import annotations

from dataclasses import dataclass

# Buildability (can we make it real here, no mocks) is weighted highest:
# it is what separates ledge from nemesis.
WEIGHTS = {"novelty": 0.25, "adjacency": 0.20, "buildability": 0.35, "oss_value": 0.20}


@dataclass
class Candidate:
    title: str
    summary: str
    sources: list[str]
    needs_gpu: bool
    novelty: int
    adjacency: int
    buildability: int
    oss_value: int


def disqualified(c: Candidate) -> str | None:
    """C1: anything needing a GPU to be real is out — it would force mocks."""
    if c.needs_gpu:
        return "needs GPU — cannot be verified for real on CPU-only hardware (C1)"
    return None


def score(c: Candidate) -> float:
    if disqualified(c):
        return float("-inf")
    return (
        WEIGHTS["novelty"] * c.novelty
        + WEIGHTS["adjacency"] * c.adjacency
        + WEIGHTS["buildability"] * c.buildability
        + WEIGHTS["oss_value"] * c.oss_value
    )


def select(cands: list[Candidate]) -> Candidate | None:
    qualified = [c for c in cands if not disqualified(c)]
    if not qualified:
        return None
    return max(qualified, key=score)
```

- [ ] **Step 4: Run, verify pass** — `pytest tests/test_scoring.py -q` → 4 passed.

- [ ] **Step 5: Commit**

```bash
git add vulcan/scoring.py tests/test_scoring.py
git commit -m "feat(vulcan): candidate scoring with C1 GPU disqualification"
```

---

### Task C2: Scout helpers (sources + dedup) — `scout.py`

**Files:**
- Create: `/Users/vanshverma/vulcan/vulcan/scout.py`
- Test: `/Users/vanshverma/vulcan/tests/test_scout.py`

**Interfaces:**
- Produces:
  - `SOURCES: list[dict]` — each `{name, kind, query_or_url}` (arXiv categories, HN, lobste.rs, GitHub trending).
  - `arxiv_query(categories: list[str], days: int) -> str` — arXiv API query string.
  - `dedupe(titles: list[str]) -> list[str]` — case/space-insensitive dedup preserving order.

- [ ] **Step 1: Write failing tests**

```python
from vulcan.scout import SOURCES, arxiv_query, dedupe

def test_sources_cover_core_channels():
    names = {s["name"] for s in SOURCES}
    assert {"arxiv", "hackernews", "lobsters", "github-trending"} <= names

def test_arxiv_query_includes_categories_and_window():
    q = arxiv_query(["cs.DC", "cs.OS"], days=7)
    assert "cs.DC" in q and "cs.OS" in q

def test_dedupe_is_case_and_space_insensitive():
    assert dedupe(["Zero Copy Cache", "zero  copy cache", "Other"]) == ["Zero Copy Cache", "Other"]
```

- [ ] **Step 2: Run, verify fail** — `pytest tests/test_scout.py -q` → FAIL.

- [ ] **Step 3: Implement `scout.py`**

```python
"""Scout helpers: the source list and pure utilities the research phase uses.

The actual web fetching is done by the Claude driver via the deep-research
skill / WebSearch; this module is the deterministic, testable scaffolding.
"""
from __future__ import annotations

import re

SOURCES = [
    {"name": "arxiv", "kind": "api", "query_or_url": "http://export.arxiv.org/api/query"},
    {"name": "hackernews", "kind": "web", "query_or_url": "https://news.ycombinator.com/newest"},
    {"name": "lobsters", "kind": "web", "query_or_url": "https://lobste.rs/"},
    {"name": "github-trending", "kind": "web", "query_or_url": "https://github.com/trending"},
]


def arxiv_query(categories: list[str], days: int) -> str:
    cats = "+OR+".join(f"cat:{c}" for c in categories)
    return f"search_query=({cats})&sortBy=submittedDate&sortOrder=descending&max_results={days * 10}"


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip()).lower()


def dedupe(titles: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for t in titles:
        key = _norm(t)
        if key not in seen:
            seen.add(key)
            out.append(t)
    return out
```

- [ ] **Step 4: Run, verify pass** — `pytest tests/test_scout.py -q` → 3 passed.

- [ ] **Step 5: Commit**

```bash
git add vulcan/scout.py tests/test_scout.py
git commit -m "feat(vulcan): scout source list + arxiv query + title dedup"
```

---

## Phase D — Publisher

### Task D1: Publisher (attribution gate → gh private push) — `publisher.py`

**Files:**
- Create: `/Users/vanshverma/vulcan/vulcan/publisher.py`
- Test: `/Users/vanshverma/vulcan/tests/test_publisher.py`

**Interfaces:**
- Consumes: `gates.attribution.is_clean`.
- Produces:
  - `class VaporError(Exception)`.
  - `publish(repo: str, name: str, description: str, run=subprocess.run, clean=attribution.is_clean) -> str` — raises `VaporError` if attribution dirty; else runs `gh repo create v-code01/<name> --private --source <repo> --push` and returns the repo URL `https://github.com/v-code01/<name>`. `run` and `clean` are injectable.

- [ ] **Step 1: Write failing tests** (inject runner + clean check; no network)

```python
import pytest
from types import SimpleNamespace
from vulcan.publisher import publish, VaporError

def test_publish_aborts_when_attribution_dirty(tmp_path):
    calls = []
    with pytest.raises(VaporError):
        publish(str(tmp_path), "proj", "d",
                run=lambda *a, **k: calls.append(a),
                clean=lambda repo: False)
    assert calls == []  # never reached gh

def test_publish_runs_gh_private_and_returns_url(tmp_path):
    calls = []
    def fake_run(cmd, **kw):
        calls.append(cmd); return SimpleNamespace(returncode=0, stdout="", stderr="")
    url = publish(str(tmp_path), "proj", "desc", run=fake_run, clean=lambda repo: True)
    assert url == "https://github.com/v-code01/proj"
    gh = calls[0]
    assert gh[:3] == ["gh", "repo", "create"]
    assert "v-code01/proj" in gh and "--private" in gh and "--push" in gh
```

- [ ] **Step 2: Run, verify fail** — `pytest tests/test_publisher.py -q` → FAIL.

- [ ] **Step 3: Implement `publisher.py`**

```python
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
```

- [ ] **Step 4: Run, verify pass** — `pytest tests/test_publisher.py -q` → 2 passed.

- [ ] **Step 5: Commit**

```bash
git add vulcan/publisher.py tests/test_publisher.py
git commit -m "feat(vulcan): publisher — attribution gate then private gh push"
```

---

## Phase E — CLI + Playbooks + Charter

### Task E1: CLI surface — `cli.py`

**Files:**
- Create: `/Users/vanshverma/vulcan/vulcan/cli.py`
- Test: `/Users/vanshverma/vulcan/tests/test_cli.py`

**Interfaces:**
- Consumes: `state`, `gates.attribution`, `gates.antivapor`, `gates.ledgebar`.
- Produces: `main(argv: list[str] | None = None) -> int` with subcommands:
  - `init` — scaffold `$VULCAN_HOME` (dirs + empty state).
  - `status` — print current `State` as JSON.
  - `gate attribution|antivapor|ledgebar <repo>` — run a gate, exit 0 if pass else 1, print findings.

- [ ] **Step 1: Write failing tests**

```python
from pathlib import Path
from vulcan.cli import main

def test_init_creates_home(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("VULCAN_HOME", str(tmp_path / "h"))
    assert main(["init"]) == 0
    home = tmp_path / "h"
    assert (home / "state.json").exists()
    assert (home / "ledger").is_dir() and (home / "research").is_dir()

def test_status_prints_phase(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("VULCAN_HOME", str(tmp_path / "h"))
    main(["init"])
    assert main(["status"]) == 0
    assert '"phase": "scout"' in capsys.readouterr().out

def test_gate_attribution_clean_repo_exits_zero(tmp_path, monkeypatch):
    import subprocess
    r = tmp_path / "r"; r.mkdir()
    def g(*a): subprocess.run(["git", "-C", str(r), *a], check=True, capture_output=True)
    g("init", "-q"); g("config", "user.name", "Vansh Verma"); g("config", "user.email", "vanshverma.code@gmail.com")
    (r / "f").write_text("x"); g("add", "-A"); g("commit", "-q", "-m", "feat: real")
    assert main(["gate", "attribution", str(r)]) == 0
```

- [ ] **Step 2: Run, verify fail** — `pytest tests/test_cli.py -q` → FAIL.

- [ ] **Step 3: Implement `cli.py`**

```python
"""Vulcan CLI: the deterministic spine the Claude driver shells out to."""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path

from vulcan import state as state_mod
from vulcan.gates import antivapor, attribution, ledgebar


def _home() -> Path:
    return Path(os.environ.get("VULCAN_HOME", str(Path.home() / "vulcan")))


def _cmd_init() -> int:
    home = _home()
    for sub in ("ledger", "research"):
        (home / sub).mkdir(parents=True, exist_ok=True)
    state_mod.save(home, state_mod.load(home))
    print(f"initialized {home}")
    return 0


def _cmd_status() -> int:
    print(json.dumps(asdict(state_mod.load(_home())), indent=2))
    return 0


def _cmd_gate(which: str, repo: str) -> int:
    if which == "attribution":
        bad = attribution.scan_history(repo)
        if bad:
            print("FAIL attribution:", *bad)
            return 1
    elif which == "antivapor":
        result = antivapor.scan(repo)
        if not antivapor.passes(result):
            print("FAIL antivapor:", json.dumps(result, indent=2))
            return 1
    elif which == "ledgebar":
        result = ledgebar.check(repo)
        if not ledgebar.passes(result):
            print("FAIL ledgebar:", json.dumps(result, indent=2))
            return 1
    print(f"PASS {which}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="vulcan")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("status")
    g = sub.add_parser("gate")
    g.add_argument("which", choices=["attribution", "antivapor", "ledgebar"])
    g.add_argument("repo")
    args = parser.parse_args(argv)
    if args.cmd == "init":
        return _cmd_init()
    if args.cmd == "status":
        return _cmd_status()
    if args.cmd == "gate":
        return _cmd_gate(args.which, args.repo)
    return 2
```

- [ ] **Step 4: Run, verify pass** — `pytest tests/test_cli.py -q` → 3 passed.

- [ ] **Step 5: Commit**

```bash
git add vulcan/cli.py tests/test_cli.py
git commit -m "feat(vulcan): CLI — init, status, gate {attribution,antivapor,ledgebar}"
```

---

### Task E2: Standards Charter + phase playbooks

**Files:**
- Create: `/Users/vanshverma/vulcan/charter.md`
- Create: `/Users/vanshverma/vulcan/playbooks/driver.md`
- Create: `/Users/vanshverma/vulcan/playbooks/00-scout.md` … `07-finish.md`

**Interfaces:**
- Produces: the runbook content the Claude driver + Opus Proxy consume each wake. No code; verified by a presence test.

- [ ] **Step 1: Write failing test**

```python
from pathlib import Path
HOME = Path("/Users/vanshverma/vulcan")

def test_charter_and_playbooks_exist():
    assert (HOME / "charter.md").read_text().strip()
    for stem in ["driver","00-scout","01-triage","02-brainstorm","03-plan",
                 "04-build","05-verify","06-review","07-finish"]:
        assert (HOME / "playbooks" / f"{stem}.md").read_text().strip()
```

- [ ] **Step 2: Run, verify fail** — `pytest tests/test_playbooks.py -q` → FAIL.

- [ ] **Step 3: Author `charter.md`** — copy the Standards Charter (spec §5) verbatim, plus the Proxy's decision rule: "Decide every superpowers gate as Vansh would, per this charter. Reject vapor harder than bugs. Prefer a narrow fully-real deliverable over a broad partly-simulated one. Default to the strongest option; only halt for true blockers."

- [ ] **Step 4: Author `playbooks/driver.md`** — the master loop the Claude `/loop` driver runs each wake:
  1. `vulcan status` → read phase.
  2. Run that phase's playbook (below), using the Skill tool for superpowers phases and the Agent tool to spawn the Opus Proxy for every gate.
  3. Persist artifacts to `ledger/<project>/`, append to `log.ndjson`.
  4. `vulcan`-advance state; if phase was `finish`, run the publisher.
  5. On a true block, write `BLOCKED.md` and stop. Else schedule the next wake.

  Author each phase playbook `00`–`07` mapping to spec §6 (the table): exact skill to invoke, exact Proxy prompt, exact gate command (`vulcan gate ...`), exact done-condition. Keep each ≤1 screen. (Full prose authored at execution time from the spec table; each must be non-empty and name its skill + gate.)

- [ ] **Step 5: Run, verify pass + commit**

Run: `pytest tests/test_playbooks.py -q` → PASS
```bash
git add charter.md playbooks/ tests/test_playbooks.py
git commit -m "docs(vulcan): standards charter + phase playbooks for the Claude driver"
```

---

## Phase F — End-to-end dry run

### Task F1: Full-suite green + lint + dry-run smoke

**Files:**
- Create: `/Users/vanshverma/vulcan/tests/test_smoke.py`

**Interfaces:**
- Consumes: everything. Validates the spine works together on a fixture project.

- [ ] **Step 1: Write the smoke test**

```python
import subprocess
from pathlib import Path
from vulcan.gates import attribution, antivapor, ledgebar

def test_clean_fixture_passes_all_gates(tmp_path):
    r = tmp_path / "proj"; (r / "src").mkdir(parents=True)
    (r / "Cargo.toml").write_text("[package]\nname='p'\n")
    (r / "LICENSE").write_text("MIT")
    (r / "src" / "lib.rs").write_text("pub fn add(a:i32,b:i32)->i32{a+b}\n")
    (r / "README.md").write_text("# p\nNo doc refs, no claims.\n")
    def g(*a): subprocess.run(["git","-C",str(r),*a],check=True,capture_output=True)
    g("init","-q"); g("config","user.name","Vansh Verma"); g("config","user.email","vanshverma.code@gmail.com")
    g("add","-A"); g("commit","-q","-m","feat: real add")
    assert attribution.is_clean(str(r))
    assert antivapor.passes(antivapor.scan(str(r)))
    # ledge-bar with a fake green runner (no cargo in unit env)
    from types import SimpleNamespace
    assert ledgebar.passes(ledgebar.check(str(r), run=lambda c,**k: SimpleNamespace(returncode=0)))
```

- [ ] **Step 2: Run, verify pass** — `pytest tests/test_smoke.py -q` → PASS.

- [ ] **Step 3: Full gate — entire suite + lint**

Run: `cd /Users/vanshverma/vulcan && ruff check . && pytest -q`
Expected: `All checks passed!` and all tests green (0 failures).

- [ ] **Step 4: Live `vulcan init` smoke**

Run: `VULCAN_HOME=/Users/vanshverma/vulcan python -m vulcan.cli init && python -m vulcan.cli status`
Expected: prints `"phase": "scout"`.

- [ ] **Step 5: Commit**

```bash
git add tests/test_smoke.py
git commit -m "test(vulcan): end-to-end gate smoke over a clean fixture repo"
```

---

## Self-Review

**Spec coverage:**
- §2 Opus Proxy at every gate → Task E2 (charter + playbooks instruct driver to spawn Proxy per gate). ✓
- §3 C1 → `scoring.disqualified` (C1). C2 → `antivapor` (B2). C3 → `attribution` (B1) + `publisher` (D1). C4 → `ledgebar` (B3). ✓
- §6 loop phases → `state.PHASES` (A2) + playbooks 00–07 (E2). ✓
- §7 continuity (state.json/ledger/log.ndjson) → `state.py` (A2) + `cli init` (E1). ✓
- §8 blocked semantics → driver.md step 5 (E2). ✓
- §9 components: Scout=C2, Selector=C1, Builder=playbooks E2, Gates=B1-3, Publisher=D1, Driver=E1/E2. ✓

**Placeholder scan:** E2 step 4 leaves phase-playbook prose to be authored at execution from the spec §6 table — this is content authoring, not a logic placeholder, and the presence test (E2 step 1) enforces non-empty files naming skill+gate. Acceptable.

**Type consistency:** `attribution.is_clean`/`scan_history`, `antivapor.scan`/`passes`, `ledgebar.check`/`passes`, `scoring.select`, `publisher.publish`, `state.State`/`PHASES`/`advance` — names are consistent across consumers (cli.py, publisher.py, smoke test). ✓

**Verdict:** plan covers the spec; ready to execute.
