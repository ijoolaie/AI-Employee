"use client";

import { useRef } from "react";

export function MobileInputAdapter() {
  const start = useRef<{ x: number; y: number } | null>(null);

  return (
    <div
      className="absolute bottom-20 left-4 z-20 h-28 w-28 touch-none rounded-full border border-white/20 bg-slate-950/85 p-2 shadow-xl backdrop-blur md:hidden"
      aria-label="World movement joystick"
      onPointerDown={(event) => {
        start.current = { x: event.clientX, y: event.clientY };
        event.currentTarget.setPointerCapture(event.pointerId);
      }}
      onPointerMove={(event) => {
        if (!start.current) return;
        const dx = Math.max(-1, Math.min(1, (event.clientX - start.current.x) / 36));
        const dy = Math.max(-1, Math.min(1, (event.clientY - start.current.y) / 36));
        event.currentTarget.dispatchEvent(
          new CustomEvent("world:mobilemove", { bubbles: true, detail: { x: dx, y: dy } }),
        );
      }}
      onPointerUp={(event) => {
        start.current = null;
        event.currentTarget.releasePointerCapture(event.pointerId);
        event.currentTarget.dispatchEvent(
          new CustomEvent("world:mobilemove", { bubbles: true, detail: { x: 0, y: 0 } }),
        );
      }}
      onPointerCancel={(event) => {
        start.current = null;
        event.currentTarget.dispatchEvent(
          new CustomEvent("world:mobilemove", { bubbles: true, detail: { x: 0, y: 0 } }),
        );
      }}
    >
      <div className="flex h-full items-center justify-center">
        <div className="h-10 w-10 rounded-full border border-white/25 bg-white/15" />
      </div>
    </div>
  );
}
