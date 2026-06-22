"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Activity, ArrowRight, Database, GitBranch, KeyRound, Trash2 } from "lucide-react";

import { deleteTask, listTasks, type ResearchTask } from "@/lib/api";
import { TopicInputCard } from "@/components/TopicInputCard";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function HomePage() {
  const router = useRouter();
  const [tasks, setTasks] = useState<ResearchTask[]>([]);
  const [deletingTaskId, setDeletingTaskId] = useState<string | null>(null);

  useEffect(() => {
    listTasks().then(setTasks).catch(() => setTasks([]));
  }, []);

  async function handleDeleteTask(task: ResearchTask) {
    const confirmed = window.confirm(
      `确认删除研究任务「${task.topic}」吗？相关论文、执行日志、评估结果和报告文件也会一起删除。`
    );
    if (!confirmed) {
      return;
    }

    setDeletingTaskId(task.task_id);
    try {
      await deleteTask(task.task_id);
      setTasks((current) => current.filter((item) => item.task_id !== task.task_id));
    } catch (error) {
      window.alert(error instanceof Error ? error.message : "删除任务失败，请查看后端日志。");
    } finally {
      setDeletingTaskId(null);
    }
  }

  return (
    <div className="space-y-8">
      <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-6">
          <div className="max-w-3xl">
            <Badge className="border-emerald-200 bg-emerald-50 text-emerald-700">CS599 Agentic AI 原生开发</Badge>
            <h1 className="mt-5 text-4xl font-semibold leading-tight tracking-normal md:text-5xl">
              ResearchPilot
            </h1>
            <p className="mt-4 text-lg leading-8 text-muted-foreground">
              面向学术调研场景的 Agentic AI 系统，自动完成研究问题拆解、论文检索、文献总结、RAG 知识库构建、综述报告生成和质量评估。
            </p>
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            <Capability icon={<GitBranch size={18} />} title="LangGraph 工作流" text="Planner、Search、Reader、Writer、Evaluator 多节点协作" />
            <Capability icon={<Database size={18} />} title="Agentic RAG" text="论文元数据和 Agent 总结写入本地检索索引" />
            <Capability icon={<KeyRound size={18} />} title="真实 API 驱动" text="Planner、Reader、Writer 等节点依赖已配置的 LLM API" />
          </div>
        </div>
        <TopicInputCard onCreated={(taskId) => router.push(`/tasks/${taskId}`)} />
      </section>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>最近任务</CardTitle>
          <Activity size={18} className="text-muted-foreground" />
        </CardHeader>
        <CardContent>
          {tasks.length === 0 ? (
            <p className="text-sm text-muted-foreground">暂无任务。请先确认后端 `.env` 已配置 LLM API，然后创建研究任务。</p>
          ) : (
            <div className="divide-y divide-border">
              {tasks.map((task) => (
                <div key={task.task_id} className="flex items-center gap-2 py-3">
                  <Link
                    href={`/tasks/${task.task_id}`}
                    className="flex min-w-0 flex-1 items-center justify-between gap-4 rounded-md px-2 py-2 transition hover:bg-muted/60"
                  >
                  <div className="min-w-0">
                    <div className="truncate font-medium">{task.topic}</div>
                    <div className="mt-1 text-xs text-muted-foreground">
                      {task.status} · {task.progress}% · {new Date(task.created_at).toLocaleString()}
                    </div>
                  </div>
                  <ArrowRight size={17} className="shrink-0 text-muted-foreground" />
                  </Link>
                  <button
                    type="button"
                    title="删除任务"
                    aria-label={`删除任务：${task.topic}`}
                    disabled={deletingTaskId === task.task_id}
                    onClick={() => handleDeleteTask(task)}
                    className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-border text-muted-foreground transition hover:border-destructive/30 hover:bg-destructive/10 hover:text-destructive disabled:pointer-events-none disabled:opacity-50"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Capability({ icon, title, text }: { icon: ReactNode; title: string; text: string }) {
  return (
    <div className="rounded-lg border border-border bg-white p-4 shadow-sm">
      <div className="flex h-9 w-9 items-center justify-center rounded-md bg-muted text-primary">{icon}</div>
      <div className="mt-3 text-sm font-semibold">{title}</div>
      <div className="mt-1 text-sm leading-6 text-muted-foreground">{text}</div>
    </div>
  );
}
