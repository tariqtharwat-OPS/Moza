"use client";

import dynamic from "next/dynamic";
import { useState, useRef, useCallback, useEffect, type FormEvent } from "react";
import { streamTask, approveTask, rejectTask, type MozaEvent } from "@/lib/api";
import MainLayout from "@/components/Layout/MainLayout";
import MessageBubble from "@/components/ui/MessageBubble";
import TypingIndicator from "@/components/ui/TypingIndicator";
import InputArea from "@/components/chat/InputArea";
import BrowserVisualizer from "@/components/browser/BrowserVisualizer";

const TerminalComponent = dynamic(
  () => import("@/components/terminal/TerminalComponent"),
  { ssr: false }
);

/* ── Sub-components ─────────────────────────────────────────────── */

function ToolCallBlock({ event }: { event: MozaEvent }) {
  const [open, setOpen] = useState(true);
  const toolName = event.payload.tool as string;
  const args = event.payload.args as Record<string, unknown> | undefined;

  return (
    <div className="animate-fade-in overflow-hidden rounded-xl border border-zinc-700/50 bg-zinc-900/50 text-sm">
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
    <div className="animate-fade-in overflow-hidden rounded-xl border border-zinc-700/30 bg-zinc-900/30">
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
          {t.is_destructive && <span className="text-amber-500">&#x26A1;</span>}
        </span>
      ))}
    </div>
  );
}

function TaskHeader({ event }: { event: MozaEvent }) {
  return (
    <div className="animate-fade-in rounded-xl border border-zinc-800 bg-zinc-900/50 px-4 py-3">
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
    <div className="animate-fade-in flex items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900/30 px-4 py-3 text-sm">
      <span className={isError ? "text-red-400" : "text-emerald-400"}>
        {isError ? "\u2715" : "\u2713"}
      </span>
      <span className={isError ? "text-red-300" : "text-zinc-300"}>
        {isError
          ? `Task failed: ${(event.payload.error as string) || "unknown error"}`
          : "Task completed"}
      </span>
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
    <div className="animate-fade-in overflow-hidden rounded-xl border border-amber-600/40 bg-amber-950/20">
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

function StreamingMessage({ content }: { content: string }) {
  if (!content) return null;
  return (
    <div className="animate-fade-in flex justify-start">
      <div className="max-w-[80%] rounded-2xl rounded-bl-md bg-zinc-800 px-4 py-2.5 text-sm leading-relaxed text-zinc-100">
        {content}
        <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-emerald-400" />
      </div>
    </div>
  );
}

/* ── Main ChatInterface ─────────────────────────────────────────── */

export default function ChatInterface() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [events, setEvents] = useState<MozaEvent[]>([]);
  const [conversation, setConversation] = useState<Array<{ role: "user" | "agent"; content: string }>>([]);
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
  const [agentStatus, setAgentStatus] = useState("Idle");
  const bottomRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || streaming) return;

    const userMsg = trimmed;
    setInput("");
    setStreaming(true);
    setAgentStatus("Thinking");
    setEvents([]);
    setTerminalEvents([]);
    setBrowserEvents([]);
    setStreamingContent("");
    setFinalMessage("");
    setWaitingApproval(null);

    setConversation((prev) => [...prev, { role: "user", content: userMsg }]);

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
          setAgentStatus("Thinking");
          scrollToBottom();
        } else if (event.type === "llm_finished") {
          const content = event.payload.content as string;
          setFinalMessage(content || "");
          setStreamingContent("");
          setAgentStatus("Idle");
          if (content) {
            setConversation((prev) => [...prev, { role: "agent", content }]);
          }
          scrollToBottom();
        } else if (event.type === "tool_call") {
          setAgentStatus("Executing Tool");
          setEvents((prev) => [...prev, event]);
          scrollToBottom();
        } else if (event.type === "tool_result") {
          setEvents((prev) => [...prev, event]);
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
          if (event.type === "agent_started") setAgentStatus("Thinking");
          if (event.type === "task_failed") setAgentStatus("Error");
          setEvents((prev) => [...prev, event]);
          scrollToBottom();
        }
      }
    } catch {
      setAgentStatus("Error");
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
      setAgentStatus("Idle");
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
        return <TypingIndicator key={idx} />;
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

  /* ── Build left panel content ───────────────────────────────── */
  const leftPanel = (
    <>
      {events.length === 0 && conversation.length === 0 && !streamingContent && !finalMessage && (
        <div className="flex h-full items-center justify-center py-20">
          <div className="text-center">
            <p className="text-sm text-zinc-600">Describe a task to execute.</p>
          </div>
        </div>
      )}
      {conversation.map((msg, i) => (
        <MessageBubble
          key={`msg-${i}`}
          role={msg.role}
          content={msg.content}
        />
      ))}
      {events.map((ev, i) => renderEvent(ev, i))}
      {streamingContent && <StreamingMessage content={streamingContent} />}
      {waitingApproval && (
        <ApprovalBanner
          waiting={{ tool: waitingApproval.tool, description: waitingApproval.description }}
          onApprove={handleApprove}
          onReject={handleReject}
        />
      )}
      <div ref={bottomRef} />
    </>
  );

  /* ── Build right panel content ──────────────────────────────── */
  const rightPanel = (
    <>
      <div className="mb-3">
        <BrowserVisualizer events={browserEvents} />
      </div>
      {terminalEvents.length > 0 && (
        <div className="mb-3">
          <TerminalComponent events={terminalEvents} />
        </div>
      )}
      {events.filter((e) => e.type === "tool_call" || e.type === "tool_result").length > 0 && (
        <div>
          <div className="mb-2 flex items-center gap-2 text-xs font-medium text-zinc-500">
            <span className="h-1.5 w-1.5 rounded-full bg-zinc-600" />
            Tool Execution Log
          </div>
          <div className="flex flex-col gap-2">
            {events
              .filter((e) => e.type === "tool_call" || e.type === "tool_result")
              .map((ev, i) => (
                ev.type === "tool_call"
                  ? <ToolCallBlock key={`rt-${i}`} event={ev} />
                  : <ToolResultBlock key={`rt-${i}`} event={ev} />
              ))}
          </div>
        </div>
      )}
    </>
  );

  return (
    <MainLayout
      leftPanel={leftPanel}
      rightPanel={rightPanel}
      inputArea={
        <InputArea
          value={input}
          onChange={setInput}
          onSubmit={handleSubmit}
          disabled={streaming}
        />
      }
      agentStatus={agentStatus}
    />
  );
}
