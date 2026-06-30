from pathlib import Path
from types import SimpleNamespace

from vulcan.gates.ledgebar import check, detect_kind, has_license, passes


def _w(p: Path, t=""):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(t)


def test_detect_kind(tmp_path: Path):
    _w(tmp_path / "Cargo.toml", "[package]")
    assert detect_kind(str(tmp_path)) == "rust"


def test_has_license(tmp_path: Path):
    assert has_license(str(tmp_path)) is False
    _w(tmp_path / "LICENSE", "BSL")
    assert has_license(str(tmp_path)) is True


def test_check_rust_all_green(tmp_path: Path):
    _w(tmp_path / "Cargo.toml", "[package]")
    _w(tmp_path / "LICENSE", "MIT")
    calls = []
    def fake_run(cmd, **kw):
        calls.append(cmd)
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    result = check(str(tmp_path), run=fake_run)
    assert result["kind"] == "rust" and result["lint_ok"] and result["tests_ok"]
    assert passes(result) is True
    assert any("clippy" in " ".join(c) for c in calls)


def test_check_fails_on_lint(tmp_path: Path):
    _w(tmp_path / "Cargo.toml", "[package]")
    _w(tmp_path / "LICENSE", "MIT")
    def fake_run(cmd, **kw):
        rc = 101 if "clippy" in " ".join(cmd) else 0
        return SimpleNamespace(returncode=rc, stdout="", stderr="")
    result = check(str(tmp_path), run=fake_run)
    assert result["lint_ok"] is False and passes(result) is False


def test_check_fails_without_license(tmp_path: Path):
    _w(tmp_path / "Cargo.toml", "[package]")
    def fake_run(cmd, **kw):
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    assert passes(check(str(tmp_path), run=fake_run)) is False
