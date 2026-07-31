"use client";

import dynamic from "next/dynamic";
import { useState, useRef, useCallback, useEffect, type FormEvent } from "react";
import { streamTask, approveTask, rejectTask, type MozaEvent } from "@/lib/api";
import MainLayout from "@/components/Layout/MainLayout";
import MessageBubble from "@/components/ui/MessageBubble";

import InputArea from "@/components/chat/InputArea";
import BrowserVisualizer from "@/components/browser/BrowserVisualizer";
import ProviderSelector from "@/components/ui/ProviderSelector";

const TerminalComponent = dynamic(
  () => import("@/components/terminal/TerminalComponent"),
  { ssr: false }
);

/* ── Sub-components ─────────────────────────────────────────────── */

function ToolCallBlock({ event }: { event: MozaEvent }) {
  const [open, setOpen] = useState(false);
  const toolName = event.payload.tool as string;
  const action = (event.payload.args as Record<string, unknown>)?.action as string | undefined;
  const statusLabel = action ? `Running ${toolName}.${action}` : `Running ${toolName}`;

  return (
    <div className="animate-fade-in overflow-hidden rounded-xl border border-slate-700/40 bg-slate-900/50 text-sm">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-slate-300 hover:bg-slate-800/50"
      >
        <span className="inline-block h-1.5 w-1.5 rounded-full bg-amber-400" />
        <span className="font-mono text-xs font-medium text-amber-400">
          {statusLabel}
        </span>
        <span className="ml-auto text-xs">{open ? "\u25BE" : "\u25B8"}</span>
      </button>
      {open && (
        <pre className="overflow-x-auto border-t border-slate-800 px-4 py-3 font-mono text-xs text-slate-400">
          {JSON.stringify(event.payload, null, 2)}
        </pre>
      )}
    </div>
  );
}

function ToolResultBlock({ event }: { event: MozaEvent }) {
  const [open, setOpen] = useState(false);
  const success = event.payload.success as boolean | undefined;
  const stdout = event.payload.stdout as string | undefined;
  const stderr = event.payload.stderr as string | undefined;
  const exitCode = event.payload.exit_code as number | null | undefined;
  const isError = success === false;
  const content = stdout || stderr || "(empty)";
  const toolName = event.payload.tool as string;
  const statusLabel = isError ? `${toolName} failed` : `${toolName} completed`;

  return (
    <div className="animate-fade-in overflow-hidden rounded-xl border border-slate-700/30 bg-slate-900/30">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-2 px-4 py-2.5 text-left hover:bg-slate-800/30"
      >
        <span
          className={`inline-block h-1.5 w-1.5 rounded-full ${
            isError ? "bg-red-500" : "bg-emerald-500"
          }`}
        />
        <span className={`text-xs font-medium ${isError ? "text-red-400" : "text-emerald-400"}`}>
          {statusLabel}
        </span>
        {typeof stdout === "string" && stdout.length > 0 && (
          <span className="truncate text-xs text-slate-500">
            {stdout.split("\n")[0].slice(0, 80)}
          </span>
        )}
        <span className="ml-auto text-xs text-slate-500">{open ? "\u25BE" : "\u25B8"}</span>
      </button>
      {open && (
        <pre className="overflow-x-auto border-t border-slate-800 px-4 py-3 font-mono text-xs leading-relaxed text-slate-300">
          {content}
        </pre>
      )}
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
        <p className="mb-2 text-sm text-slate-300">
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
      <div className="max-w-[80%] rounded-2xl rounded-bl-md bg-slate-800 px-4 py-2.5 text-sm leading-relaxed text-slate-100">
        {content}
        <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-emerald-400" />
      </div>
    </div>
  );
}

