"""Scout helpers: the source list and pure utilities the research phase uses.

The actual web fetching is done by the Claude driver via the deep-research
skill / WebSearch; this module is the deterministic, testable scaffolding.
"""
from __future__ import annotations

import re

SOURCES = [
    {"name": "arxiv", "kind": "api", "query_or_url": "http://export.arxiv.org/api/query"},
    {"name": "hackernews", "kind": "web", "query_or_url": "https://news.ycombinator.com/newest"},
    {"name": "lobsters", "kind": "web", "query_or_url": "https://lobste.rs/"},
    {"name": "github-trending", "kind": "web", "query_or_url": "https://github.com/trending"},
]


def arxiv_query(categories: list[str], days: int) -> str:
    cats = "+OR+".join(f"cat:{c}" for c in categories)
    return (
        f"search_query=({cats})&sortBy=submittedDate"
        f"&sortOrder=descending&max_results={days * 10}"
    )


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip()).lower()


def dedupe(titles: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for t in titles:
        key = _norm(t)
        if key not in seen:
            seen.add(key)
            out.append(t)
    return out
