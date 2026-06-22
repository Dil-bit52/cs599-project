from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from app.config import settings


class HybridVectorStore:
    """Chroma-backed store when available, lexical JSON store otherwise."""

    def __init__(self, cache_path: Path | None = None) -> None:
        self.cache_path = cache_path or (settings.cache_dir / "vector_store.json")
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._chroma = None
        try:
            import chromadb  # type: ignore

            self._chroma = chromadb.PersistentClient(path=str(settings.chroma_dir))
        except Exception:
            self._chroma = None

    def store_documents(self, task_id: str, papers: list[dict[str, Any]]) -> None:
        data = self._load()
        data[task_id] = [
            {
                "title": paper.get("title", ""),
                "text": self._paper_text(paper),
                "url": paper.get("url"),
                "summary": paper.get("summary"),
            }
            for paper in papers
        ]
        self.cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        if self._chroma is not None:
            collection = self._chroma.get_or_create_collection(name="researchpilot_papers")
            ids = [f"{task_id}_{idx}" for idx, _ in enumerate(papers)]
            collection.upsert(
                ids=ids,
                documents=[self._paper_text(paper) for paper in papers],
                metadatas=[
                    {
                        "task_id": task_id,
                        "title": paper.get("title", ""),
                        "url": paper.get("url") or "",
                    }
                    for paper in papers
                ],
            )

    def delete_documents(self, task_id: str) -> None:
        data = self._load()
        if task_id in data:
            del data[task_id]
            self.cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        if self._chroma is not None:
            try:
                collection = self._chroma.get_or_create_collection(name="researchpilot_papers")
                collection.delete(where={"task_id": task_id})
            except Exception:
                pass

    def retrieve_documents(self, task_id: str, query: str, top_k: int = 4) -> list[dict[str, Any]]:
        if self._chroma is not None:
            try:
                collection = self._chroma.get_or_create_collection(name="researchpilot_papers")
                result = collection.query(
                    query_texts=[query],
                    n_results=top_k,
                    where={"task_id": task_id},
                )
                documents = result.get("documents", [[]])[0]
                metadatas = result.get("metadatas", [[]])[0]
                distances = result.get("distances", [[]])[0] if result.get("distances") else []
                return [
                    {
                        "title": metadata.get("title", ""),
                        "text": document,
                        "url": metadata.get("url"),
                        "score": round(1 / (1 + (distances[idx] if idx < len(distances) else 0)), 3),
                    }
                    for idx, (document, metadata) in enumerate(zip(documents, metadatas))
                ]
            except Exception:
                pass

        docs = self._load().get(task_id, [])
        scored = [
            {
                **doc,
                "score": self._lexical_score(query, f"{doc.get('title', '')} {doc.get('text', '')}"),
            }
            for doc in docs
        ]
        return [doc for doc in sorted(scored, key=lambda item: item["score"], reverse=True)[:top_k] if doc["score"] > 0]

    def _load(self) -> dict[str, list[dict[str, Any]]]:
        if not self.cache_path.exists():
            return {}
        try:
            return json.loads(self.cache_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _paper_text(self, paper: dict[str, Any]) -> str:
        return "\n".join(
            [
                f"Title: {paper.get('title', '')}",
                f"Abstract: {paper.get('abstract', '')}",
                f"Agent summary: {paper.get('summary', '')}",
            ]
        )

    def _lexical_score(self, query: str, text: str) -> float:
        q_terms = self._terms(query)
        t_terms = self._terms(text)
        if not q_terms or not t_terms:
            return 0.0
        tf = {term: t_terms.count(term) for term in set(t_terms)}
        score = sum(1 + math.log(tf.get(term, 0)) for term in set(q_terms) if tf.get(term, 0) > 0)
        return round(min(score / max(len(set(q_terms)), 1), 1.0), 3)

    def _terms(self, text: str) -> list[str]:
        return re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}|[\u4e00-\u9fff]{2,}", text.lower())


vector_store = HybridVectorStore()
