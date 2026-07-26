"use client";

import { useState, useRef, useCallback, type FormEvent } from "react";
import { streamTask, approveTask, rejectTask, type MozaEvent } from "@/lib/api";
import BrowserVisualizer from "@/components/browser/BrowserVisualizer";
import TerminalComponent from "@/components/terminal/TerminalComponent";

function ThinkingDots() {
  return (
    <div className="flex items-center gap-1.5 px-4 py-3 text-sm text-zinc-400">
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-emerald-500 [animation-delay:0ms]" />
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-emerald-500 [animation-delay:150ms]" />
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-emerald-500 [animation-delay:300ms]" />
    </div>
  );
}

function ToolCallBlock({ event }: { event: MozaEvent }) {
  const [open, setOpen] = useState(true);
  const toolName = event.payload.tool as string;
  const args = event.payload.args as Record<string, unknown> | undefined;

  return (
    <div className="overflow-hidden rounded-xl border border-zinc-700/50 bg-zinc-900/50 text-sm">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-zinc-300 hover:bg-zinc-800/50"
      >
        <span className="text-xs">{open ? "▾" : "▸"}</span>
        <span className="font-mono text-xs font-medium text-amber-400">
          {toolName}
        </span>
        {args && (
          <span className="truncate text-xs text-zinc-500">
            {JSON.stringify(args).slice(0, 120)}
          </span>
        )}
      </button>
      {open && args && (
        <pre className="overflow-x-auto border-t border-zinc-800 px-4 py-3 font-mono text-xs text-zinc-400">
          {JSON.stringify(args, null, 2)}
        </pre>
      )}
    </div>
  );
}

function ToolResultBlock({ event }: { event: MozaEvent }) {
  const success = event.payload.success as boolean | undefined;
  const stdout = event.payload.stdout as string | undefined;
  const stderr = event.payload.stderr as string | undefined;
  const exitCode = event.payload.exit_code as number | null | undefined;
  const isError = success === false;

  const content = stdout || stderr || "(empty)";
  const exitInfo = exitCode !== null && exitCode !== undefined
    ? `exit code: ${exitCode}`
    : null;

  return (
    <div className="overflow-hidden rounded-xl border border-zinc-700/30 bg-zinc-900/30">
      <div className="flex items-center gap-2 border-b border-zinc-800/50 px-4 py-2">
        <span
          className={`inline-block h-1.5 w-1.5 rounded-full ${
            isError ? "bg-red-500" : "bg-emerald-500"
          }`}
        />
        <span className="text-xs font-medium text-zinc-400">
          {isError ? "Failed" : "Output"}
        </span>
        {exitInfo && (
          <span className="ml-auto font-mono text-xs text-zinc-500">
            {exitInfo}
          </span>
        )}
      </div>
      <pre className="overflow-x-auto px-4 py-3 font-mono text-xs leading-relaxed text-zinc-300">
        {content}
      </pre>
    </div>
  );
}

