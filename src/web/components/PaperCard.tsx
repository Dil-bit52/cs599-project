import { ExternalLink } from "lucide-react";

import type { Paper } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

export function PaperCard({ paper }: { paper: Paper }) {
  return (
    <article className="rounded-lg border border-border bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-center gap-2">
        <Badge>{paper.source}</Badge>
        {paper.year && <Badge>{paper.year}</Badge>}
        <Badge className="border-emerald-200 bg-emerald-50 text-emerald-700">相关性 {Math.round(paper.relevance * 100)}%</Badge>
      </div>
      <h3 className="mt-3 text-base font-semibold leading-snug">{paper.title}</h3>
      <p className="mt-2 text-xs text-muted-foreground">{paper.authors?.join(", ") || "Unknown authors"}</p>
      <p className="mt-3 line-clamp-4 text-sm leading-6 text-muted-foreground">{paper.abstract}</p>
      {paper.summary && (
        <div className="mt-3 rounded-md bg-muted/45 p-3 text-sm leading-6">
          <span className="font-medium">Agent 评价：</span>
          {paper.summary}
        </div>
      )}
      {paper.url && (
        <a className="mt-3 inline-flex items-center gap-2 text-sm font-medium text-primary" href={paper.url} target="_blank">
          查看来源
          <ExternalLink size={14} />
        </a>
      )}
    </article>
  );
}

