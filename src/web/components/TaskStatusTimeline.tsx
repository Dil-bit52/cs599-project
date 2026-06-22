import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react";

import type { ResearchTask } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

const steps = [
  "planner",
  "search",
  "reader",
  "rag_store",
  "synthesis",
  "writer",
  "evaluator",
  "completed"
];

export function TaskStatusTimeline({ task }: { task: ResearchTask }) {
  const currentIndex = Math.max(0, steps.indexOf(task.current_step));

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-4">
        <div>
          <CardTitle>{task.topic}</CardTitle>
          <p className="mt-1 text-sm text-muted-foreground">当前步骤：{task.current_step}</p>
        </div>
        <Badge className={task.status === "completed" ? "border-emerald-200 bg-emerald-50 text-emerald-700" : ""}>{task.status}</Badge>
      </CardHeader>
      <CardContent className="space-y-5">
        <Progress value={task.progress} />
        <div className="grid gap-3 md:grid-cols-2">
          {steps.slice(0, -1).map((step, index) => {
            const done = task.status === "completed" || index < currentIndex;
            const active = task.status === "running" && step === task.current_step;
            const failed = task.status === "failed" && step === task.current_step;
            return (
              <div key={step} className="flex items-start gap-3 rounded-md border border-border bg-white p-3">
                <span className="mt-0.5 text-primary">
                  {failed ? <XCircle size={18} className="text-red-600" /> : done ? <CheckCircle2 size={18} /> : active ? <Loader2 size={18} className="animate-spin" /> : <Circle size={18} className="text-muted-foreground" />}
                </span>
                <div>
                  <div className="text-sm font-medium">{label(step)}</div>
                  <div className="text-xs text-muted-foreground">{description(step)}</div>
                </div>
              </div>
            );
          })}
        </div>
        <div className="space-y-3">
          <h3 className="text-sm font-semibold">Agent 执行日志</h3>
          <div className="space-y-2">
            {task.agent_logs.map((log) => (
              <div key={log.id} className="rounded-md border border-border bg-muted/35 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-sm font-medium">{log.agent}</span>
                  <span className="text-xs text-muted-foreground">{new Date(log.created_at).toLocaleString()}</span>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">{log.message}</p>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function label(step: string) {
  return {
    planner: "Planner Agent",
    search: "Search Agent",
    reader: "Reader Agent",
    rag_store: "RAG Store",
    synthesis: "Synthesis Agent",
    writer: "Writer Agent",
    evaluator: "Evaluator Agent"
  }[step] ?? step;
}

function description(step: string) {
  return {
    planner: "拆解主题、生成关键词和报告大纲",
    search: "调用工具检索候选论文",
    reader: "阅读摘要并生成论文总结",
    rag_store: "写入本地知识库",
    synthesis: "横向归纳方法、趋势和局限",
    writer: "生成 Markdown 研究报告",
    evaluator: "评估报告质量"
  }[step] ?? "";
}

