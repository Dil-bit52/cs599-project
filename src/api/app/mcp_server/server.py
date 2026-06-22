from __future__ import annotations

from app.evaluation.scoring import evaluate_report
from app.retrieval.vector_store import vector_store
from app.reporting.markdown import generate_report
from app.tools.papers import fetch_paper_detail, search_papers


try:
    from mcp.server.fastmcp import FastMCP
except Exception:  # pragma: no cover - optional runtime dependency
    FastMCP = None  # type: ignore


if FastMCP is not None:
    mcp = FastMCP("researchpilot-tools")

    @mcp.tool()
    def search_papers_tool(topic: str, keywords: list[str] | None = None, max_papers: int = 8) -> list[dict]:
        return search_papers(topic, keywords=keywords, max_papers=max_papers)

    @mcp.tool()
    def fetch_paper_detail_tool(url: str) -> dict:
        return fetch_paper_detail(url)

    @mcp.tool()
    def store_documents_tool(task_id: str, papers: list[dict]) -> str:
        vector_store.store_documents(task_id, papers)
        return "stored"

    @mcp.tool()
    def retrieve_documents_tool(task_id: str, query: str, top_k: int = 4) -> list[dict]:
        return vector_store.retrieve_documents(task_id, query, top_k=top_k)

    @mcp.tool()
    def write_report_tool(topic: str, language: str, plan: dict, papers: list[dict], synthesis: dict) -> str:
        return generate_report(topic=topic, language=language, plan=plan, papers=papers, synthesis=synthesis)

    @mcp.tool()
    def evaluate_report_tool(topic: str, report: str, papers: list[dict]) -> dict:
        return evaluate_report(topic, report, papers)


def main() -> None:
    if FastMCP is None:
        raise RuntimeError("Install the optional 'mcp' package to run the MCP server.")
    mcp.run()


if __name__ == "__main__":
    main()
