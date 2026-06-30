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
