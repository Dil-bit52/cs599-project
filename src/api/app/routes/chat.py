from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.llm.client import llm_client
from app.memory.database import db
from app.retrieval.vector_store import vector_store
from app.schemas import ChatRequest, ChatResponse, ChatSource


router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    task = db.get_task(payload.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    docs = vector_store.retrieve_documents(payload.task_id, payload.question, top_k=4)
    if not docs:
        return ChatResponse(
            answer="当前任务的知识库中没有检索到足够相关的论文证据。请先完成研究任务，或换一个更具体的问题。",
            sources=[],
        )

    if not llm_client.is_enabled():
        raise HTTPException(status_code=503, detail="No real LLM provider is configured.")

    evidence = "\n".join([f"- {doc['title']}: {doc.get('text', '')[:700]}" for doc in docs])
    try:
        answer = llm_client.complete(
            system=(
                "You are a knowledge-base QA agent. Answer using only the provided retrieved evidence. "
                "If evidence is insufficient, say so clearly. Include concise source mentions by title."
            ),
            user=f"Question: {payload.question}\n\nRetrieved evidence:\n{evidence}",
            max_tokens=900,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {exc}") from exc

    return ChatResponse(
        answer=answer,
        sources=[
            ChatSource(title=doc.get("title", ""), url=doc.get("url"), score=float(doc.get("score", 0)))
            for doc in docs
        ],
    )
