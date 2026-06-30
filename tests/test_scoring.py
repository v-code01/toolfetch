import math

from vulcan.scoring import Candidate, disqualified, score, select


def _c(title, needs_gpu=False, **kw):
    base = dict(novelty=3, adjacency=3, buildability=3, oss_value=3)
    base.update(kw)
    return Candidate(title=title, summary="s", sources=["u"], needs_gpu=needs_gpu, **base)


def test_gpu_disqualified():
    assert disqualified(_c("x", needs_gpu=True)) is not None
    assert math.isinf(score(_c("x", needs_gpu=True)))


def test_score_orders_by_weighted_merit():
    low = _c("low", novelty=1, adjacency=1, buildability=1, oss_value=1)
    high = _c("high", novelty=5, adjacency=5, buildability=5, oss_value=5)
    assert score(high) > score(low)


def test_select_skips_disqualified_even_if_high():
    gpu = _c("gpu", needs_gpu=True, novelty=5, adjacency=5, buildability=5, oss_value=5)
    cpu = _c("cpu", novelty=2, adjacency=2, buildability=2, oss_value=2)
    assert select([gpu, cpu]).title == "cpu"


def test_select_empty_returns_none():
    assert select([]) is None
    assert select([_c("g", needs_gpu=True)]) is None
