"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { BookOpen, FileText, Gauge, ListTree } from "lucide-react";

import { EvaluationPanel } from "@/components/EvaluationPanel";
import { PaperCard } from "@/components/PaperCard";
import { ReportViewer } from "@/components/ReportViewer";
import { TaskStatusTimeline } from "@/components/TaskStatusTimeline";
import { getReport, getTask, type ResearchTask } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const tabs = [
  { key: "timeline", label: "执行轨迹", icon: ListTree },
  { key: "papers", label: "论文结果", icon: BookOpen },
  { key: "report", label: "研究报告", icon: FileText },
  { key: "evaluation", label: "质量评估", icon: Gauge }
] as const;

type TabKey = (typeof tabs)[number]["key"];

export default function TaskPage() {
  const params = useParams<{ taskId: string }>();
  const taskId = params.taskId;
  const [task, setTask] = useState<ResearchTask | null>(null);
  const [report, setReport] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabKey>("timeline");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const nextTask = await getTask(taskId);
        if (cancelled) return;
        setTask(nextTask);
        if (nextTask.report_path && !report) {
          const nextReport = await getReport(taskId);
          if (!cancelled) setReport(nextReport.content);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "加载任务失败");
      }
    }

    load();
    const timer = setInterval(() => {
      if (task?.status === "completed" || task?.status === "failed") return;
      load();
    }, 1400);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [taskId, task?.status, report]);

  if (error) {
    return <Card><CardContent className="py-10 text-sm text-red-700">{error}</CardContent></Card>;
  }

  if (!task) {
    return <Card><CardContent className="py-10 text-sm text-muted-foreground">正在加载任务...</CardContent></Card>;
  }

  return (
    <div className="space-y-5">
      <TaskStatusTimeline task={task} />

      <div className="flex flex-wrap gap-2">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <Button
              key={tab.key}
              variant={activeTab === tab.key ? "default" : "outline"}
              onClick={() => setActiveTab(tab.key)}
            >
              <Icon size={16} />
              {tab.label}
            </Button>
          );
        })}
      </div>

      {activeTab === "timeline" && <TaskStatusTimeline task={task} />}
      {activeTab === "papers" && (
        <div className="grid gap-4 lg:grid-cols-2">
          {task.papers.length === 0 ? (
            <Card><CardContent className="py-10 text-sm text-muted-foreground">论文结果尚未生成。</CardContent></Card>
          ) : task.papers.map((paper) => <PaperCard key={`${paper.title}-${paper.year}`} paper={paper} />)}
        </div>
      )}
      {activeTab === "report" && <ReportViewer taskId={taskId} content={report} />}
      {activeTab === "evaluation" && <EvaluationPanel evaluation={task.evaluation} />}
    </div>
  );
}

