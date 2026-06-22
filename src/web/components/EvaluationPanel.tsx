import type { Evaluation } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

const metrics: Array<[keyof Evaluation, string]> = [
  ["relevance", "相关性"],
  ["citation", "引用完整性"],
  ["structure", "结构清晰度"],
  ["faithfulness", "事实一致性"],
  ["overall", "综合评分"]
];

export function EvaluationPanel({ evaluation }: { evaluation?: Evaluation | null }) {
  if (!evaluation) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-muted-foreground">评估尚未完成，等待 Evaluator Agent 输出评分。</CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>报告质量评估</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid gap-4 md:grid-cols-5">
          {metrics.map(([key, label]) => {
            const value = Number(evaluation[key]);
            return (
              <div key={key} className="rounded-lg border border-border bg-white p-4">
                <div className="text-sm text-muted-foreground">{label}</div>
                <div className="mt-2 text-2xl font-semibold">{value.toFixed(1)}</div>
                <div className="mt-3">
                  <Progress value={value * 10} />
                </div>
              </div>
            );
          })}
        </div>
        <div className="rounded-md bg-muted/45 p-4">
          <h3 className="text-sm font-semibold">改进建议</h3>
          <ul className="mt-2 space-y-2 text-sm text-muted-foreground">
            {evaluation.suggestions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}

