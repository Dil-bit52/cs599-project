from __future__ import annotations

from pathlib import Path

from app.memory.database import Database


def test_delete_task_removes_related_records(tmp_path: Path) -> None:
    database = Database(tmp_path / "test.db")
    database.init()

    task_id = database.create_task("Agentic RAG", "en", 5)
    database.add_log(task_id, "Planner Agent", "completed", "planned")
    database.replace_papers(
        task_id,
        [
            {
                "title": "Agentic RAG paper",
                "authors": ["Researcher A"],
                "year": 2026,
                "source": "OpenAlex",
                "abstract": "A paper about retrieval and planning.",
                "url": "https://example.org/paper",
                "relevance": 0.91,
                "summary": "Relevant paper.",
            }
        ],
    )
    database.set_evaluation(
        task_id,
        {
            "relevance": 9,
            "citation": 8,
            "structure": 9,
            "faithfulness": 8,
            "overall": 8.5,
            "suggestions": ["Add more evidence."],
        },
    )

    deleted = database.delete_task(task_id)

    assert deleted is not None
    assert deleted["task_id"] == task_id
    assert database.get_task(task_id) is None
    assert database.get_logs(task_id) == []
    assert database.get_papers(task_id) == []
    assert database.get_evaluation(task_id) is None

    database.add_log(task_id, "Workflow", "completed", "late log")
    database.replace_papers(task_id, [])
    database.set_evaluation(
        task_id,
        {
            "relevance": 1,
            "citation": 1,
            "structure": 1,
            "faithfulness": 1,
            "overall": 1,
            "suggestions": [],
        },
    )

    assert database.get_logs(task_id) == []
    assert database.get_papers(task_id) == []
    assert database.get_evaluation(task_id) is None
