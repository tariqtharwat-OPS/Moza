"use client";

export default function Logo() {
  return (
    <div className="flex items-center gap-3">
      <img
        src="/logo.png"
        alt="MOZA"
        style={{ width: 220 }}
        className="h-auto object-contain transition-opacity duration-200 hover:opacity-90"
      />
    </div>
  );
}
