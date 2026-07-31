const API_BASE = "http://localhost:8001/v1";
const WS_URL = "ws://localhost:8001/ws";

type StatusCallback = (status: "connected" | "disconnected") => void;
type EventCallback = (event: MessageEvent) => void;

let ws: WebSocket | null = null;
let pingInterval: ReturnType<typeof setInterval> | null = null;
let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_DELAY = 30000;
let statusCallbacks: StatusCallback[] = [];
let eventCallbacks: EventCallback[] = [];

export function onBackendStatus(cb: StatusCallback) {
  statusCallbacks.push(cb);
  return () => { statusCallbacks = statusCallbacks.filter((c) => c !== cb); };
}

export function onWebSocketEvent(cb: EventCallback) {
  eventCallbacks.push(cb);
  return () => { eventCallbacks = eventCallbacks.filter((c) => c !== cb); };
}

function notifyStatus(status: "connected" | "disconnected") {
  statusCallbacks.forEach((cb) => cb(status));
}

function scheduleReconnect() {
  const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), MAX_RECONNECT_DELAY);
  reconnectAttempts++;
  reconnectTimeout = setTimeout(() => {
    connectWebSocket();
  }, delay);
}

export function connectWebSocket() {
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;
  try {
    ws = new WebSocket(WS_URL);
    ws.onopen = () => {
      reconnectAttempts = 0;
      notifyStatus("connected");
      pingInterval = setInterval(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "ping" }));
        }
      }, 10000);
    };
    ws.onmessage = (event: MessageEvent) => {
      eventCallbacks.forEach((cb) => cb(event));
    };
    ws.onclose = () => {
      notifyStatus("disconnected");
      if (pingInterval) clearInterval(pingInterval);
      scheduleReconnect();
    };
    ws.onerror = () => {
      ws?.close();
    };
  } catch {
    scheduleReconnect();
  }
}

export function disconnectWebSocket() {
  if (reconnectTimeout) clearTimeout(reconnectTimeout);
  if (pingInterval) clearInterval(pingInterval);
  if (ws) {
    ws.onclose = null;
    ws.close();
    ws = null;
  }
  reconnectAttempts = 0;
}

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

export interface OrchestratorInfo {
  enabled: boolean;
  current_provider?: string;
  current_model?: string;
  current_rank?: number;
  success_rate?: number;
  dead_providers?: string[];
  total_providers?: number;
  total_models?: number;
  error?: string;
}

export async function getOrchestratorInfo(): Promise<OrchestratorInfo> {
  try {
    const response = await fetch(`${API_BASE}/orchestrator/info`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
      throw new Error(`Orchestrator API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Failed to get orchestrator info:", error);
    return { enabled: false };
  }
}
