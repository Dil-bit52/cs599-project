"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { ExternalLink, MessageSquareText, Send } from "lucide-react";

import { askQuestion, listTasks, type ChatResponse, type ResearchTask } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/input";

export default function ChatPage() {
  const [tasks, setTasks] = useState<ResearchTask[]>([]);
  const [taskId, setTaskId] = useState("");
  const [question, setQuestion] = useState("Agentic RAG 和传统 RAG 有什么区别？");
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listTasks()
      .then((items) => {
        setTasks(items);
        const completed = items.find((item) => item.status === "completed");
        if (completed) setTaskId(completed.task_id);
      })
      .catch(() => setTasks([]));
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResponse(null);
    try {
      setResponse(await askQuestion(taskId, question));
    } catch (err) {
      setError(err instanceof Error ? err.message : "问答失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-5 lg:grid-cols-[0.8fr_1.2fr]">
      <Card>
        <CardHeader>
          <CardTitle>知识库问答</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <label className="text-sm font-medium">选择已完成任务</label>
              <select
                className="h-10 w-full rounded-md border border-border bg-white px-3 text-sm"
                value={taskId}
                onChange={(event) => setTaskId(event.target.value)}
              >
                <option value="">请选择任务</option>
                {tasks.map((task) => (
                  <option key={task.task_id} value={task.task_id}>
                    {task.topic} · {task.status}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">追问问题</label>
              <Textarea value={question} onChange={(event) => setQuestion(event.target.value)} />
            </div>
            {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
            <Button type="submit" disabled={!taskId || question.trim().length < 2 || loading}>
              <Send size={16} />
              {loading ? "检索中" : "提交问题"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center gap-2">
          <MessageSquareText size={18} />
          <CardTitle>回答与引用来源</CardTitle>
        </CardHeader>
        <CardContent>
          {!response ? (
            <p className="text-sm leading-7 text-muted-foreground">
              完成一个研究任务后，可以基于该任务写入的本地知识库继续提问。没有任务时请先回到 <Link className="font-medium text-primary" href="/">研究任务</Link> 创建任务。
            </p>
          ) : (
            <div className="space-y-5">
              <div className="whitespace-pre-wrap rounded-md border border-border bg-muted/35 p-4 text-sm leading-7">{response.answer}</div>
              <div className="space-y-2">
                <h3 className="text-sm font-semibold">Sources</h3>
                {response.sources.map((source) => (
                  <div key={`${source.title}-${source.score}`} className="flex items-center justify-between gap-3 rounded-md border border-border bg-white p-3">
                    <div>
                      <div className="text-sm font-medium">{source.title}</div>
                      <div className="text-xs text-muted-foreground">score: {source.score.toFixed(3)}</div>
                    </div>
                    {source.url && (
                      <a href={source.url} target="_blank" className="text-primary">
                        <ExternalLink size={16} />
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
