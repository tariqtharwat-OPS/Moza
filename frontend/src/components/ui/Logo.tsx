"use client";

export default function Logo({ className }: { className?: string }) {
  return (
    <div className={className || ""}>
      <img
        src="/logo.png"
        alt="MOZA"
        className="h-auto w-full object-contain"
      />
    </div>
  );
}