function WelcomeCard({ onChipClick }: { onChipClick: (text: string) => void }) {
  const chips = [
    { label: "Search the web", icon: "\uD83D\uDD0D" },
    { label: "Create a file", icon: "\uD83D\uDCC4" },
    { label: "Debug my code", icon: "\uD83D\uDD27" },
    { label: "Research a topic", icon: "\uD83D\uDCDA" },
  ];

  return (
    <div className="flex h-full items-center justify-center py-16">
      <div className="mx-auto max-w-md text-center">
        <h1 className="mb-2 text-2xl font-bold text-slate-100">
          Welcome to MOZA Workspace
        </h1>
        <p className="mb-8 text-sm text-slate-500">
          Your AI Operating System. Describe a task and I will execute it.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          {chips.map((chip) => (
            <button
              key={chip.label}
              onClick={() => onChipClick(chip.label)}
              className="flex items-center gap-2 rounded-full border border-slate-700/50 bg-slate-800/50 px-4 py-2 text-sm text-slate-300 transition-colors hover:border-indigo-500/40 hover:bg-slate-800 hover:text-white"
            >
              <span>{chip.icon}</span>
              <span>{chip.label}</span>
            </button>
          ))}
        </div>
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
  const [terminalEvents, setTerminalEvents] = useState<MozaEvent[]>([]);
  const [browserEvents, setBrowserEvents] = useState<MozaEvent[]>([]);
  const [waitingApproval, setWaitingApproval] = useState<{
    taskId: string;
    tool: string;
    description: string;
  } | null>(null);
  const [agentStatus, setAgentStatus] = useState("Idle");
  const [toolLogOpen, setToolLogOpen] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  const hasContent = events.length > 0 || conversation.length > 0 || !!streamingContent;

async function handleSubmit(e: FormEvent | string) {
        const trimmed = typeof e === "string" ? e : input.trim();
        if (!trimmed || streaming) return;

        if (typeof e !== "string") {
            e.preventDefault();
        }

        const userMsg = trimmed;
        setInput("");
        setStreaming(true);
        setAgentStatus("Thinking");
        setEvents([]);
        setTerminalEvents([]);
        setBrowserEvents([]);
        setStreamingContent("");
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
                    let token = (event.payload.content as string) || "";
                    token = token.replace(/<function=[^>]*>/gi, "").replace(/<\/function>/gi, "").replace(/ool_call>/gi, "");
                    setStreamingContent((prev) => prev + token);
                    setAgentStatus("Thinking");
                    scrollToBottom();
                } else if (event.type === "llm_finished") {
                    const content = event.payload.content as string;
                    if (content) {
                        setConversation((prev) => [...prev, { role: "agent", content }]);
                    }
                    setStreamingContent("");
                    setAgentStatus("Idle");
                    scrollToBottom();
                } else if (event.type === "tool_call") {
                    setAgentStatus("Executing Tool");
                    setEvents((prev) => [...prev, event]);
                    if (event.payload.tool === "browser") {
                        setBrowserEvents((prev) => [...prev, event]);
                    }
                    if (event.payload.tool === "terminal") {
                        setTerminalEvents((prev) => [...prev, event]);
                    }
                    scrollToBottom();
                } else if (event.type === "tool_result") {
                    setEvents((prev) => [...prev, event]);
                    if (event.payload.tool === "browser") {
                        setBrowserEvents((prev) => [...prev, event]);
                    }
                    if (event.payload.tool === "terminal") {
                        setTerminalEvents((prev) => [...prev, event]);
                    }
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
                } else if (event.type === "task_failed") {
                    setAgentStatus("Error");
                    setEvents((prev) => [...prev, event]);
                    scrollToBottom();
                    const errorMsg = event.payload.error as string || "Task failed";
                    setConversation((prev) => [...prev, { role: "agent", content: `Error: ${errorMsg}` }]);
                } else {
                    if (event.type === "agent_started") setAgentStatus("Thinking");
                    if (event.type === "task_failed") setAgentStatus("Error");
                    setEvents((prev) => [...prev, event]);
                    scrollToBottom();
                }
            }
        } catch (error) {
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
                    payload: { error: error instanceof Error ? error.message : "Connection failed" },
                } as MozaEvent,
            ]);
            setConversation((prev) => [...prev, { role: "agent", content: `Error: ${error instanceof Error ? error.message : "Connection failed"}` }]);
        } finally {
            setStreaming(false);
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
      case "waiting_approval":
        const tool = (event.payload.tool as string) || "";
        const action = (event.payload.args as Record<string, unknown>)?.action as string | undefined;
        const label = action ? `${tool} (${action})` : tool;
        return (
          <div key={idx} className="rounded-xl border border-amber-600/30 bg-amber-950/10 px-4 py-2 text-xs text-amber-400">
            Awaiting approval: {label}
          </div>
        );
      default:
        return null;
    }
  }

  /* ── Build left panel content ───────────────────────────────── */
  const leftPanel = (
    <>
      <ProviderSelector />
      {!hasContent && <WelcomeCard onChipClick={(text) => handleSubmit(text)} />}
      {conversation.map((msg, i) => (
        <MessageBubble
          key={`msg-${i}`}
          role={msg.role}
          content={msg.content}
        />
      ))}
      {events.map((ev, i) => renderEvent(ev, i))}
      {streamingContent && <StreamingMessage content={streamingContent} />}
      {(agentStatus === "Thinking" || agentStatus === "Executing Tool") && !streamingContent && (
        <div className="flex items-center gap-2 text-sm text-indigo-400 p-2 bg-indigo-950/30 rounded-lg w-fit">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-indigo-500"></span>
          </span>
          <span>MOZA is processing task...</span>
        </div>
      )}
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
      {browserEvents.length > 0 && (
        <div className="mb-3">
          <BrowserVisualizer events={browserEvents} />
        </div>
      )}
      {terminalEvents.length > 0 && (
        <div className="mb-3">
          <div className="mb-1 text-[10px] font-medium uppercase tracking-widest text-slate-500">
            Terminal
          </div>
          <TerminalComponent events={terminalEvents} />
        </div>
      )}
      {events.filter((e) => e.type === "tool_call" || e.type === "tool_result").length > 0 && (
        <div>
          <button
            onClick={() => setToolLogOpen(!toolLogOpen)}
            className="mb-2 flex w-full items-center gap-2 text-xs font-medium text-slate-500 hover:text-slate-300"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-slate-600" />
            Tool Execution Log
            <span className="ml-auto text-xs">{toolLogOpen ? "\u25BE" : "\u25B8"}</span>
          </button>
          {toolLogOpen && (
            <div className="flex flex-col gap-1">
              {events
                .filter((e) => e.type === "tool_call" || e.type === "tool_result")
                .map((ev, i) => (
                  ev.type === "tool_call"
                    ? <ToolCallBlock key={`rt-${i}`} event={ev} />
                    : <ToolResultBlock key={`rt-${i}`} event={ev} />
                ))}
            </div>
          )}
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
          onSubmit={(e) => handleSubmit(e)}
          isProcessing={streaming}
          placeholder={streaming ? "Type to interrupt or guide MOZA..." : "Ask MOZA to perform a task..."}
        />
      }
      agentStatus={agentStatus}
    />
  );
}
