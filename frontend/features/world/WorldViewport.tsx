"use client";

import { useEffect, useRef } from "react";
import { WorldCamera } from "./WorldCamera";
import { WorldInput } from "./WorldInput";
import { DEFAULT_MAP, drawEmployees, drawMap, screenPoint } from "./WorldRenderer";
import { worldPositionForSlot } from "./WorldState";
import type { WorldEmployee } from "./WorldState";
export function WorldViewport({
  employees,
  selectedEmployeeId,
  onEmployeeSelect,
  onMapToggle: handleMapToggle,
}: {
  employees: WorldEmployee[];
  selectedEmployeeId: string | null;
  onEmployeeSelect: (employeeId: string | null) => void;
  onMapToggle: () => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const host = canvas?.parentElement;
    const context = canvas?.getContext("2d");
    if (!canvas || !host || !context) return;

    const camera = new WorldCamera({ x: 0, y: 0, zoom: 1 });
    const input = new WorldInput(canvas);
    let frame = 0;
    let last = performance.now();
    let mobileMove = { x: 0, y: 0 };

    const resize = () => {
      const ratio = window.devicePixelRatio || 1;
      canvas.width = Math.max(1, Math.floor(host.clientWidth * ratio));
      canvas.height = Math.max(1, Math.floor(host.clientHeight * ratio));
      canvas.style.width = `${host.clientWidth}px`;
      canvas.style.height = `${host.clientHeight}px`;
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
    };

    const onPan = (event: Event) => {
      const { dx, dy } = (event as CustomEvent<{ dx: number; dy: number }>).detail;
      camera.pan(-dx, -dy);
    };

    const onReset = () => camera.reset();

    const onZoom = (event: Event) => {
      const { delta } = (event as CustomEvent<{ delta: number }>).detail;
      camera.zoomBy(delta);
    };

    const onMapToggle = () => handleMapToggle();

    const onMobileMove = (event: Event) => {
      mobileMove = (event as CustomEvent<{ x: number; y: number }>).detail;
    };

    const onTap = (event: Event) => {
      const { x, y } = (event as CustomEvent<{ x: number; y: number }>).detail;
      const hit = employees.find((employee) => {
        const point = screenPoint(worldPositionForSlot(employee.slot, DEFAULT_MAP), camera, host.clientWidth, host.clientHeight);
        return Math.hypot(point.x - x, point.y - y) <= Math.max(20, 22 * camera.getState().zoom);
      });
      onEmployeeSelect(hit?.id ?? null);
    };

    canvas.addEventListener("world:pan", onPan);
    canvas.addEventListener("world:zoom", onZoom);
    canvas.addEventListener("world:reset", onReset);
    canvas.addEventListener("world:tap", onTap);
    canvas.addEventListener("world:map-toggle", onMapToggle);
    host.addEventListener("world:mobilemove", onMobileMove);

    const observer = new ResizeObserver(resize);
    observer.observe(host);
    resize();

    const tick = (now: number) => {
      const delta = Math.min(64, now - last);
      last = now;
      const keyboard = input.consume();
      const moveX = keyboard.moveX || mobileMove.x;
      const moveY = keyboard.moveY || mobileMove.y;
      if (moveX || moveY) {
        const length = Math.hypot(moveX, moveY) || 1;
        camera.pan((moveX / length) * delta * 0.45, (moveY / length) * delta * 0.45);
      }

      drawMap(context, host.clientWidth, host.clientHeight, camera, DEFAULT_MAP);
      drawEmployees(context, employees, camera, host.clientWidth, host.clientHeight, DEFAULT_MAP, selectedEmployeeId);
      frame = requestAnimationFrame(tick);
    };

    frame = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      canvas.removeEventListener("world:pan", onPan);
      canvas.removeEventListener("world:zoom", onZoom);
      canvas.removeEventListener("world:reset", onReset);
      canvas.removeEventListener("world:tap", onTap);
      canvas.removeEventListener("world:map-toggle", onMapToggle);
      host.removeEventListener("world:mobilemove", onMobileMove);
      input.destroy();
    };
  }, [employees, selectedEmployeeId, onEmployeeSelect, handleMapToggle]);

  return (
    <div className="relative h-[min(72vh,720px)] min-h-[420px] w-full overflow-hidden rounded-2xl border border-slate-800 bg-slate-950 shadow-2xl">
      <canvas ref={canvasRef} aria-label="AI Company World viewport" className="block h-full w-full outline-none" />
      <div className="absolute bottom-4 left-4 z-10 flex gap-1 rounded-xl border border-white/10 bg-slate-950/80 p-1 backdrop-blur" aria-label="World camera controls">
        <button type="button" className="h-8 w-8 rounded-lg text-sm text-slate-200 hover:bg-white/10" onClick={() => canvasRef.current?.dispatchEvent(new CustomEvent("world:zoom", { detail: { delta: 0.12 } }))} aria-label="Zoom in">+</button>
        <button type="button" className="h-8 w-8 rounded-lg text-sm text-slate-200 hover:bg-white/10" onClick={() => canvasRef.current?.dispatchEvent(new CustomEvent("world:zoom", { detail: { delta: -0.12 } }))} aria-label="Zoom out">−</button>
        <button type="button" className="rounded-lg px-2 text-xs text-slate-300 hover:bg-white/10" onClick={() => canvasRef.current?.dispatchEvent(new CustomEvent("world:reset"))}>Reset</button>
      </div>
      <div className="pointer-events-none absolute left-4 top-4 rounded-xl border border-slate-700/80 bg-slate-950/80 px-3 py-2 text-xs text-slate-300 backdrop-blur">
        <div className="font-medium text-white">HQ World</div>
        <div className="hidden sm:block">WASD / Arrow keys · drag to pan · wheel to zoom</div>
        <div className="sm:hidden">Joystick · drag to pan</div>
      </div>
    </div>
  );
}
