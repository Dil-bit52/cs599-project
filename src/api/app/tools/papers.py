from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

from app.config import settings


def search_papers(topic: str, keywords: list[str] | None = None, max_papers: int = 8) -> list[dict[str, Any]]:
    papers: list[dict[str, Any]] = []
    errors: list[str] = []
    queries = _search_queries(topic, keywords or [])
    for query in queries:
        for provider in (_search_openalex, _search_arxiv):
            try:
                provider_results = provider(query, max_papers)
                if provider_results:
                    papers.extend(provider_results)
                else:
                    errors.append(f"{provider.__name__} returned 0 results for query '{query}'")
            except Exception as exc:
                errors.append(f"{provider.__name__} failed for query '{query}': {exc}")

    if not papers:
        raise RuntimeError(
            "No papers were retrieved from external sources. "
            f"Queries tried: {', '.join(queries)}. "
            f"Details: {'; '.join(errors)}"
        )

    ranking_text = " ".join([topic, *(keywords or [])])
    return _dedupe(_rank_papers(ranking_text, papers))[:max_papers]


def fetch_paper_detail(url: str) -> dict[str, Any]:
    return {"url": url, "detail": "Full-text fetching is reserved for the extension stage."}


def _search_queries(topic: str, keywords: list[str]) -> list[str]:
    queries: list[str] = []
    for item in [topic, *keywords]:
        query = " ".join(str(item).strip().split())
        if query and query.lower() not in {existing.lower() for existing in queries}:
            queries.append(query)
    return queries[:6]


def _search_openalex(topic: str, limit: int) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode(
        {
            "search": topic,
            "per-page": min(limit, 10),
            "sort": "relevance_score:desc",
        }
    )
    url = f"{settings.openalex_base_url}/works?{query}"
    with urllib.request.urlopen(url, timeout=8) as response:
        payload = json.loads(response.read().decode("utf-8"))

    results: list[dict[str, Any]] = []
    for item in payload.get("results", []):
        title = _strip_html(item.get("title") or "")
        if not title:
            continue
        abstract = _openalex_abstract(item.get("abstract_inverted_index") or {})
        authors = [
            authorship.get("author", {}).get("display_name", "")
            for authorship in item.get("authorships", [])[:4]
            if authorship.get("author", {}).get("display_name")
        ]
        results.append(
            {
                "title": title,
                "authors": authors,
                "year": item.get("publication_year"),
                "source": "OpenAlex",
                "abstract": abstract or "No abstract is available from OpenAlex.",
                "url": item.get("doi") or item.get("id"),
            }
        )
    return results


def _search_arxiv(topic: str, limit: int) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode(
        {
            "search_query": f"all:{topic}",
            "start": 0,
            "max_results": min(limit, 10),
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
    )
    url = f"{settings.arxiv_base_url}?{query}"
    with urllib.request.urlopen(url, timeout=8) as response:
        xml_text = response.read().decode("utf-8", errors="ignore")

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_text)
    results: list[dict[str, Any]] = []
    for entry in root.findall("atom:entry", ns):
        title = " ".join((entry.findtext("atom:title", default="", namespaces=ns) or "").split())
        abstract = " ".join((entry.findtext("atom:summary", default="", namespaces=ns) or "").split())
        url = entry.findtext("atom:id", default="", namespaces=ns)
        published = entry.findtext("atom:published", default="", namespaces=ns)
        authors = [
            author.findtext("atom:name", default="", namespaces=ns)
            for author in entry.findall("atom:author", ns)[:4]
        ]
        if title:
            results.append(
                {
                    "title": title,
                    "authors": [author for author in authors if author],
                    "year": int(published[:4]) if published[:4].isdigit() else None,
                    "source": "arXiv",
                    "abstract": abstract,
                    "url": url,
                }
            )
    return results


def _openalex_abstract(index: dict[str, list[int]]) -> str:
    if not index:
        return ""
    words: list[tuple[int, str]] = []
    for word, positions in index.items():
        words.extend((position, word) for position in positions)
    return " ".join(word for _, word in sorted(words))


def _rank_papers(topic: str, papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    topic_terms = set(_terms(topic))
    ranked: list[dict[str, Any]] = []
    for paper in papers:
        text = f"{paper.get('title', '')} {paper.get('abstract', '')}"
        terms = set(_terms(text))
        overlap = len(topic_terms & terms)
        score = min(0.98, 0.55 + overlap * 0.08 + (0.08 if paper.get("year", 0) and paper["year"] >= 2022 else 0))
        item = dict(paper)
        item["relevance"] = round(score, 2)
        ranked.append(item)
    return sorted(ranked, key=lambda paper: paper["relevance"], reverse=True)


def _dedupe(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for paper in papers:
        key = re.sub(r"\W+", "", paper.get("title", "").lower())
        if key and key not in seen:
            unique.append(paper)
            seen.add(key)
    return unique


def _terms(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}|[\u4e00-\u9fff]{2,}", text.lower())


def _strip_html(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value)
