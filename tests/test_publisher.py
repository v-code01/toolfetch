from types import SimpleNamespace

import pytest

from vulcan.publisher import VaporError, publish


def test_publish_aborts_when_attribution_dirty(tmp_path):
    calls = []
    with pytest.raises(VaporError):
        publish(str(tmp_path), "proj", "d",
                run=lambda *a, **k: calls.append(a),
                clean=lambda repo: False)
    assert calls == []  # never reached gh


def test_publish_runs_gh_private_and_returns_url(tmp_path):
    calls = []
    def fake_run(cmd, **kw):
        calls.append(cmd)
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    url = publish(str(tmp_path), "proj", "desc", run=fake_run, clean=lambda repo: True)
    assert url == "https://github.com/v-code01/proj"
    gh = calls[0]
    assert gh[:3] == ["gh", "repo", "create"]
    assert "v-code01/proj" in gh and "--private" in gh and "--push" in gh
