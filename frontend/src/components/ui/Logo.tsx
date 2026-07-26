"use client";

export default function Logo({ className }: { className?: string }) {
  return (
    <div className={`relative overflow-hidden ${className || ""}`}>
      <div className="absolute inset-0 bg-slate-900/80" />
      <img
        src="/logo.png"
        alt="MOZA"
        className="relative z-10 h-auto w-full object-contain mix-blend-screen"
        style={{ filter: "contrast(1.2) brightness(1.1)" }}
      />
    </div>
  );
}
