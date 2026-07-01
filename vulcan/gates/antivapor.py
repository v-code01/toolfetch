"""C2 gate: refuse vapor — stubs, mocks, dangling docs, and unbacked claims.

Encodes the nemesis-audit failure modes as mechanical checks. The README's
honesty is enforced by `vulcan-claims.toml`: every headline claim must name an
`evidence` string that grep finds in its backing `files`.

C2 mechanization boundary (stated decision, not omission)
---------------------------------------------------------
The clauses below are *fully mechanized* by this module and the CLI gate:
  - stub markers (`todo!`, `unimplemented!`, `unreachable!`, `panic!/bail!`
    "not implemented"-style messages) outside test paths        -> find_stubs
  - mock-framework usage outside test paths                      -> find_prod_mocks
  - dangling `docs/...` references that resolve to no file/dir   -> find_dangling_doc_refs
  - README/doc claims that grep cannot find in code, via the
    `vulcan-claims.toml` evidence manifest, AND fail-closed when
    a claim-bearing README ships with no manifest at all         -> verify_claims / scan

Two C2 clauses are *genuinely dynamic* and CANNOT be soundly mechanized by a
static grep; they are explicitly DELEGATED to the Opus Proxy at Phase 5
(verify) time, per `playbooks/05-verify.md`:
  - No strawman benchmarks. Whether a baseline is a real, defensible
    alternative system run on the same hardware/inputs (vs. a hardcoded
    constant like the nemesis `17.17x == 600/25`) requires judgement about
    what the baseline *means*, which grep cannot supply.
  - No tautological datasets. Whether a benchmark dataset is adversarial or
    trivially separable (the nemesis healthy~0 vs failing-ramp-to-10 giving a
    meaningless F1=0.98) requires statistical adjudication of separability.
The Proxy must manually adjudicate both at verify time; this module does not
silently pretend to cover them.
"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

STUB_PATTERNS = [
    r"todo!\(",
    r"unimplemented!\(",
    # Bare `unreachable!()` (no justification) is a lazy stub; a justified
    # `unreachable!("<reason>")` documenting a proven-impossible branch is a
    # legitimate invariant guard and is NOT flagged. Also flag stub-worded ones.
    r"unreachable!\(\s*\)",
    r'unreachable!\(\s*"[^"]*(?:not implemented|unimplemented|todo|fixme)',
    # panic!/bail! whose message announces missing work, in any case.
    r'panic!\(\s*"[^"]*(?:not implemented|unimplemented|todo)',
    r"bail!\([^)]*(?:not yet implemented|not implemented|unimplemented)",
    r"raise NotImplementedError",
]
_STUB_RE = re.compile("|".join(STUB_PATTERNS), re.IGNORECASE)

# Mock-framework usage is vapor outside test code (C2: "No mock framework
# usage outside #[cfg(test)] / test modules").
_MOCK_RE = re.compile(
    r"\bmockall\b|mock!\(|unittest\.mock|from\s+unittest\s+import\s+mock|@patch\b",
)

_SRC_EXT = {".rs", ".py", ".go", ".ts", ".c", ".h", ".cpp", ".zig"}
# Any docs/<path> reference (not just .md): bare dirs and other extensions count.
_DOC_REF_RE = re.compile(r"docs/[\w./-]+")
_README_RE = re.compile(r"readme.*\.md$", re.IGNORECASE)
# Benchmark-ish / claim-verb tokens that mark a README as making substantive,
# verifiable assertions (and therefore requiring a `vulcan-claims.toml`).
_CLAIM_TOKEN_RE = re.compile(
    r"\d+(?:\.\d+)?\s*x\b"            # 17x, 17.17x, 600 x
    r"|\bGB/s\b|\bMB/s\b|\bGB/sec\b"
    r"|\d+(?:\.\d+)?\s*%"
    r"|\bspeedups?\b|\bspeed-up\b|\bfaster\b|\boutperform\w*"
    r"|\bbenchmark\w*|\bthroughput\b|\bachieves?\b|\bbeats\b",
    re.IGNORECASE,
)


def _is_test_path(rel: str) -> bool:
    parts = rel.replace("\\", "/").split("/")
    return any(p in ("tests", "test", "testkit") for p in parts) or rel.endswith("_test.py")


def _source_files(repo: str):
    root = Path(repo)
    for p in root.rglob("*"):
        if (
            p.is_file()
            and p.suffix in _SRC_EXT
            and ".git" not in p.parts
            and "target" not in p.parts
        ):
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


def find_prod_mocks(repo: str) -> list[tuple[str, int, str]]:
    """Flag mock-framework usage in non-test source (mocks belong in tests only)."""
    hits: list[tuple[str, int, str]] = []
    for path, rel in _source_files(repo):
        if _is_test_path(rel):
            continue
        for i, line in enumerate(path.read_text(errors="ignore").splitlines(), 1):
            m = _MOCK_RE.search(line)
            if m:
                hits.append((rel, i, m.group(0)))
    return hits


def find_dangling_doc_refs(repo: str) -> list[str]:
    root = Path(repo)
    referenced: set[str] = set()
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in (_SRC_EXT | {".md"}) and ".git" not in p.parts:
            for raw in _DOC_REF_RE.findall(p.read_text(errors="ignore")):
                # Strip trailing prose punctuation but keep a meaningful dir slash.
                referenced.add(raw.rstrip(".,;:)"))
    return sorted(ref for ref in referenced if not (root / ref).exists())


def manifest_present(repo: str) -> bool:
    """True if the claims manifest exists; absence is a fail-closed signal."""
    return (Path(repo) / "vulcan-claims.toml").exists()


def _readme_files(repo: str):
    root = Path(repo)
    if not root.exists():
        return
    for p in root.iterdir():
        if p.is_file() and _README_RE.match(p.name):
            yield p


def has_readme_claims(repo: str) -> bool:
    """True if a top-level README makes substantive, verifiable-looking claims.

    Substantive = long prose (>400 chars) OR benchmark-ish / claim-verb tokens
    (e.g. "17.17x", "GB/s", "speedup", "throughput"). Such a README MUST be
    backed by a `vulcan-claims.toml`; see `scan()` for the fail-closed policy.
    """
    for p in _readme_files(repo):
        text = p.read_text(errors="ignore")
        if len(text) > 400 or _CLAIM_TOKEN_RE.search(text):
            return True
    return False


def verify_claims(repo: str) -> list[str]:
    root = Path(repo)
    manifest = root / "vulcan-claims.toml"
    if not manifest.exists():
        return []  # absence handled by caller policy; see scan()
    claims = tomllib.loads(manifest.read_text()).get("claim", [])
    unbacked: list[str] = []
    for c in claims:
        # Defensive access: a malformed/incomplete claim is itself unbacked,
        # not a crash. Report its text (or a placeholder) and move on.
        evidence = c.get("evidence")
        files = c.get("files") or []
        text = c.get("text") or c.get("statement") or "<malformed claim: missing text>"
        if not evidence or not files:
            unbacked.append(text)
            continue
        # `evidence` may be a single substring or a list of substrings. Every
        # listed substring must appear in at least one of the claim's files;
        # a claim with any missing substring is unbacked.
        substrings = [evidence] if isinstance(evidence, str) else list(evidence)
        file_texts = [
            (root / f).read_text(errors="ignore") for f in files if (root / f).exists()
        ]
        for sub in substrings:
            if not any(isinstance(sub, str) and sub in ft for ft in file_texts):
                unbacked.append(text)
                break
    return unbacked


def scan(repo: str) -> dict:
    present = manifest_present(repo)
    readme_claims = has_readme_claims(repo)
    return {
        "stubs": find_stubs(repo),
        "prod_mocks": find_prod_mocks(repo),
        "dangling": find_dangling_doc_refs(repo),
        "unbacked_claims": verify_claims(repo),
        "manifest_present": present,
        "has_readme_claims": readme_claims,
        # Fail closed: a README that makes claims but ships no manifest is vapor.
        "missing_manifest": readme_claims and not present,
    }


def passes(result: dict) -> bool:
    return not (
        result["stubs"]
        or result["prod_mocks"]
        or result["dangling"]
        or result["unbacked_claims"]
        or result["missing_manifest"]
    )
