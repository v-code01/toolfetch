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
    r = tmp_path / "r"
    r.mkdir()
    def g(*a):
        subprocess.run(["git", "-C", str(r), *a], check=True, capture_output=True)
    g("init", "-q")
    g("config", "user.name", "Vansh Verma")
    g("config", "user.email", "vanshverma.code@gmail.com")
    (r / "f").write_text("x")
    g("add", "-A")
    g("commit", "-q", "-m", "feat: real")
    assert main(["gate", "attribution", str(r)]) == 0
