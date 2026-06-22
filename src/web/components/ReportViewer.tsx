"use client";

import ReactMarkdown from "react-markdown";
import { Copy, Download } from "lucide-react";

import { reportDownloadUrl } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function ReportViewer({ taskId, content }: { taskId: string; content: string | null }) {
  if (!content) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-muted-foreground">报告尚未生成，等待 Writer Agent 完成。</CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-3">
        <CardTitle>研究报告预览</CardTitle>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigator.clipboard.writeText(content)}>
            <Copy size={16} />
            复制
          </Button>
          <a href={reportDownloadUrl(taskId)}>
            <Button>
              <Download size={16} />
              下载 Markdown
            </Button>
          </a>
        </div>
      </CardHeader>
      <CardContent>
        <div className="markdown-body max-h-[720px] overflow-auto rounded-md border border-border bg-white p-5">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      </CardContent>
    </Card>
  );
}

