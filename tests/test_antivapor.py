from pathlib import Path

from vulcan.gates.antivapor import (
    find_dangling_doc_refs,
    find_prod_mocks,
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


def test_find_stubs_flags_unreachable_and_broad_panic(tmp_path: Path):
    _w(tmp_path / "src/x.rs", "fn a() { unreachable!() }\n")  # I-2: was missed
    _w(tmp_path / "src/y.rs", 'fn b() { panic!("UNIMPLEMENTED yet") }\n')
    _w(tmp_path / "src/z.rs", 'fn c() { bail!("this path is unimplemented") }\n')
    _w(tmp_path / "tests/x.rs", "fn t() { unreachable!() }\n")  # legit test arm
    hits = find_stubs(str(tmp_path))
    files = {h[0] for h in hits}
    assert {"src/x.rs", "src/y.rs", "src/z.rs"} <= files
    assert not any("tests/x.rs" in f for f in files)


def test_find_prod_mocks_flags_mock_in_src_not_tests(tmp_path: Path):
    _w(tmp_path / "src/x.rs", "use mockall::predicate;\n")
    _w(tmp_path / "tests/x.rs", "use mockall::predicate;\n")
    _w(tmp_path / "src/svc.py", "from unittest import mock\n")
    hits = find_prod_mocks(str(tmp_path))
    files = {h[0] for h in hits}
    assert "src/x.rs" in files and "src/svc.py" in files
    assert not any("tests/x.rs" in f for f in files)


def test_find_dangling_doc_refs(tmp_path: Path):
    _w(tmp_path / "README.md", "See docs/arch/present.md and docs/arch/missing.md\n")
    _w(tmp_path / "docs/arch/present.md", "here")
    dangling = find_dangling_doc_refs(str(tmp_path))
    assert dangling == ["docs/arch/missing.md"]


def test_dangling_doc_refs_non_md_extension(tmp_path: Path):
    # M-3: refs to non-.md docs paths must also be verified.
    _w(tmp_path / "README.md", "Benchmarks in docs/bench.json and docs/results.csv\n")
    _w(tmp_path / "docs/bench.json", "{}")
    dangling = find_dangling_doc_refs(str(tmp_path))
    assert dangling == ["docs/results.csv"]


def test_verify_claims_backed_and_unbacked(tmp_path: Path):
    _w(tmp_path / "src/ring.rs", "// a real seqlock\nstruct Seqlock;\n")
    _w(tmp_path / "claims.toml",
       '[[claim]]\ntext="uses a seqlock"\nevidence="Seqlock"\nfiles=["src/ring.rs"]\n'
       '[[claim]]\ntext="alibaba trace"\nevidence="alibaba"\nfiles=["src/ring.rs"]\n')
    unbacked = verify_claims(str(tmp_path))
    assert unbacked == ["alibaba trace"]


def test_verify_claims_malformed_missing_evidence(tmp_path: Path):
    # M-1: a claim missing `evidence` is reported as unbacked, not a KeyError.
    _w(tmp_path / "src/x.rs", "struct S;\n")
    _w(tmp_path / "claims.toml",
       '[[claim]]\ntext="no evidence key"\nfiles=["src/x.rs"]\n')
    unbacked = verify_claims(str(tmp_path))
    assert "no evidence key" in unbacked


def test_verify_claims_evidence_list_and_statement(tmp_path: Path):
    # A claim may use `statement` (alias of text) and a LIST of evidence
    # substrings; every substring must be present, else the claim is unbacked.
    _w(tmp_path / "src/a.rs", "// marker_alpha marker_beta 1.70x\nstruct S;\n")
    _w(tmp_path / "claims.toml",
       '[[claim]]\nstatement="alpha beta and ratio"\nfiles=["src/a.rs"]\n'
       'evidence=["marker_alpha", "marker_beta", "1.70x"]\n')
    assert verify_claims(str(tmp_path)) == []  # all present -> backed
    _w(tmp_path / "claims.toml",
       '[[claim]]\nstatement="one missing"\nfiles=["src/a.rs"]\n'
       'evidence=["marker_alpha", "NOT_THERE"]\n')
    assert verify_claims(str(tmp_path)) == ["one missing"]  # one missing -> unbacked


def test_justified_unreachable_not_a_stub(tmp_path: Path):
    # A justified `unreachable!("<reason>")` (proven-impossible branch) is a
    # legitimate invariant guard, NOT a stub. Bare/stub-worded ones ARE stubs.
    _w(tmp_path / "src/ok.rs",
       'fn f() { unreachable!("rho checks always give a dependent set"); }\n')
    _w(tmp_path / "src/bare.rs", "fn g() { unreachable!() }\n")
    _w(tmp_path / "src/stub.rs", 'fn h() { unreachable!("TODO implement") }\n')
    hits = {rel for rel, _line, _pat in find_stubs(str(tmp_path))}
    assert not any("ok.rs" in h for h in hits), "justified unreachable must be allowed"
    assert any("bare.rs" in h for h in hits), "bare unreachable!() is a stub"
    assert any("stub.rs" in h for h in hits), "stub-worded unreachable is a stub"


def test_scan_passes_on_clean_repo(tmp_path: Path):
    # A "clean" repo with a claim-bearing README must carry a matching manifest.
    _w(tmp_path / "src/lib.rs", "// real seqlock ring\nstruct Seqlock;\n")
    _w(tmp_path / "README.md",
       "This crate achieves a 3x speedup using a Seqlock ring buffer.\n")
    _w(tmp_path / "claims.toml",
       '[[claim]]\ntext="3x speedup via seqlock"\nevidence="Seqlock"\nfiles=["src/lib.rs"]\n')
    result = scan(str(tmp_path))
    assert passes(result) is True


def test_scan_fails_when_readme_claims_without_manifest(tmp_path: Path):
    # C-1 nemesis scenario: overclaiming README, no manifest -> fail closed.
    _w(tmp_path / "src/lib.rs", "fn a() -> i32 { 1 }\n")
    _w(tmp_path / "README.md",
       "Vulcan delivers a 17.17x speedup vs the Alibaba cluster trace.\n")
    result = scan(str(tmp_path))
    assert result["missing_manifest"] is True
    assert passes(result) is False
