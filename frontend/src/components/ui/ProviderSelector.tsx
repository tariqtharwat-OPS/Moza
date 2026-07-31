"use client";

import { useState, useEffect } from "react";
import { getOrchestratorInfo } from "@/lib/api";

interface ProviderInfo {
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

export default function ProviderSelector() {
  const [providerInfo, setProviderInfo] = useState<ProviderInfo>({ enabled: false });
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Check if orchestrator is available and load provider info
    const loadProviderInfo = async () => {
      try {
        const info = await getOrchestratorInfo();
        setProviderInfo(info);
        setIsVisible(info.enabled);
      } catch (error) {
        console.error("Failed to load provider info:", error);
        setProviderInfo({ enabled: false });
        setIsVisible(false);
      }
    };

    loadProviderInfo();
    
    // Refresh provider info every 30 seconds
    const interval = setInterval(loadProviderInfo, 30000);
    return () => clearInterval(interval);
  }, []);

  if (!isVisible) return null;

  const getRankBadgeColor = (rank: number) => {
    if (rank <= 3) return "bg-emerald-500 text-white";
    if (rank <= 10) return "bg-amber-500 text-white";
    return "bg-slate-500 text-white";
  };

  const getProviderStatusColor = (provider: string) => {
    if (providerInfo.dead_providers?.includes(provider)) {
      return "bg-red-500";
    }
    return "bg-emerald-500";
  };

  return (
    <div className="mb-4 rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-slate-300">AI Provider Status</h3>
        <div className="flex items-center gap-2">
          {providerInfo.success_rate !== undefined && (
            <span className="text-xs text-slate-500">
              {Math.round(providerInfo.success_rate * 100)}% success
            </span>
          )}
          <button
            onClick={() => setIsVisible(!isVisible)}
            className="text-xs text-slate-500 hover:text-slate-300"
          >
            {isVisible ? "Hide" : "Show"}
          </button>
        </div>
      </div>

      {providerInfo.enabled ? (
        <div className="space-y-2">
          {providerInfo.current_provider && providerInfo.current_model && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">Using:</span>
              <span className="text-sm font-medium text-slate-200">
                #{providerInfo.current_rank || "N/A"} {providerInfo.current_provider}
              </span>
              <span className="text-xs text-slate-500">
                {providerInfo.current_model}
              </span>
              <span 
                className={`inline-flex h-5 w-5 items-center justify-center rounded-full text-xs font-medium ${getRankBadgeColor(providerInfo.current_rank || 0)}`}
              >
                #{providerInfo.current_rank || "N/A"}
              </span>
            </div>
          )}

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="text-slate-500">
              Total Providers: {providerInfo.total_providers || 7}
            </div>
            <div className="text-slate-500">
              Total Models: {providerInfo.total_models || 19}
            </div>
          </div>

          {providerInfo.dead_providers && providerInfo.dead_providers.length > 0 && (
            <div className="mt-2 p-2 bg-red-900/20 rounded-lg">
              <div className="text-xs font-medium text-red-400 mb-1">
                Unavailable Providers:
              </div>
              <div className="flex flex-wrap gap-1">
                {providerInfo.dead_providers.map((provider) => (
                  <span
                    key={provider}
                    className="inline-flex items-center gap-1 rounded-full bg-red-800/50 px-2 py-1 text-xs text-red-300"
                  >
                    <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
                    {provider}
                  </span>
                ))}
              </div>
            </div>
          )}

          {providerInfo.error && (
            <div className="mt-2 p-2 bg-amber-900/20 rounded-lg">
              <div className="text-xs text-amber-400">
                Error: {providerInfo.error}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-sm text-slate-400">
          Using single provider mode
        </div>
      )}
    </div>
  );
}