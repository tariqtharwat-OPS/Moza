"use client";

interface Props {
  status: "connected" | "disconnected" | "checking";
  label?: string;
}

export default function StatusIndicator({ status, label }: Props) {
  return (
    <div className="flex items-center gap-2">
      <span
        className={`inline-block h-2 w-2 rounded-full ${
          status === "connected"
            ? "bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.5)]"
            : status === "checking"
            ? "bg-amber-500 shadow-[0_0_6px_rgba(245,158,11,0.5)]"
            : "bg-red-500 shadow-[0_0_6px_rgba(239,68,68,0.5)]"
        }`}
      />
      <span className="text-xs font-medium text-zinc-400">
        {label || (status === "connected"
          ? "Backend Connected"
          : status === "checking"
          ? "Checking..."
          : "Backend Disconnected")}
      </span>
    </div>
  );
}
