# API Spec: ResearchPilot

## 1. Create Research Task

```http
POST /api/research-tasks
```

Request:

```json
{
  "topic": "Agentic RAG 在企业知识库中的应用",
  "language": "zh",
  "max_papers": 8
}
```

Response:

```json
{
  "task_id": "task_xxx",
  "status": "created"
}
```

## 2. List Tasks

```http
GET /api/research-tasks
```

## 3. Get Task Detail

```http
GET /api/research-tasks/{task_id}
```

Response includes:

- task metadata
- status
- current_step
- progress
- agent_logs
- papers
- evaluation

## 4. Delete Task

```http
DELETE /api/research-tasks/{task_id}
```

Response:

```json
{
  "task_id": "task_xxx",
  "deleted": true
}
```

说明：删除任务时会同步清理任务记录、论文记录、Agent 日志、评估结果、报告文件和本地 RAG 索引。

## 5. Get Papers

```http
GET /api/research-tasks/{task_id}/papers
```

## 6. Get Report

```http
GET /api/research-tasks/{task_id}/report
```

Response:

```json
{
  "task_id": "task_xxx",
  "format": "markdown",
  "content": "# Research Report ..."
}
```

## 7. Download Report

```http
GET /api/research-tasks/{task_id}/report/download
```

Returns a Markdown file.

## 8. Knowledge Base Chat

```http
POST /api/chat
```

Request:

```json
{
  "task_id": "task_xxx",
  "question": "Agentic RAG 和传统 RAG 有什么区别？"
}
```

Response:

```json
{
  "answer": "基于当前任务知识库...",
  "sources": [
    {
      "title": "Self-RAG...",
      "url": "https://...",
      "score": 0.82
    }
  ]
}
```
