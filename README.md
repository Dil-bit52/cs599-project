# ResearchPilot: Agentic AI Research Assistant

ResearchPilot 是一个面向学术调研场景的 Agentic AI 原生系统。用户输入研究主题后，系统会自动完成研究问题拆解、论文检索、论文摘要阅读、任务级知识库构建、综述报告生成、引用证据展示和报告质量评估。

## 项目简介

本项目解决传统学术调研中“检索耗时、阅读分散、证据难追踪、报告质量不稳定”的问题，将学术调研流程拆解为多个可观测 Agent 节点，并通过 Web 控制台展示任务进度、论文结果、报告内容和评估分数。

## 方向

方向一：Agentic AI 原生开发。

本项目从零构建一个具备实际价值的学术调研 Agent 系统，覆盖 SDD 规格驱动开发、工具调用 / MCP、任务记忆、RAG 检索、多步骤状态流转、多 Agent 协作和可观测评估。

## 技术栈

- AI IDE: Trae CN / Codex
- LLM: DeepSeek API 或 OpenAI-compatible API
- Frontend: Next.js, React, TypeScript, Tailwind CSS, shadcn/ui 风格组件
- Backend: FastAPI, Pydantic, SQLite
- Agent Workflow: Planner, Search, Reader, RAG Store, Synthesis, Writer, Evaluator
- Tool Layer: Python MCP Server, Function Calling 风格工具封装
- RAG: Chroma 优先，JSON 词法检索回退
- Paper Sources: OpenAlex, arXiv
- Infrastructure: Docker Compose, Git, 环境变量配置
- Evaluation: pytest, Agent 行为日志, 报告质量评分

## 核心功能

- 创建学术调研任务，配置语言和最大论文数量
- Planner Agent 生成关键词、研究问题和报告大纲
- Search Agent 调用论文检索工具，从 OpenAlex / arXiv 获取候选论文
- Reader Agent 基于论文标题、摘要和元数据总结贡献、方法与局限
- RAG Store 将论文元数据和 Agent 总结写入本地知识库
- Synthesis Agent 横向归纳方法对比、技术趋势和研究不足
- Writer Agent 生成 Markdown 研究报告
- Evaluator Agent 从相关性、引用完整性、结构清晰度、事实一致性给出质量评分
- Web 前端展示 Agent 执行轨迹、论文卡片、报告预览、质量评估和知识库问答
- 支持删除最近任务，并同步清理任务记录、论文、日志、评估、报告文件和 RAG 索引

## 目录结构

```text
cs599-project/
├── docs/
│   ├── CS599_大作业报告.pdf      # 最终课程报告
│   ├── CS599_大作业报告.md       # 报告源文件
│   ├── product_spec.md           # Product Spec
│   ├── architecture_spec.md      # Architecture Spec
│   ├── architecture.md           # 图文架构说明
│   ├── api_spec.md               # API Spec
│   └── test_report.md            # 测试说明
├── scripts/
│   └── build_cs599_report_pdf.py # 报告 PDF 生成脚本
├── src/
│   ├── api/
│   │   ├── app/
│   │   │   ├── agents/           # Agent 工作流与节点实现
│   │   │   ├── evaluation/       # 报告评分逻辑
│   │   │   ├── llm/              # DeepSeek / OpenAI-compatible LLM 接入
│   │   │   ├── mcp_server/       # MCP 工具服务
│   │   │   ├── memory/           # SQLite 任务记忆与日志
│   │   │   ├── reporting/        # Markdown 报告生成
│   │   │   ├── retrieval/        # Chroma / JSON RAG 检索
│   │   │   ├── routes/           # FastAPI REST API
│   │   │   └── tools/            # OpenAlex / arXiv 论文检索工具
│   │   └── tests/                # 后端单元测试
│   └── web/
│       ├── app/                  # Next.js App Router 页面
│       ├── components/           # 任务输入、时间线、论文卡片、报告预览、评分面板
│       └── lib/                  # 前端 API client
├── data/                         # 本地运行数据，已在 .gitignore 中排除
├── docker-compose.yml
├── .env.example
├── .gitignore
└── LICENSE
```

## 环境搭建

### 1. 后端依赖安装

