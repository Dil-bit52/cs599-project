from __future__ import annotations

from typing import Any


def generate_report(
    *,
    topic: str,
    language: str,
    plan: dict[str, Any],
    papers: list[dict[str, Any]],
    synthesis: dict[str, str],
) -> str:
    if language == "en":
        return _generate_en(topic, plan, papers, synthesis)
    return _generate_zh(topic, plan, papers, synthesis)


def _generate_zh(topic: str, plan: dict[str, Any], papers: list[dict[str, Any]], synthesis: dict[str, str]) -> str:
    paper_lines = "\n".join(
        [
            f"### {idx}. {paper['title']}\n\n"
            f"- 作者：{', '.join(paper.get('authors') or ['Unknown'])}\n"
            f"- 年份：{paper.get('year') or 'N/A'}\n"
            f"- 来源：{paper.get('source')}\n"
            f"- 相关性：{paper.get('relevance', 0):.2f}\n"
            f"- Agent 总结：{paper.get('summary')}\n"
            f"- 链接：{paper.get('url') or 'N/A'}\n"
            for idx, paper in enumerate(papers, start=1)
        ]
    )
    questions = "\n".join([f"- {item}" for item in plan.get("research_questions", [])])
    references = "\n".join(
        [
            f"{idx}. {paper['title']}. {paper.get('authors', ['Unknown'])[0] if paper.get('authors') else 'Unknown'}, "
            f"{paper.get('year') or 'N/A'}. {paper.get('url') or ''}"
            for idx, paper in enumerate(papers, start=1)
        ]
    )
    return f"""# {topic} 研究报告

## 1. 摘要

本报告围绕“{topic}”展开自动化学术调研。ResearchPilot 通过 Planner、Search、Reader、Synthesis、Writer 和 Evaluator 多个 Agent 协作完成研究问题拆解、论文检索、文献总结、知识库构建、综述写作与质量评估。

## 2. 研究问题

{questions}

## 3. 研究背景

{synthesis.get("background")}

## 4. 代表性论文

{paper_lines}

## 5. 方法对比与技术趋势

{synthesis.get("comparison")}

{synthesis.get("trends")}

## 6. 局限性分析

{synthesis.get("limitations")}

## 7. 结论

围绕该主题，当前研究正在从单次检索增强生成转向具备主动规划、工具调用、反思评估和多步骤状态管理的 Agentic RAG 范式。后续系统可以进一步接入 PDF 全文解析、更多论文数据库、人工反馈学习和更严格的事实一致性评测。

## 8. 参考文献

{references}
"""


def _generate_en(topic: str, plan: dict[str, Any], papers: list[dict[str, Any]], synthesis: dict[str, str]) -> str:
    paper_lines = "\n".join(
        [
            f"### {idx}. {paper['title']}\n\n"
            f"- Authors: {', '.join(paper.get('authors') or ['Unknown'])}\n"
            f"- Year: {paper.get('year') or 'N/A'}\n"
            f"- Source: {paper.get('source')}\n"
            f"- Relevance: {paper.get('relevance', 0):.2f}\n"
            f"- Agent summary: {paper.get('summary')}\n"
            f"- URL: {paper.get('url') or 'N/A'}\n"
            for idx, paper in enumerate(papers, start=1)
        ]
    )
    questions = "\n".join([f"- {item}" for item in plan.get("research_questions", [])])
    references = "\n".join(
        [
            f"{idx}. {paper['title']}. {paper.get('authors', ['Unknown'])[0] if paper.get('authors') else 'Unknown'}, "
            f"{paper.get('year') or 'N/A'}. {paper.get('url') or ''}"
            for idx, paper in enumerate(papers, start=1)
        ]
    )
    return f"""# Research Report: {topic}

## 1. Abstract

This report surveys "{topic}" through an agentic research workflow. ResearchPilot coordinates Planner, Search, Reader, Synthesis, Writer, and Evaluator agents to decompose questions, retrieve papers, summarize evidence, build a local knowledge base, write a structured report, and score report quality.

## 2. Research Questions

{questions}

## 3. Background

{synthesis.get("background")}

## 4. Representative Papers

{paper_lines}

## 5. Method Comparison and Trends

{synthesis.get("comparison")}

{synthesis.get("trends")}

## 6. Limitations

{synthesis.get("limitations")}

## 7. Conclusion

The literature is moving from one-shot RAG pipelines toward agentic systems with planning, tool calling, reflection, and stateful evaluation. Future versions can add full-text PDF parsing, more paper sources, human feedback, and stricter faithfulness benchmarks.

## 8. References

{references}
"""

