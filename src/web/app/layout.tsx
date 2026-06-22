import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import { BookOpenCheck, MessageSquareText, Search } from "lucide-react";

import "./globals.css";

export const metadata: Metadata = {
  title: "ResearchPilot",
  description: "Agentic AI Research Assistant"
};

export default function RootLayout({
  children
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>
        <div className="min-h-screen">
          <header className="border-b border-border/70 bg-white/75 backdrop-blur">
            <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
              <Link href="/" className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-md bg-primary text-primary-foreground">
                  <BookOpenCheck size={22} />
                </span>
                <span>
                  <span className="block text-base font-semibold">ResearchPilot</span>
                  <span className="block text-xs text-muted-foreground">Agentic AI Research Assistant</span>
                </span>
              </Link>
              <nav className="flex items-center gap-2 text-sm">
                <Link className="flex items-center gap-2 rounded-md px-3 py-2 text-muted-foreground hover:bg-muted hover:text-foreground" href="/">
                  <Search size={16} />
                  研究任务
                </Link>
                <Link className="flex items-center gap-2 rounded-md px-3 py-2 text-muted-foreground hover:bg-muted hover:text-foreground" href="/chat">
                  <MessageSquareText size={16} />
                  知识库问答
                </Link>
              </nav>
            </div>
          </header>
          <main className="mx-auto max-w-7xl px-5 py-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
