from vulcan.scout import SOURCES, arxiv_query, dedupe


def test_sources_cover_core_channels():
    names = {s["name"] for s in SOURCES}
    assert {"arxiv", "hackernews", "lobsters", "github-trending"} <= names


def test_arxiv_query_includes_categories_and_window():
    q = arxiv_query(["cs.DC", "cs.OS"], days=7)
    assert "cs.DC" in q and "cs.OS" in q


def test_dedupe_is_case_and_space_insensitive():
    assert dedupe(["Zero Copy Cache", "zero  copy cache", "Other"]) == ["Zero Copy Cache", "Other"]
