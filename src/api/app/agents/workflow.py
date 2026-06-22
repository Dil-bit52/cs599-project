from __future__ import annotations

import time
import re
from pathlib import Path
from typing import Any

from app.config import settings
from app.llm.client import LLMClient, llm_client, parse_json_object
from app.memory.database import Database, db
from app.retrieval.vector_store import HybridVectorStore, vector_store
from app.tools.papers import search_papers


class ResearchWorkflow:
    def __init__(
        self,
        database: Database | None = None,
        store: HybridVectorStore | None = None,
        reports_dir: Path | None = None,
        llm: LLMClient | None = None,
    ) -> None:
        self.db = database or db
        self.store = store or vector_store
        self.reports_dir = reports_dir or settings.reports_dir
        self.llm = llm or llm_client

    def run(self, task_id: str) -> None:
        task = self.db.get_task(task_id)
        if not task:
            return

        try:
            if not self.llm.is_enabled():
                raise RuntimeError("No real LLM provider is configured. Set LLM_PROVIDER and the matching API credentials in .env.")

            self.db.add_log(
                task_id,
                "LLM Provider",
                "enabled",
                f"Using real LLM provider: {self.llm.provider_name()}.",
            )

            self.db.update_task(task_id, status="running", current_step="planner", progress=5)
            plan = self._planner(task_id, task["topic"], task["language"])

            self.db.update_task(task_id, current_step="search", progress=20)
            papers = self._search(task_id, task["topic"], plan["keywords"], task["max_papers"])

            self.db.update_task(task_id, current_step="reader", progress=42)
            papers = self._reader(task_id, task["topic"], task["language"], papers)
            self.db.replace_papers(task_id, papers)

            self.db.update_task(task_id, current_step="rag_store", progress=58)
            self._rag_store(task_id, papers)

            self.db.update_task(task_id, current_step="synthesis", progress=70)
            synthesis = self._synthesis(task_id, task["topic"], task["language"], papers)

            self.db.update_task(task_id, current_step="writer", progress=82)
            report_path, report = self._writer(task_id, task, plan, papers, synthesis)

            self.db.update_task(task_id, current_step="evaluator", progress=92)
            evaluation = self._evaluator(task_id, task["topic"], task["language"], report, papers)
            self.db.set_evaluation(task_id, evaluation)

            self.db.update_task(
                task_id,
                status="completed",
                current_step="completed",
                progress=100,
                report_path=str(report_path),
            )
            self.db.add_log(task_id, "Workflow", "completed", "Research workflow completed.", {"progress": 100})
        except Exception as exc:
            self.db.update_task(task_id, status="failed", current_step="failed", error=str(exc))
            self.db.add_log(task_id, "Workflow", "failed", f"Workflow failed: {exc}")

    def _planner(self, task_id: str, topic: str, language: str) -> dict[str, Any]:
        planner_text = self.llm.complete_json_text(
            system=(
                "You are Planner Agent for an academic research assistant. "
                "Return compact strict JSON only. No Markdown. No explanation. "
                "Keys: keywords, research_questions, outline. "
                "Each value must be a short array of strings."
            ),
            user=(
                f"Topic: {topic}\n"
                f"Output language: {'English' if language == 'en' else 'Chinese'}\n"
                "Create exactly 6 search keywords, exactly 3 research questions, and exactly 6 outline titles. "
                "Keep every string under 12 words. "
                "Search keywords must be suitable for OpenAlex and arXiv. "
                "If the topic contains Chinese or a system name, include English academic keywords and expanded technical terms."
            ),
            max_tokens=700,
        )
        plan = parse_json_object(planner_text) or self._parse_partial_plan(planner_text)
        normalized = {
            "keywords": self._ensure_list(plan.get("keywords"), self._default_keywords(topic))[:8],
            "research_questions": self._ensure_list(plan.get("research_questions"), self._default_questions(topic, language))[:5],
            "outline": self._ensure_list(plan.get("outline"), self._default_outline(language))[:8],
        }
        self.db.add_log(task_id, "Planner Agent", "completed", "Generated research plan with the configured LLM.", normalized)
        time.sleep(0.2)
        return normalized

    def _search(self, task_id: str, topic: str, keywords: list[str], max_papers: int) -> list[dict[str, Any]]:
        papers = search_papers(topic, keywords=keywords, max_papers=max_papers)
        self.db.add_log(
            task_id,
            "Search Agent",
            "completed",
            f"Retrieved {len(papers)} candidate papers from external sources.",
            {
                "queries": [topic, *keywords[:5]],
                "sources": sorted({paper.get("source", "unknown") for paper in papers}),
            },
        )
        time.sleep(0.2)
        return papers

    def _reader(
        self,
        task_id: str,
        topic: str,
        language: str,
        papers: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        summarized: list[dict[str, Any]] = []
        for paper in papers:
            item = dict(paper)
            item["summary"] = self.llm.complete(
                system=(
                    "You are Reader Agent. Summarize one academic paper for a literature review. "
                    "Focus on contribution, method, relevance to the topic, and limitation. "
                    "Do not invent details beyond title and abstract."
                ),
                user=(
                    f"Topic: {topic}\n"
                    f"Output language: {'English' if language == 'en' else 'Chinese'}\n"
                    f"Title: {item.get('title')}\n"
                    f"Authors: {', '.join(item.get('authors') or [])}\n"
                    f"Year: {item.get('year')}\n"
                    f"Abstract: {item.get('abstract')}"
                ),
                max_tokens=320,
            )
            summarized.append(item)
        self.db.add_log(task_id, "Reader Agent", "completed", f"Summarized {len(papers)} papers with the configured LLM.")
        time.sleep(0.2)
        return summarized

    def _rag_store(self, task_id: str, papers: list[dict[str, Any]]) -> None:
        self.store.store_documents(task_id, papers)
        self.db.add_log(task_id, "RAG Store", "completed", "Stored paper metadata and summaries in the local retrieval index.")
        time.sleep(0.2)

    def _synthesis(
        self,
        task_id: str,
        topic: str,
        language: str,
        papers: list[dict[str, Any]],
    ) -> dict[str, str]:
        synthesis_text = self.llm.complete(
            system=(
                "You are Synthesis Agent. Compare academic papers and synthesize evidence. "
                "Do not use JSON. Use exactly these four Markdown headings: "
                "## Background, ## Comparison, ## Trends, ## Limitations. "
                "Ground every claim in the provided paper metadata and summaries."
            ),
            user=(
                f"Topic: {topic}\n"
                f"Output language: {'English' if language == 'en' else 'Chinese'}\n\n"
                f"Papers:\n{self._papers_brief(papers)}"
            ),
            max_tokens=1400,
        )
        normalized = self._parse_synthesis_text(synthesis_text)
        normalized = self._complete_synthesis_sections(normalized, synthesis_text)
        self.db.add_log(task_id, "Synthesis Agent", "completed", "Synthesized paper evidence with the configured LLM.", normalized)
        time.sleep(0.2)
        return normalized

    def _writer(
        self,
        task_id: str,
        task: dict[str, Any],
        plan: dict[str, Any],
        papers: list[dict[str, Any]],
        synthesis: dict[str, str],
    ) -> tuple[Path, str]:
        report = self.llm.complete(
            system=(
                "You are Writer Agent for an academic research assistant. "
                "Write a structured Markdown literature review. "
                "Use only the provided plan, synthesis, papers, summaries, URLs, and years. "
                "Must include sections: abstract, research background, representative papers, method comparison, trends, limitations, conclusion, references. "
                "References must preserve paper titles and URLs."
            ),
            user=(
                f"Topic: {task['topic']}\n"
                f"Output language: {'English' if task['language'] == 'en' else 'Chinese'}\n"
                f"Plan: {plan}\n"
                f"Synthesis: {synthesis}\n"
                f"Papers:\n{self._papers_brief(papers)}"
            ),
            max_tokens=3200,
        )
        path = self.reports_dir / f"{task_id}.md"
        path.write_text(report, encoding="utf-8")
        self.db.add_log(task_id, "Writer Agent", "completed", "Generated and saved a Markdown research report.", {"report_path": str(path)})
        time.sleep(0.2)
        return path, report

    def _evaluator(
        self,
        task_id: str,
        topic: str,
        language: str,
        report: str,
        papers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        evaluation = self.llm.complete_json(
            system=(
                "You are Evaluator Agent. Score a research report and return strict JSON only. "
                "Required numeric keys from 0 to 10: relevance, citation, structure, faithfulness, overall. "
                "Required key suggestions: array of short strings."
            ),
            user=(
                f"Topic: {topic}\n"
                f"Output language for suggestions: {'English' if language == 'en' else 'Chinese'}\n"
                f"Available paper count: {len(papers)}\n"
                f"Report:\n{report[:7000]}"
            ),
            max_tokens=900,
        )
        normalized = self._normalize_evaluation(evaluation)
        self.db.add_log(task_id, "Evaluator Agent", "completed", "Scored report quality with the configured LLM.", normalized)
        time.sleep(0.2)
        return normalized

    def _papers_brief(self, papers: list[dict[str, Any]]) -> str:
        chunks: list[str] = []
        for idx, paper in enumerate(papers, start=1):
            chunks.append(
                "\n".join(
                    [
                        f"[{idx}] Title: {paper.get('title')}",
                        f"Authors: {', '.join(paper.get('authors') or ['Unknown'])}",
                        f"Year: {paper.get('year') or 'N/A'}",
                        f"Source: {paper.get('source')}",
                        f"URL: {paper.get('url') or 'N/A'}",
                        f"Abstract: {(paper.get('abstract') or '')[:900]}",
                        f"Agent summary: {(paper.get('summary') or '')[:600]}",
                    ]
                )
            )
        return "\n\n".join(chunks)

    def _parse_partial_plan(self, text: str) -> dict[str, Any]:
        return {
            "keywords": self._extract_json_array(text, "keywords"),
            "research_questions": self._extract_json_array(text, "research_questions"),
            "outline": self._extract_json_array(text, "outline"),
        }

    def _extract_json_array(self, text: str, key: str) -> list[str]:
        match = re.search(rf'"{re.escape(key)}"\s*:\s*\[(.*?)\]', text, flags=re.DOTALL)
        if not match:
            return []
        values = re.findall(r'"([^"]+)"', match.group(1))
        return [value.strip() for value in values if value.strip()]

    def _parse_synthesis_text(self, text: str) -> dict[str, str]:
        parsed_json = parse_json_object(text)
        if parsed_json:
            return {
                "background": str(parsed_json.get("background") or ""),
                "comparison": str(parsed_json.get("comparison") or ""),
                "trends": str(parsed_json.get("trends") or ""),
                "limitations": str(parsed_json.get("limitations") or ""),
            }

        sections = self._split_markdown_sections(text)
        if sections:
            return {
                "background": sections.get("background", ""),
                "comparison": sections.get("comparison", ""),
                "trends": sections.get("trends", ""),
                "limitations": sections.get("limitations", ""),
            }

        loose = self._parse_loose_synthesis_object(text)
        if any(loose.values()):
            return loose

        return {
            "background": text.strip(),
            "comparison": "",
            "trends": "",
            "limitations": "",
        }

    def _complete_synthesis_sections(self, sections: dict[str, str], raw_text: str) -> dict[str, str]:
        cleaned_raw = raw_text.strip()
        background = sections.get("background", "").strip() or cleaned_raw
        comparison = sections.get("comparison", "").strip() or (
            "The retrieved papers should be compared by their sensing modality, loop-closure trigger, "
            "matching strategy, and robustness assumptions."
        )
        trends = sections.get("trends", "").strip() or (
            "The main trend is to combine geometric matching, learned place recognition, and graph optimization "
            "to improve long-term localization robustness."
        )
        limitations = sections.get("limitations", "").strip() or (
            "The available evidence may be limited by metadata-only retrieval and lack of full-text experimental details."
        )
        return {
            "background": background,
            "comparison": comparison,
            "trends": trends,
            "limitations": limitations,
        }

    def _split_markdown_sections(self, text: str) -> dict[str, str]:
        aliases = {
            "background": "background",
            "研究背景": "background",
            "comparison": "comparison",
            "方法对比": "comparison",
            "trends": "trends",
            "技术趋势": "trends",
            "趋势": "trends",
            "limitations": "limitations",
            "局限性": "limitations",
            "局限": "limitations",
        }
        matches = list(re.finditer(r"^#{1,3}\s*(.+?)\s*$", text, flags=re.MULTILINE))
        sections: dict[str, str] = {}
        for index, match in enumerate(matches):
            raw_title = match.group(1).strip().lower()
            canonical = aliases.get(raw_title)
            if not canonical:
                continue
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            sections[canonical] = text[start:end].strip()
        return sections

    def _parse_loose_synthesis_object(self, text: str) -> dict[str, str]:
        result = {"background": "", "comparison": "", "trends": "", "limitations": ""}
        keys = list(result.keys())
        for index, key in enumerate(keys):
            next_keys = "|".join(keys[index + 1 :])
            if next_keys:
                pattern = rf'"?{key}"?\s*:\s*(.*?)(?=,\s*"?(?:{next_keys})"?\s*:|}}\s*$)'
            else:
                pattern = rf'"?{key}"?\s*:\s*(.*?)(?=}}\s*$|$)'
            match = re.search(pattern, text, flags=re.DOTALL)
            if match:
                value = match.group(1).strip().strip(",").strip()
                result[key] = value.strip('"').strip()
        return result

    def _ensure_list(self, value: Any, defaults: list[str]) -> list[str]:
        if isinstance(value, list):
            strings = [str(item).strip() for item in value if str(item).strip()]
            if strings:
                return strings
        return defaults

    def _default_keywords(self, topic: str) -> list[str]:
        topic_lower = topic.lower()
        defaults = [
            topic,
            "loop closure detection",
            "LiDAR SLAM",
            "LiDAR inertial odometry",
            "place recognition",
            "graph SLAM loop closure",
        ]
        if "lio" in topic_lower:
            defaults.insert(1, "LiDAR inertial odometry loop closure")
        return defaults

    def _default_questions(self, topic: str, language: str) -> list[str]:
        if language == "en":
            return [
                f"What is the core problem in {topic}?",
                "Which loop closure methods are most relevant?",
                "What limitations remain in current systems?",
            ]
        return [
            f"{topic} 的核心技术问题是什么？",
            "相关回环检测方法如何提升定位精度？",
            "当前方法还存在哪些局限？",
        ]

    def _default_outline(self, language: str) -> list[str]:
        if language == "en":
            return ["Abstract", "Background", "Representative Papers", "Method Comparison", "Limitations", "Conclusion"]
        return ["摘要", "研究背景", "代表性论文", "方法对比", "局限性", "结论"]

    def _normalize_evaluation(self, value: dict[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        for key in ("relevance", "citation", "structure", "faithfulness", "overall"):
            try:
                normalized[key] = round(max(0.0, min(10.0, float(value[key]))), 1)
            except (KeyError, TypeError, ValueError) as exc:
                raise RuntimeError(f"Evaluator Agent returned invalid score for {key}.") from exc
        suggestions = value.get("suggestions")
        if not isinstance(suggestions, list):
            raise RuntimeError("Evaluator Agent returned invalid suggestions.")
        normalized["suggestions"] = [str(item).strip() for item in suggestions if str(item).strip()][:5]
        return normalized


workflow = ResearchWorkflow()
