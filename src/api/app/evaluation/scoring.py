from __future__ import annotations

import re
from typing import Any


def evaluate_report(topic: str, report: str, papers: list[dict[str, Any]]) -> dict[str, Any]:
    topic_terms = set(_terms(topic))
    report_terms = set(_terms(report))
    relevance = 7.0 + min(len(topic_terms & report_terms), 3)
    citation = min(10.0, 5.0 + len([paper for paper in papers if paper.get("url")]) * 0.7)
    structure = min(10.0, 5.0 + len(re.findall(r"^##\s+", report, flags=re.MULTILINE)) * 0.6)
    faithfulness = 8.0 if papers else 5.0

    suggestions: list[str] = []
    if citation < 8:
        suggestions.append("Increase citation coverage by linking every key claim to a paper source.")
    if structure < 8:
        suggestions.append("Improve report structure with clearer headings and comparison tables.")
    if faithfulness < 8:
        suggestions.append("Add stronger evidence grounding before making conclusions.")
    if not suggestions:
        suggestions.append("The report is suitable for review; next step is full-text evidence verification.")

    overall = round((relevance + citation + structure + faithfulness) / 4, 1)
    return {
        "relevance": round(min(relevance, 10.0), 1),
        "citation": round(min(citation, 10.0), 1),
        "structure": round(min(structure, 10.0), 1),
        "faithfulness": round(min(faithfulness, 10.0), 1),
        "overall": overall,
        "suggestions": suggestions,
    }


def _terms(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}|[\u4e00-\u9fff]{2,}", text.lower())
