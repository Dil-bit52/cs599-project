from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import settings


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or settings.database_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    language TEXT NOT NULL,
                    max_papers INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    current_step TEXT NOT NULL,
                    progress INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    report_path TEXT,
                    error TEXT
                );

                CREATE TABLE IF NOT EXISTS papers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    authors TEXT NOT NULL,
                    year INTEGER,
                    source TEXT NOT NULL,
                    abstract TEXT NOT NULL,
                    url TEXT,
                    relevance REAL NOT NULL,
                    summary TEXT,
                    FOREIGN KEY(task_id) REFERENCES tasks(task_id)
                );

                CREATE TABLE IF NOT EXISTS agent_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT NOT NULL,
                    payload TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(task_id) REFERENCES tasks(task_id)
                );

                CREATE TABLE IF NOT EXISTS evaluations (
                    task_id TEXT PRIMARY KEY,
                    relevance REAL NOT NULL,
                    citation REAL NOT NULL,
                    structure REAL NOT NULL,
                    faithfulness REAL NOT NULL,
                    overall REAL NOT NULL,
                    suggestions TEXT NOT NULL,
                    FOREIGN KEY(task_id) REFERENCES tasks(task_id)
                );
                """
            )
            self._drop_legacy_demo_mode_column(conn)

    def create_task(self, topic: str, language: str, max_papers: int) -> str:
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        now = utc_now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO tasks (
                    task_id, topic, language, max_papers, status, current_step,
                    progress, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (task_id, topic, language, max_papers, "created", "queued", 0, now, now),
            )
        return task_id

    def _drop_legacy_demo_mode_column(self, conn: sqlite3.Connection) -> None:
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()]
        if "demo_mode" not in columns:
            return
        try:
            conn.execute("ALTER TABLE tasks DROP COLUMN demo_mode")
        except sqlite3.OperationalError:
            # Older SQLite builds may not support DROP COLUMN. In that case the
            # extra ignored column can remain in existing local development DBs.
            pass

    def _task_exists(self, conn: sqlite3.Connection, task_id: str) -> bool:
        row = conn.execute("SELECT 1 FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        return row is not None

    def list_tasks(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._task_row(row) for row in rows]

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        return self._task_row(row) if row else None

    def delete_task(self, task_id: str) -> dict[str, Any] | None:
        task = self.get_task(task_id)
        if not task:
            return None
        with self.connect() as conn:
            conn.execute("DELETE FROM papers WHERE task_id = ?", (task_id,))
            conn.execute("DELETE FROM agent_logs WHERE task_id = ?", (task_id,))
            conn.execute("DELETE FROM evaluations WHERE task_id = ?", (task_id,))
            conn.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
        return task

    def update_task(
        self,
        task_id: str,
        *,
        status: str | None = None,
        current_step: str | None = None,
        progress: int | None = None,
        report_path: str | None = None,
        error: str | None = None,
    ) -> None:
        current = self.get_task(task_id)
        if not current:
            return
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE tasks
                SET status = ?, current_step = ?, progress = ?, report_path = ?,
                    error = ?, updated_at = ?
                WHERE task_id = ?
                """,
                (
                    status if status is not None else current["status"],
                    current_step if current_step is not None else current["current_step"],
                    progress if progress is not None else current["progress"],
                    report_path if report_path is not None else current["report_path"],
                    error if error is not None else current["error"],
                    utc_now(),
                    task_id,
                ),
            )

    def add_log(
        self,
        task_id: str,
        agent: str,
        status: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        with self.connect() as conn:
            if not self._task_exists(conn, task_id):
                return
            conn.execute(
                """
                INSERT INTO agent_logs (task_id, agent, status, message, payload, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (task_id, agent, status, message, json.dumps(payload or {}, ensure_ascii=False), utc_now()),
            )

    def get_logs(self, task_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM agent_logs WHERE task_id = ? ORDER BY id ASC",
                (task_id,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "agent": row["agent"],
                "status": row["status"],
                "message": row["message"],
                "payload": json.loads(row["payload"] or "{}"),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def replace_papers(self, task_id: str, papers: list[dict[str, Any]]) -> None:
        with self.connect() as conn:
            if not self._task_exists(conn, task_id):
                return
            conn.execute("DELETE FROM papers WHERE task_id = ?", (task_id,))
            conn.executemany(
                """
                INSERT INTO papers (
                    task_id, title, authors, year, source, abstract, url, relevance, summary
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        task_id,
                        paper["title"],
                        json.dumps(paper.get("authors", []), ensure_ascii=False),
                        paper.get("year"),
                        paper.get("source", "unknown"),
                        paper.get("abstract", ""),
                        paper.get("url"),
                        float(paper.get("relevance", 0)),
                        paper.get("summary"),
                    )
                    for paper in papers
                ],
            )

    def get_papers(self, task_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM papers WHERE task_id = ? ORDER BY relevance DESC, year DESC",
                (task_id,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "authors": json.loads(row["authors"] or "[]"),
                "year": row["year"],
                "source": row["source"],
                "abstract": row["abstract"],
                "url": row["url"],
                "relevance": row["relevance"],
                "summary": row["summary"],
            }
            for row in rows
        ]

    def set_evaluation(self, task_id: str, evaluation: dict[str, Any]) -> None:
        with self.connect() as conn:
            if not self._task_exists(conn, task_id):
                return
            conn.execute(
                """
                INSERT INTO evaluations (
                    task_id, relevance, citation, structure, faithfulness, overall, suggestions
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    relevance = excluded.relevance,
                    citation = excluded.citation,
                    structure = excluded.structure,
                    faithfulness = excluded.faithfulness,
                    overall = excluded.overall,
                    suggestions = excluded.suggestions
                """,
                (
                    task_id,
                    evaluation["relevance"],
                    evaluation["citation"],
                    evaluation["structure"],
                    evaluation["faithfulness"],
                    evaluation["overall"],
                    json.dumps(evaluation.get("suggestions", []), ensure_ascii=False),
                ),
            )

    def get_evaluation(self, task_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM evaluations WHERE task_id = ?", (task_id,)).fetchone()
        if not row:
            return None
        return {
            "relevance": row["relevance"],
            "citation": row["citation"],
            "structure": row["structure"],
            "faithfulness": row["faithfulness"],
            "overall": row["overall"],
            "suggestions": json.loads(row["suggestions"] or "[]"),
        }

    def hydrate_task(self, task_id: str) -> dict[str, Any] | None:
        task = self.get_task(task_id)
        if not task:
            return None
        task["agent_logs"] = self.get_logs(task_id)
        task["papers"] = self.get_papers(task_id)
        task["evaluation"] = self.get_evaluation(task_id)
        return task

    def _task_row(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "task_id": row["task_id"],
            "topic": row["topic"],
            "language": row["language"],
            "max_papers": row["max_papers"],
            "status": row["status"],
            "current_step": row["current_step"],
            "progress": row["progress"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "report_path": row["report_path"],
            "error": row["error"],
        }


db = Database()