function ToolSelectedBanner({ event }: { event: MozaEvent }) {
  const tools = event.payload.tools as
    | Array<{ name: string; description: string; is_destructive: boolean }>
    | undefined;

  return (
    <div className="flex flex-wrap items-center gap-2 px-4 py-2 text-xs text-zinc-500">
      <span>tools available:</span>
      {tools?.map((t) => (
        <span
          key={t.name}
          className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 font-mono ${
            t.is_destructive
              ? "bg-amber-950/40 text-amber-400"
              : "bg-zinc-800 text-zinc-300"
          }`}
        >
          {t.name}
          {t.is_destructive && <span className="text-amber-500">⚡</span>}
        </span>
      ))}
    </div>
  );
}

function TaskHeader({ event }: { event: MozaEvent }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 px-4 py-3">
      <div className="flex items-center gap-2 text-xs text-zinc-500">
        <span className="h-1.5 w-1.5 rounded-full bg-blue-500" />
        Task started
      </div>
      <p className="mt-1 text-sm text-zinc-300">
        {event.payload.description as string}
      </p>
    </div>
  );
}

function TaskComplete({ event }: { event: MozaEvent }) {
  const isError = event.type === "task_failed";
  return (
    <div className="flex items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900/30 px-4 py-3 text-sm">
      <span className={isError ? "text-red-400" : "text-emerald-400"}>
        {isError ? "✕" : "✓"}
      </span>
      <span className={isError ? "text-red-300" : "text-zinc-300"}>
        {isError
          ? `Task failed: ${(event.payload.error as string) || "unknown error"}`
          : "Task completed"}
      </span>
    </div>
  );
}

function StreamingMessage({ content }: { content: string }) {
  if (!content) return null;
  return (
    <div className="flex justify-start">
      <div className="max-w-[80%] rounded-2xl rounded-bl-md bg-zinc-800 px-4 py-2.5 text-sm leading-relaxed text-zinc-100">
        {content}
        <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-emerald-400" />
      </div>
    </div>
  );
}

function ApprovalBanner({
  waiting,
  onApprove,
  onReject,
}: {
  waiting: { tool: string; description: string };
  onApprove: () => void;
  onReject: () => void;
}) {
  const isPending = waiting.description === "approving..." || waiting.description === "rejecting...";
  return (
    <div className="overflow-hidden rounded-xl border border-amber-600/40 bg-amber-950/20">
      <div className="flex items-center gap-2 border-b border-amber-800/30 px-4 py-2.5">
        <span className="h-2 w-2 rounded-full bg-amber-400" />
        <span className="text-xs font-medium text-amber-300">Approval Required</span>
      </div>
      <div className="px-4 py-3">
        <p className="mb-2 text-sm text-zinc-300">
          {waiting.description || `Tool "${waiting.tool}" requires approval.`}
        </p>
        <div className="flex gap-2">
          <button
            onClick={onApprove}
            disabled={isPending}
            className="rounded-lg bg-emerald-700 px-4 py-1.5 text-xs font-medium text-white transition-colors hover:bg-emerald-600 disabled:opacity-50"
          >
            {waiting.description === "approving..." ? "Approving..." : "Approve"}
          </button>
          <button
            onClick={onReject}
            disabled={isPending}
            className="rounded-lg bg-red-800 px-4 py-1.5 text-xs font-medium text-white transition-colors hover:bg-red-700 disabled:opacity-50"
          >
            {waiting.description === "rejecting..." ? "Rejecting..." : "Reject"}
          </button>
        </div>
      </div>
    </div>
  );
}

function FinalMessage({ content }: { content: string }) {
  if (!content) return null;
  return (
    <div className="flex justify-start">
      <div className="max-w-[80%] rounded-2xl rounded-bl-md bg-zinc-800 px-4 py-2.5 text-sm leading-relaxed text-zinc-100">
        {content}
      </div>
    </div>
  );
}

export default function ChatInterface() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [events, setEvents] = useState<MozaEvent[]>([]);
  const [streamingContent, setStreamingContent] = useState("");
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [finalMessage, setFinalMessage] = useState("");
  const [terminalEvents, setTerminalEvents] = useState<MozaEvent[]>([]);
  const [browserEvents, setBrowserEvents] = useState<MozaEvent[]>([]);
  const [waitingApproval, setWaitingApproval] = useState<{
    taskId: string;
    tool: string;
    description: string;
  } | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || streaming) return;

    setInput("");
    setStreaming(true);
    setEvents([]);
    setTerminalEvents([]);
    setBrowserEvents([]);
    setStreamingContent("");
    setFinalMessage("");
    setWaitingApproval(null);

    let sid = sessionId;

    try {
      for await (const event of streamTask(trimmed, sid || undefined)) {
        if (!sid) {
          sid = event.session_id;
          setSessionId(sid);
        }

        if (event.type === "llm_token") {
          const token = event.payload.content as string;
          setStreamingContent((prev) => prev + (token || ""));
          scrollToBottom();
        } else if (event.type === "llm_finished") {
          const content = event.payload.content as string;
          setFinalMessage(content || "");
          setStreamingContent("");
          scrollToBottom();
        } else if (
          (event.type === "tool_call" || event.type === "tool_result") &&
          event.payload.tool === "terminal"
        ) {
          setTerminalEvents((prev) => [...prev, event]);
          scrollToBottom();
        } else if (
          (event.type === "tool_call" || event.type === "tool_result") &&
          event.payload.tool === "browser"
        ) {
          setBrowserEvents((prev) => [...prev, event]);
          scrollToBottom();
        } else if (
          event.type === "browser_started" ||
          event.type === "browser_action"
        ) {
          setBrowserEvents((prev) => [...prev, event]);
          scrollToBottom();
        } else if (event.type === "waiting_approval") {
          setWaitingApproval({
            taskId: event.task_id,
            tool: (event.payload.tool as string) || "unknown",
            description: (event.payload.description as string) || "",
          });
          setEvents((prev) => [...prev, event]);
          scrollToBottom();
        } else {
          setEvents((prev) => [...prev, event]);
          scrollToBottom();
        }
      }
    } catch {
      setEvents((prev) => [
        ...prev,
        {
          id: "error",
          timestamp: new Date().toISOString(),
          session_id: sid || "unknown",
          task_id: "unknown",
          type: "task_failed",
          source: "frontend",
          payload: { error: "Connection failed" },
        },
      ]);
    } finally {
      setWaitingApproval(null);
      scrollToBottom();
    }
  }

  async function handleApprove() {
    if (!waitingApproval) return;
    setWaitingApproval((prev) => prev ? { ...prev, description: "approving..." } : null);
    await approveTask(waitingApproval.taskId);
  }

  async function handleReject() {
    if (!waitingApproval) return;
    setWaitingApproval((prev) => prev ? { ...prev, description: "rejecting..." } : null);
    await rejectTask(waitingApproval.taskId);
  }

  function renderEvent(event: MozaEvent, idx: number) {
    switch (event.type) {
      case "agent_started":
        return <TaskHeader key={idx} event={event} />;
      case "agent_thinking":
        return <ThinkingDots key={idx} />;
      case "tool_selected":
        return <ToolSelectedBanner key={idx} event={event} />;
      case "tool_call":
        return <ToolCallBlock key={idx} event={event} />;
      case "tool_result":
        return <ToolResultBlock key={idx} event={event} />;
      case "waiting_approval":
        return (
          <div key={idx} className="rounded-xl border border-amber-600/30 bg-amber-950/10 px-4 py-2 text-xs text-amber-400">
            Awaiting approval for tool: {(event.payload.tool as string) || "unknown"}
          </div>
        );
      case "task_completed":
      case "task_failed":
        return <TaskComplete key={idx} event={event} />;
      default:
        return null;
    }
  }

  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center gap-3 border-b border-zinc-800 px-6 py-4">
        <span className="text-lg font-semibold tracking-tight">MOZA</span>
        <span className="rounded-md bg-zinc-800 px-2 py-0.5 text-xs text-zinc-400">
          The Hands
        </span>
        {streaming && (
          <span className="ml-auto animate-pulse text-xs text-emerald-400">
            executing...
          </span>
        )}
      </header>

      <div className="flex-1 overflow-y-auto px-4 py-6">
        {events.length === 0 && !streamingContent && !finalMessage && (
          <div className="flex h-full items-center justify-center">
            <p className="text-sm text-zinc-600">
              Describe a task to execute.
            </p>
          </div>
        )}
        <div className="mx-auto flex max-w-3xl flex-col gap-3">
          {events.map((ev, i) => renderEvent(ev, i))}
          {terminalEvents.length > 0 && (
            <TerminalComponent events={terminalEvents} />
          )}
          {browserEvents.length > 0 && (
            <BrowserVisualizer events={browserEvents} />
          )}
          {waitingApproval && (
            <ApprovalBanner
              waiting={{ tool: waitingApproval.tool, description: waitingApproval.description }}
              onApprove={handleApprove}
              onReject={handleReject}
            />
          )}
          {streamingContent && <StreamingMessage content={streamingContent} />}
          {finalMessage && <FinalMessage content={finalMessage} />}
        </div>
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={handleSubmit}
        className="border-t border-zinc-800 px-4 py-4"
      >
        <div className="mx-auto flex max-w-3xl gap-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Describe a task..."
            disabled={streaming}
            className="flex-1 rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm text-zinc-100 placeholder-zinc-500 outline-none transition-colors focus:border-zinc-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={streaming || !input.trim()}
            className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:opacity-50 disabled:hover:bg-blue-600"
          >
            Execute
          </button>
        </div>
      </form>
    </div>
  );
}
