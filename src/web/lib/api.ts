export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type AgentLog = {
  id: number;
  agent: string;
  status: string;
  message: string;
  payload?: Record<string, unknown>;
  created_at: string;
};

export type Paper = {
  id?: number;
  title: string;
  authors: string[];
  year?: number | null;
  source: string;
  abstract: string;
  url?: string | null;
  relevance: number;
  summary?: string | null;
};

export type Evaluation = {
  relevance: number;
  citation: number;
  structure: number;
  faithfulness: number;
  overall: number;
  suggestions: string[];
};

export type ResearchTask = {
  task_id: string;
  topic: string;
  language: "zh" | "en";
  max_papers: number;
  status: "created" | "running" | "completed" | "failed";
  current_step: string;
  progress: number;
  created_at: string;
  updated_at: string;
  report_path?: string | null;
  error?: string | null;
  agent_logs: AgentLog[];
  papers: Paper[];
  evaluation?: Evaluation | null;
};

export type ChatResponse = {
  answer: string;
  sources: Array<{ title: string; url?: string | null; score: number }>;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function createTask(input: {
  topic: string;
  language: "zh" | "en";
  max_papers: number;
}) {
  return request<{ task_id: string; status: string }>("/api/research-tasks", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export function listTasks() {
  return request<ResearchTask[]>("/api/research-tasks");
}

export function getTask(taskId: string) {
  return request<ResearchTask>(`/api/research-tasks/${taskId}`);
}

export function deleteTask(taskId: string) {
  return request<{ task_id: string; deleted: boolean }>(`/api/research-tasks/${taskId}`, {
    method: "DELETE"
  });
}

export function getReport(taskId: string) {
  return request<{ task_id: string; format: "markdown"; content: string }>(`/api/research-tasks/${taskId}/report`);
}

export function askQuestion(taskId: string, question: string) {
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({ task_id: taskId, question })
  });
}

export function reportDownloadUrl(taskId: string) {
  return `${API_BASE_URL}/api/research-tasks/${taskId}/report/download`;
}
