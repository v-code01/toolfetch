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
