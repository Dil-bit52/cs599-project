from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.agents.workflow import workflow
from app.config import settings
from app.memory.database import db
from app.retrieval.vector_store import vector_store
from app.schemas import ReportResponse, ResearchTask, ResearchTaskCreate, ResearchTaskCreated, ResearchTaskDeleted


router = APIRouter(prefix="/api/research-tasks", tags=["research-tasks"])
executor = ThreadPoolExecutor(max_workers=2)


@router.post("", response_model=ResearchTaskCreated)
def create_research_task(payload: ResearchTaskCreate) -> ResearchTaskCreated:
    task_id = db.create_task(
        topic=payload.topic,
        language=payload.language,
        max_papers=payload.max_papers,
    )
    executor.submit(workflow.run, task_id)
    return ResearchTaskCreated(task_id=task_id, status="created")


@router.get("", response_model=list[ResearchTask])
def list_research_tasks() -> list[ResearchTask]:
    return [ResearchTask(**task, agent_logs=[], papers=[], evaluation=None) for task in db.list_tasks()]


@router.get("/{task_id}", response_model=ResearchTask)
def get_research_task(task_id: str) -> ResearchTask:
    task = db.hydrate_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return ResearchTask(**task)


@router.delete("/{task_id}", response_model=ResearchTaskDeleted)
def delete_research_task(task_id: str) -> ResearchTaskDeleted:
    task = db.delete_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    vector_store.delete_documents(task_id)
    _delete_report_file(task.get("report_path"))
    return ResearchTaskDeleted(task_id=task_id, deleted=True)


@router.get("/{task_id}/papers")
def get_papers(task_id: str) -> list[dict]:
    if not db.get_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return db.get_papers(task_id)


@router.get("/{task_id}/report", response_model=ReportResponse)
def get_report(task_id: str) -> ReportResponse:
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not task.get("report_path"):
        raise HTTPException(status_code=404, detail="Report is not ready")
    path = Path(task["report_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    return ReportResponse(task_id=task_id, format="markdown", content=path.read_text(encoding="utf-8"))


@router.get("/{task_id}/report/download")
def download_report(task_id: str) -> FileResponse:
    task = db.get_task(task_id)
    if not task or not task.get("report_path"):
        raise HTTPException(status_code=404, detail="Report is not ready")
    path = Path(task["report_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    return FileResponse(path, filename=f"{task_id}_research_report.md", media_type="text/markdown")


def _delete_report_file(report_path: str | None) -> None:
    if not report_path:
        return

    path = Path(report_path).resolve()
    reports_dir = settings.reports_dir.resolve()
    if path.is_file() and path.is_relative_to(reports_dir):
        path.unlink()
