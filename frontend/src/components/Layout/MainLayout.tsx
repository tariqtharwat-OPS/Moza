"use client";

import { useState, useEffect } from "react";
import Logo from "@/components/ui/Logo";
import StatusIndicator from "@/components/ui/StatusIndicator";

const BACKEND_URL = "http://localhost:8000";

interface Props {
  leftPanel: React.ReactNode;
  rightPanel: React.ReactNode;
  inputArea: React.ReactNode;
  agentStatus?: string;
}

const RECENT_SESSIONS = [
  { id: "s1", label: "Browser Research", ts: "2m ago" },
  { id: "s2", label: "Bug Fix Session", ts: "15m ago" },
  { id: "s3", label: "File Operations", ts: "1h ago" },
];

export default function MainLayout({ leftPanel, rightPanel, inputArea, agentStatus }: Props) {
  const [backendStatus, setBackendStatus] = useState<"checking" | "connected" | "disconnected">("checking");
  const [rightOpen, setRightOpen] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/docs`, { method: "GET", signal: AbortSignal.timeout(3000) });
        if (!cancelled) setBackendStatus(res.ok ? "connected" : "disconnected");
      } catch {
        if (!cancelled) setBackendStatus("disconnected");
      }
    };
    check();
    const interval = setInterval(check, 15000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  function handleNewSession() {
    window.location.reload();
  }

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100">
      {/* Left Sidebar */}
      <aside className="flex w-[250px] shrink-0 flex-col border-r border-slate-800/60 bg-slate-900/40">
        <div className="flex items-center gap-3 border-b border-slate-800/40 px-4 py-4">
          <Logo size={64} />
        </div>
        <div className="px-3 py-3">
          <button
            onClick={handleNewSession}
            className="flex w-full items-center gap-2 rounded-lg border border-slate-700/50 bg-slate-800/50 px-3 py-2 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-700/50 hover:text-white"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
            </svg>
            New Session
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-3">
          <div className="mb-2 px-1 text-[10px] font-medium uppercase tracking-widest text-slate-500">
            Recent Sessions
          </div>
          <div className="flex flex-col gap-1">
            {RECENT_SESSIONS.map((s) => (
              <button
                key={s.id}
                className="flex items-center justify-between rounded-lg px-3 py-2 text-left text-sm text-slate-400 transition-colors hover:bg-slate-800/60 hover:text-slate-200"
              >
                <span className="truncate">{s.label}</span>
                <span className="shrink-0 text-[10px] text-slate-600">{s.ts}</span>
              </button>
            ))}
          </div>
        </div>
        <div className="border-t border-slate-800/40 px-3 py-3">
          <StatusIndicator status={backendStatus} />
        </div>
      </aside>

      {/* Main Center Panel */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto">
          <div className="mx-auto flex max-w-3xl flex-col gap-3 px-4 py-4">
            {leftPanel}
          </div>
        </div>
        {inputArea}
      </div>

      {/* Right Panel */}
      {rightOpen && (
        <div className="flex w-[300px] shrink-0 flex-col border-l border-slate-800/60 bg-slate-900/30">
          <div className="flex items-center justify-between border-b border-slate-800/40 px-3 py-2">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Execution
            </span>
            <button
              onClick={() => setRightOpen(false)}
              className="rounded p-1 text-slate-600 hover:bg-slate-800/60 hover:text-slate-300"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-3">
            {rightPanel}
          </div>
        </div>
      )}

      {/* Right panel toggle button when closed */}
      {!rightOpen && (
        <button
          onClick={() => setRightOpen(true)}
          className="absolute right-0 top-1/2 -translate-y-1/2 rounded-l-lg border border-slate-800/60 bg-slate-900/80 p-2 text-slate-500 hover:text-slate-300"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      )}
    </div>
  );
}
