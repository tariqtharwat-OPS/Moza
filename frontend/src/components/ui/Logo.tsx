"use client";

export default function Logo({ size = 72 }: { size?: number }) {
  return (
    <img
      src="/logo.png"
      alt="MOZA"
      style={{ width: size, height: size }}
      className="h-auto object-contain mix-blend-screen"
    />
  );
}
