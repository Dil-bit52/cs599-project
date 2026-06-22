from __future__ import annotations

from pathlib import Path
from typing import Any

import app.agents.workflow as workflow_module
from app.agents.workflow import ResearchWorkflow
from app.memory.database import Database
from app.retrieval.vector_store import HybridVectorStore


class FakeLLM:
    def is_enabled(self) -> bool:
        return True

    def provider_name(self) -> str:
        return "fake-test-provider"

    def complete_json(self, *, system: str, user: str, max_tokens: int = 1200) -> dict[str, Any]:
        if "Evaluator Agent" in system:
            return {
                "relevance": 9,
                "citation": 8,
                "structure": 9,
                "faithfulness": 8,
                "overall": 8.5,
                "suggestions": ["Add full-text evidence verification."],
            }
        raise AssertionError(f"Unexpected JSON prompt: {system}")

    def complete_json_text(self, *, system: str, user: str, max_tokens: int = 1200) -> str:
        if "Planner Agent" in system:
            return (
                '{"keywords":["agentic rag","enterprise knowledge base","evaluation"],'
                '"research_questions":["What is Agentic RAG?","How is it evaluated?","What are its limitations?"],'
                '"outline":["Abstract","Background","Papers"'
            )
        raise AssertionError(f"Unexpected JSON-text prompt: {system}")

    def complete(self, *, system: str, user: str, max_tokens: int = 1200) -> str:
        if "Reader Agent" in system:
            return "This paper is relevant because it discusses retrieval, planning, and evidence-grounded generation."
        if "Synthesis Agent" in system:
            return "Agentic RAG combines retrieval and planning, but the model did not follow the requested section format."
        if "Writer Agent" in system:
            return "# Research Report\n\n## Abstract\n\nA generated report with references.\n\n## References\n\n1. Test paper."
        raise AssertionError(f"Unexpected text prompt: {system}")


def test_research_workflow_requires_llm_and_external_papers(tmp_path: Path, monkeypatch: Any) -> None:
    database = Database(tmp_path / "test.db")
    database.init()
    store = HybridVectorStore(tmp_path / "vectors.json")
    workflow = ResearchWorkflow(database=database, store=store, reports_dir=tmp_path, llm=FakeLLM())

    monkeypatch.setattr(
        workflow_module,
        "search_papers",
        lambda topic, keywords, max_papers: [
            {
                "title": "Test paper on Agentic RAG",
                "authors": ["Researcher A"],
                "year": 2025,
                "source": "OpenAlex",
                "abstract": "This paper studies retrieval, planning, and tool use in Agentic RAG.",
                "url": "https://example.org/test-paper",
                "relevance": 0.92,
            }
        ],
    )

    task_id = database.create_task("Agentic RAG in enterprise knowledge base", "en", 5)
    workflow.run(task_id)

    task = database.hydrate_task(task_id)
    assert task is not None
    assert task["status"] == "completed"
    assert task["progress"] == 100
    assert len(task["papers"]) == 1
    assert task["evaluation"]["overall"] == 8.5
    assert Path(task["report_path"]).exists()
