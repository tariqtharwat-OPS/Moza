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

export default function MainLayout({ leftPanel, rightPanel, inputArea, agentStatus }: Props) {
  const [backendStatus, setBackendStatus] = useState<"checking" | "connected" | "disconnected">("checking");

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

  return (
    <div className="flex h-screen flex-col bg-zinc-950 text-zinc-100">
      {/* Header */}
      <header className="flex shrink-0 items-center justify-between border-b border-zinc-800/60 bg-zinc-900/40 px-6 py-3 backdrop-blur-md">
        <Logo />
        <div className="flex items-center gap-4">
          {agentStatus && (
            <span className="rounded-md bg-zinc-800/60 px-2.5 py-1 text-xs font-medium text-zinc-400 ring-1 ring-zinc-700/30">
              {agentStatus}
            </span>
          )}
          <StatusIndicator status={backendStatus} />
        </div>
      </header>

      {/* Main content area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left panel: chat messages */}
        <div className="flex flex-1 flex-col overflow-hidden border-r border-zinc-800/50">
          <div className="flex-1 overflow-y-auto px-4 py-4">
            <div className="mx-auto flex max-w-3xl flex-col gap-3">
              {leftPanel}
            </div>
          </div>
          {inputArea}
        </div>

        {/* Right panel: browser + tools */}
        <div className="flex w-[420px] shrink-0 flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto p-3">
            {rightPanel}
          </div>
        </div>
      </div>
    </div>
  );
}
