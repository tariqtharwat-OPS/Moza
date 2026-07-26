"use client";

import { useState } from "react";
import type { MozaEvent } from "@/lib/api";

interface BrowserState {
  url: string;
  title: string;
  screenshotBase64: string | null;
  actions: Array<{ action: string; timestamp: string }>;
}

export default function BrowserVisualizer({ events }: { events: MozaEvent[] }) {
  const [state, setState] = useState<BrowserState>({
    url: "",
    title: "",
    screenshotBase64: null,
    actions: [],
  });
  const [activeTab, setActiveTab] = useState<"view" | "actions">("view");

  const lastEvent = events[events.length - 1];
  const payload = lastEvent?.payload || {};
  const metaScreenshot = payload.metadata
    ? (payload.metadata as Record<string, unknown>)?.screenshot_base64
    : null;
  const metaUrl = payload.metadata
    ? (payload.metadata as Record<string, unknown>)?.url
    : null;
  const metaTitle = payload.metadata
    ? (payload.metadata as Record<string, unknown>)?.title
    : null;

  const screenshotSrc =
    (metaScreenshot as string) || state.screenshotBase64 || null;
  const displayUrl = (metaUrl as string) || state.url || "—";
  const displayTitle = (metaTitle as string) || state.title || "—";

  if (!screenshotSrc && !displayUrl) {
    return null;
  }

  const actionLabel =
    lastEvent.type === "tool_call"
      ? ((payload.args as Record<string, unknown>)?.action as string) || ""
      : "result";

  return (
    <div className="overflow-hidden rounded-xl border border-zinc-700/50 bg-zinc-950">
      <div className="flex items-center gap-3 border-b border-zinc-800 px-4 py-2.5">
        <span className="flex items-center gap-1.5 text-xs text-zinc-500">
          <span className="h-2 w-2 rounded-full bg-blue-500" />
          Browser
        </span>
        <div className="flex flex-1 items-center gap-2 overflow-hidden">
          <span className="text-xs text-zinc-400">URL:</span>
          <span className="truncate font-mono text-xs text-zinc-300">
            {displayUrl}
          </span>
        </div>
        <div className="flex gap-1">
          <button
            onClick={() => setActiveTab("view")}
            className={`rounded px-2 py-0.5 text-xs ${
              activeTab === "view"
                ? "bg-zinc-700 text-zinc-200"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            View
          </button>
          <button
            onClick={() => setActiveTab("actions")}
            className={`rounded px-2 py-0.5 text-xs ${
              activeTab === "actions"
                ? "bg-zinc-700 text-zinc-200"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            Actions
          </button>
        </div>
      </div>

      {activeTab === "view" && (
        <div>
          {displayTitle && (
            <div className="border-b border-zinc-800 px-4 py-1.5 text-xs text-zinc-500">
              {displayTitle}
            </div>
          )}
          {screenshotSrc ? (
            <div className="relative">
              <img
                src={`data:image/png;base64,${screenshotSrc}`}
                alt="Browser screenshot"
                className="w-full object-contain"
                style={{ maxHeight: 480 }}
              />
            </div>
          ) : (
            <div className="flex items-center justify-center px-4 py-12 text-xs text-zinc-600">
              No screenshot available
            </div>
          )}
          {actionLabel && (
            <div className="border-t border-zinc-800 px-4 py-1.5 text-xs text-zinc-500">
              {actionLabel}
            </div>
          )}
        </div>
      )}

      {activeTab === "actions" && (
        <div className="max-h-48 overflow-y-auto px-4 py-2">
          {events.length === 0 ? (
            <p className="py-4 text-center text-xs text-zinc-600">
              No browser actions yet
            </p>
          ) : (
            events.map((ev, i) => {
              const act = ev.payload.args
                ? (ev.payload.args as Record<string, unknown>).action
                : null;
              const label =
                ev.type === "tool_call"
                  ? act
                    ? `→ ${act}`
                    : "→ call"
                  : `✓ result`;
              return (
                <div
                  key={i}
                  className="flex items-center gap-2 py-1 font-mono text-xs"
                >
                  <span
                    className={
                      ev.type === "tool_call"
                        ? "text-amber-400"
                        : "text-emerald-400"
                    }
                  >
                    {label}
                  </span>
                  <span className="text-zinc-600">
                    {new Date(ev.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
