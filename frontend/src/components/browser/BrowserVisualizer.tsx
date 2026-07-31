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
  const [isExpanded, setIsExpanded] = useState(false);
  const [loadingTimeout, setLoadingTimeout] = useState(false);
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

  const hasToolEvent = events.some((e) => e.type === "tool_call" || e.type === "browser_action" || e.type === "browser_started");
  const hasContent = screenshotSrc || displayUrl || events.length > 0;

  /* Loading timeout */
  useEffect(() => {
    if (screenshotSrc || !hasToolEvent) {
      setLoadingTimeout(false);
      return;
    }
    const timer = setTimeout(() => setLoadingTimeout(true), 10000);
    return () => clearTimeout(timer);
  }, [screenshotSrc, hasToolEvent]);

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

  const currentUrl = displayUrl || "";

  /* ── Empty state ── */
  if (!hasContent) {
    const waitingTooLong = loadingTimeout && hasToolEvent;
    return (
      <div className="overflow-hidden rounded-xl border border-zinc-700/50 bg-zinc-950">
        <div className="flex items-center gap-2 border-b border-zinc-800 px-4 py-2.5">
          <span className="flex items-center gap-1.5 text-xs text-zinc-500">
            <span className={`h-2 w-2 rounded-full ${waitingTooLong ? "bg-amber-500" : "bg-blue-500"}`} />
            Browser
          </span>
          {waitingTooLong && <span className="text-[10px] text-amber-400">no response</span>}
        </div>
        <div className="flex flex-col items-center justify-center gap-2 px-4 py-12 text-xs text-zinc-600">
          <svg className="h-8 w-8 text-zinc-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0022.5 18.75V5.25A2.25 2.25 0 0020.25 3H3.75A2.25 2.25 0 001.5 5.25v13.5A2.25 2.25 0 003.75 21z" />
          </svg>
          <span>{waitingTooLong ? "Waiting for browser events..." : "Waiting for a browser task..."}</span>
        </div>
      </div>
    );
  }

  const renderView = (isFull: boolean) => (
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
            style={{ maxHeight: isFull ? 600 : 360 }}
          />
          {hasToolEvent && (
            <div className="absolute right-2 top-2 flex items-center gap-1 rounded bg-green-950/80 px-2 py-0.5 text-[10px] text-green-400">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-green-400" />
              Live
            </div>
          )}
        </div>
      ) : (
        <div className="flex items-center justify-center px-4 py-8 text-xs text-zinc-600">
          {loadingTimeout
            ? <span className="text-amber-400">Waiting for browser events ...</span>
            : <span className="animate-pulse">Loading browser preview ...</span>}
        </div>
      )}
      {actionLabel && (
        <div className="border-t border-zinc-800 px-4 py-1.5 text-xs text-zinc-500">
          {"\u2192"} {actionLabel}
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Main panel */}
      <div className={`relative w-full bg-slate-900 rounded-lg border border-slate-700 overflow-hidden transition-all duration-300 ${isExpanded ? 'fixed inset-4 z-50 shadow-2xl' : 'h-64'}`}>
        {/* Header with Expand Button */}
        <div className="flex justify-between items-center p-2 bg-slate-800 border-b border-slate-700">
          <span className="text-sm font-medium text-slate-300">Browser Live View</span>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 hover:bg-slate-700 rounded-md transition-colors text-slate-300"
            title={isExpanded ? "Compress" : "Expand to Fullscreen"}
          >
            {isExpanded ? (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25" /></svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" /></svg>
            )}
          </button>
        </div>

        {/* Content Area */}
        <div className="w-full h-full flex items-center justify-center bg-black">
          {currentUrl ? (
            <iframe src={currentUrl} className="w-full h-full bg-white" title="Browser Preview" />
          ) : hasContent ? (
            <span className="text-slate-500 text-sm">Loading browser preview...</span>
          ) : (
            <span className="text-slate-500 text-sm">Waiting for browser events...</span>
          )}
        </div>
      </div>

      {/* Backdrop for expanded state */}
      {isExpanded && (
        <div className="fixed inset-0 z-40 bg-black/50" onClick={() => setIsExpanded(false)} />
      )}
    </>
  );
}
