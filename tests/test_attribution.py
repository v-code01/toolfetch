import subprocess
from pathlib import Path

from vulcan.gates.attribution import is_clean, scan_history


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
    r = tmp_path / "clean"
    _init(r)
    _commit(r, "feat: real work")
    _commit(r, "fix: more real work", "g.txt")
    assert scan_history(str(r)) == []
    assert is_clean(str(r)) is True


def test_detects_co_authored_by_claude(tmp_path: Path):
    r = tmp_path / "dirty"
    _init(r)
    _commit(r, "feat: thing\n\nCo-Authored-By: Claude <noreply@anthropic.com>")
    assert len(scan_history(str(r))) == 1
    assert is_clean(str(r)) is False


def test_detects_generated_with(tmp_path: Path):
    r = tmp_path / "gen"
    _init(r)
    _commit(r, "feat: thing\n\nGenerated with Claude Code")
    assert is_clean(str(r)) is False
