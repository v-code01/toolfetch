import subprocess
from types import SimpleNamespace

from vulcan.gates import antivapor, attribution, ledgebar


def test_clean_fixture_passes_all_gates(tmp_path):
    r = tmp_path / "proj"
    (r / "src").mkdir(parents=True)
    (r / "Cargo.toml").write_text("[package]\nname='p'\n")
    (r / "LICENSE").write_text("MIT")
    (r / "src" / "lib.rs").write_text("pub fn add(a:i32,b:i32)->i32{a+b}\n")
    (r / "README.md").write_text("# p\nNo doc refs, no claims.\n")
    def g(*a):
        subprocess.run(["git", "-C", str(r), *a], check=True, capture_output=True)
    g("init", "-q")
    g("config", "user.name", "Vansh Verma")
    g("config", "user.email", "vanshverma.code@gmail.com")
    g("add", "-A")
    g("commit", "-q", "-m", "feat: real add")
    assert attribution.is_clean(str(r))
    assert antivapor.passes(antivapor.scan(str(r)))
    # ledge-bar with a fake green runner (no cargo in unit env)
    assert ledgebar.passes(ledgebar.check(str(r), run=lambda c, **k: SimpleNamespace(returncode=0)))
