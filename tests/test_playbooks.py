from pathlib import Path

HOME = Path("/Users/vanshverma/vulcan")


def test_charter_and_playbooks_exist():
    assert (HOME / "charter.md").read_text().strip()
    for stem in ["driver", "00-scout", "01-triage", "02-brainstorm", "03-plan",
                 "04-build", "05-verify", "06-review", "07-finish"]:
        assert (HOME / "playbooks" / f"{stem}.md").read_text().strip()
