from __future__ import annotations

from pathlib import Path

from app.retrieval.vector_store import HybridVectorStore


def test_delete_documents_removes_task_from_local_index(tmp_path: Path) -> None:
    store = HybridVectorStore(tmp_path / "vectors.json")
    store._chroma = None

    store.store_documents(
        "task_1",
        [
            {
                "title": "Retrieval planning",
                "abstract": "This paper discusses retrieval planning.",
                "summary": "Useful for Agentic RAG.",
                "url": "https://example.org/retrieval",
            }
        ],
    )

    assert store.retrieve_documents("task_1", "retrieval planning")

    store.delete_documents("task_1")

    assert store.retrieve_documents("task_1", "retrieval planning") == []
