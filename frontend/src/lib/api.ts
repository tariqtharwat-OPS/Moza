const API_BASE = "http://localhost:8000/v1";

export interface MozaEvent {
  id: string;
  timestamp: string;
  session_id: string;
  task_id: string;
  type: string;
  source: string;
  payload: Record<string, unknown>;
}

export async function* streamTask(
  description: string,
  sessionId?: string
): AsyncGenerator<MozaEvent> {
  const response = await fetch(`${API_BASE}/task/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId || null,
      description,
      workspace_path: "",
    }),
  });

  if (!response.ok) {
    throw new Error(`Task API error: ${response.status}`);
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let isDataLine = false;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("event: step")) {
        isDataLine = true;
      } else if (isDataLine && line.startsWith("data: ")) {
        isDataLine = false;
        try {
          const parsed: MozaEvent = JSON.parse(line.slice(6));
          yield parsed;
        } catch {
          // skip malformed JSON
        }
      }
    }
  }
}

export async function approveTask(taskId: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/task/${taskId}/approve`, {
    method: "POST",
  });
  return res.ok;
}

export async function rejectTask(taskId: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/task/${taskId}/reject`, {
    method: "POST",
  });
  return res.ok;
}