```bash
cd src/api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

如需运行 MCP Server、Chroma 或 LangGraph 扩展，可继续安装可选依赖：

```bash
pip install -r requirements-optional.txt
```

### 2. 前端依赖安装

```bash
cd src/web
npm install
```

### 3. 环境变量配置

复制 `.env.example` 为 `.env`。不要把真实 API Key 提交到 GitHub。

```bash
copy .env.example .env
```

OpenAI-compatible Provider 示例：

```env
LLM_PROVIDER=openai_compatible
OPENAI_COMPATIBLE_BASE_URL=https://token.sensenova.cn/v1
OPENAI_COMPATIBLE_API_KEY=your_api_key_here
OPENAI_COMPATIBLE_MODEL=sensenova-6.7-flash-lite
```

DeepSeek 示例：

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
```

说明：

- 本项目当前要求配置真实 LLM API。
- 如果 API Key 缺失、论文源不可访问或 LLM 调用失败，任务会进入 `failed` 状态，错误原因会显示在任务详情页的 Agent 日志中。
- 真实 API Key 只允许放在本地 `.env` 中，不得写入代码、README 或报告。

## 启动步骤

### 启动后端

```bash
cd src/api
.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

FastAPI 文档地址：

```text
http://localhost:8000/docs
```

### 启动前端

```bash
cd src/web
npm run dev
```

前端地址：

```text
http://localhost:3000
```

### Docker Compose 启动

```bash
docker compose up --build
```

## API 概览

```http
POST   /api/research-tasks
GET    /api/research-tasks
GET    /api/research-tasks/{task_id}
DELETE /api/research-tasks/{task_id}
GET    /api/research-tasks/{task_id}/papers
GET    /api/research-tasks/{task_id}/report
GET    /api/research-tasks/{task_id}/report/download
POST   /api/chat
```

创建任务示例：

```json
{
  "topic": "Agentic RAG 在企业知识库中的应用",
  "language": "zh",
  "max_papers": 8
}
```

知识库问答示例：

```json
{
  "task_id": "task_xxx",
  "question": "Agentic RAG 和传统 RAG 有什么区别？"
}
```

## Agent 工作流

```text
用户输入主题
  -> Planner Agent：拆解主题，生成关键词、研究问题和报告大纲
  -> Search Agent：调用 OpenAlex / arXiv 检索候选论文
  -> Reader Agent：阅读标题、摘要和元数据，生成论文总结
  -> RAG Store：写入任务级本地知识库
  -> Synthesis Agent：归纳方法对比、趋势和局限
  -> Writer Agent：生成 Markdown 研究报告
  -> Evaluator Agent：输出质量评分和改进建议
  -> Web UI：展示轨迹、论文、报告、评分和问答
```

## 测试

后端测试：

```bash
cd src/api
pytest
```

前端构建验证：

```bash
cd src/web
npm run build
```

当前测试覆盖：

- LLM 客户端空响应重试
- 多 Agent 工作流闭环
- 删除任务时清理关联记录
- 删除任务时清理本地 RAG 索引

## 报告生成

最终报告文件位于：

```text
docs/CS599_大作业报告.pdf
```

如果修改了 `docs/CS599_大作业报告.md` 中的姓名、学号、专业或正文内容，可以重新生成 PDF：

```bash
cd src/api
.venv\Scripts\activate
pip install -r requirements-optional.txt
cd ..\..
python scripts/build_cs599_report_pdf.py
```

生成脚本会为 PDF 写入导航书签和目录页。

## 项目状态

- [x] Proposal
- [x] Product / Architecture / API Specs
- [x] FastAPI 后端
- [x] Next.js 前端
- [x] OpenAI-compatible LLM integration
- [x] MCP 工具层
- [x] RAG 本地知识库
- [x] Agent 执行轨迹与评估
- [x] Final PDF report

## 学术与安全说明

- 本项目使用 OpenAlex、arXiv 公开元数据接口作为论文检索来源。
- 本项目引用的开源框架包括 FastAPI、Next.js、React、Tailwind CSS、OpenAI Python SDK、pytest、Chroma、MCP 等。
- API Key 必须通过环境变量配置，不得硬编码在代码、README 或报告中。
- 如果仓库为 Private Repository，请添加 `qxr777` 为 Collaborator。
- 如果仓库为 Public Repository，请保留 LICENSE 文件。
