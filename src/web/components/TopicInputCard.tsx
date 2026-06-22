"use client";

import { FormEvent, useState } from "react";
import { ArrowRight } from "lucide-react";

import { createTask } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

const examples = [
  "Agentic RAG 在企业知识库中的应用",
  "大语言模型多智能体协作研究进展",
  "RAG 系统中的检索增强与评估方法"
];

export function TopicInputCard({ onCreated }: { onCreated: (taskId: string) => void }) {
  const [topic, setTopic] = useState(examples[0]);
  const [language, setLanguage] = useState<"zh" | "en">("zh");
  const [maxPapers, setMaxPapers] = useState(8);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await createTask({
        topic,
        language,
        max_papers: maxPapers
      });
      onCreated(response.task_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建任务失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>创建学术调研任务</CardTitle>
      </CardHeader>
      <CardContent>
        <form className="space-y-5" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <label className="text-sm font-medium">研究主题</label>
            <Input value={topic} onChange={(event) => setTopic(event.target.value)} placeholder="输入研究主题" />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">报告语言</label>
              <select
                className="h-10 w-full rounded-md border border-border bg-white px-3 text-sm"
                value={language}
                onChange={(event) => setLanguage(event.target.value as "zh" | "en")}
              >
                <option value="zh">中文</option>
                <option value="en">English</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">最大论文数</label>
              <Input
                type="number"
                min={3}
                max={20}
                value={maxPapers}
                onChange={(event) => setMaxPapers(Number(event.target.value))}
              />
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            {examples.map((item) => (
              <button
                type="button"
                key={item}
                className="rounded-md border border-border bg-white px-3 py-2 text-xs text-muted-foreground hover:border-primary hover:text-foreground"
                onClick={() => setTopic(item)}
              >
                {item}
              </button>
            ))}
          </div>

          {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

          <Button disabled={loading || topic.trim().length < 2} type="submit">
            {loading ? "创建中" : "开始研究"}
            <ArrowRight size={16} />
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
