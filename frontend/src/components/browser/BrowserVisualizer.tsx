"use client";

import { useState, useEffect, useRef } from "react";
import type { MozaEvent } from "@/lib/api";

interface BrowserState {
  url: string;
  title: string;
  screenshotBase64: string | null;
}

export default function BrowserVisualizer({ events }: { events: MozaEvent[] }) {
  const [state, setState] = useState<BrowserState>({
    url: "",
    title: "",
    screenshotBase64: null,
  });
  const [activeTab, setActiveTab] = useState<"view" | "actions">("view");
  const imgRef = useRef<HTMLImageElement>(null);

  const lastEvent = events[events.length - 1];
  const payload = lastEvent?.payload || {};
  const meta = payload.metadata as Record<string, unknown> | undefined;
  const metaScreenshot = meta?.screenshot_base64 as string | null;
  const metaUrl = meta?.url as string | null;
  const metaTitle = meta?.title as string | null;

  const screenshotSrc = metaScreenshot || state.screenshotBase64 || null;
  const displayUrl = metaUrl || state.url || null;
  const displayTitle = metaTitle || state.title || null;

  const hasContent = screenshotSrc || displayUrl || events.length > 0;
  const isActive = events.some((e) => e.type === "tool_call" || e.type === "browser_action" || e.type === "browser_started");

  /* Keep state in sync with latest event metadata */
  useEffect(() => {
    if (metaScreenshot) setState((s) => ({ ...s, screenshotBase64: metaScreenshot }));
    if (metaUrl) setState((s) => ({ ...s, url: metaUrl }));
    if (metaTitle) setState((s) => ({ ...s, title: metaTitle }));
  }, [metaScreenshot, metaUrl, metaTitle]);

  const actionLabel =
    lastEvent?.type === "tool_call"
      ? ((payload.args as Record<string, unknown>)?.action as string) || ""
      : null;

  /* ── Empty state ── */
  if (!hasContent) {
    return (
      <div className="overflow-hidden rounded-xl border border-zinc-700/50 bg-zinc-950">
        <div className="flex items-center gap-2 border-b border-zinc-800 px-4 py-2.5">
          <span className="flex items-center gap-1.5 text-xs text-zinc-500">
            <span className="h-2 w-2 rounded-full bg-blue-500" />
            Browser
          </span>
        </div>
        <div className="flex flex-col items-center justify-center gap-2 px-4 py-12 text-xs text-zinc-600">
          <svg className="h-8 w-8 text-zinc-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0022.5 18.75V5.25A2.25 2.25 0 0020.25 3H3.75A2.25 2.25 0 001.5 5.25v13.5A2.25 2.25 0 003.75 21z" />
          </svg>
          <span>Waiting for a browser task...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-zinc-700/50 bg-zinc-950">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-zinc-800 px-4 py-2.5">
        <span className="flex items-center gap-1.5 text-xs text-zinc-500">
          <span className={`h-2 w-2 rounded-full ${isActive ? "bg-green-500 animate-pulse" : "bg-blue-500"}`} />
          Browser
          {isActive && <span className="ml-1 text-[10px] text-green-400">LIVE</span>}
        </span>
        <div className="flex flex-1 items-center gap-2 overflow-hidden">
          <span className="text-xs text-zinc-400">URL:</span>
          <span className="truncate font-mono text-xs text-zinc-300">
            {displayUrl || "\u2014"}
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

      {/* View tab */}
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
                ref={imgRef}
                src={`data:image/png;base64,${screenshotSrc}`}
                alt="Browser screenshot"
                className="w-full object-contain transition-opacity duration-300"
                style={{ maxHeight: 360 }}
              />
              {isActive && (
                <div className="absolute right-2 top-2 flex items-center gap-1 rounded bg-green-950/80 px-2 py-0.5 text-[10px] text-green-400">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-green-400" />
                  Live
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center px-4 py-8 text-xs text-zinc-600">
              <span className="animate-pulse">Loading browser preview...</span>
            </div>
          )}
          {actionLabel && (
            <div className="border-t border-zinc-800 px-4 py-1.5 text-xs text-zinc-500">
              {"\u2192"} {actionLabel}
            </div>
          )}
        </div>
      )}

      {/* Actions tab */}
      {activeTab === "actions" && (
        <div className="max-h-40 overflow-y-auto px-4 py-2">
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
                    ? `\u2192 ${act}`
                    : "\u2192 call"
                  : `\u2713 result`;
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
