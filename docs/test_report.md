# Test Report

## 1. 测试目标

验证 ResearchPilot 的真实 API 工作流是否可运行，重点覆盖：

- 任务创建。
- LLM Provider 配置检查。
- Agent 工作流状态更新。
- SQLite 持久化。
- RAG 写入与检索。
- Markdown 报告生成。
- 报告质量评估。

## 2. 单元测试

```bash
cd src/api
pytest
```

当前测试：

- `tests/test_workflow.py`
  - 创建临时 SQLite 数据库。
  - 使用测试专用 Fake LLM 隔离真实模型费用和网络波动。
  - monkeypatch 论文检索函数以隔离外部论文源。
  - 验证任务完成、论文数量、报告文件和评估分数。

## 3. 集成测试流程

```text
POST /api/research-tasks
  -> LLM Planner
  -> external paper search
  -> LLM Reader
  -> RAG store
  -> LLM Synthesis
  -> LLM Writer
  -> LLM Evaluator
  -> GET /api/research-tasks/{task_id}
  -> GET /api/research-tasks/{task_id}/report
  -> POST /api/chat
```

## 4. 真实运行前置条件

- `.env` 中配置真实 LLM API。
- 当前环境可以访问 LLM Provider。
- 当前环境可以访问 OpenAlex 或 arXiv。

## 5. 后续测试计划

- 增加 API route 测试。
- 增加真实 OpenAlex 检索 stub。
- 增加前端 Playwright 冒烟测试。
- 引入 RAGAS 或 DeepEval 做报告事实一致性评估。
