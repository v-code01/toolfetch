from pathlib import Path

from vulcan.gates.antivapor import (
    find_dangling_doc_refs,
    find_stubs,
    passes,
    scan,
    verify_claims,
)


def _w(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


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
