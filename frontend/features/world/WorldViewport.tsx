"use client";

import { useEffect, useRef } from "react";
import { WorldCamera } from "./WorldCamera";
import { WorldInput } from "./WorldInput";
import { worldPositionForSlot } from "./WorldState";
import type { WorldEmployee } from "./WorldState";
import type { WorldMapConfig, WorldPoint } from "./worldTypes";

const DEFAULT_MAP: WorldMapConfig = { columns: 12, rows: 8, tileWidth: 72, tileHeight: 36 };

const STATE_GLYPH: Record<WorldEmployee["state"], string> = {
  WORKING: "●",
  WAITING_APPROVAL: "!",
  IDLE: "·",
  BLOCKED: "×",
  ESCALATED: "▲",
  COMPLETED: "✓",
};

const STATE_TONE: Record<WorldEmployee["state"], string> = {
  WORKING: "#34d399",
  WAITING_APPROVAL: "#fbbf24",
  IDLE: "#94a3b8",
  BLOCKED: "#f87171",
  ESCALATED: "#fb923c",
  COMPLETED: "#818cf8",
};

function screenPoint(world: WorldPoint, camera: WorldCamera, width: number, height: number): WorldPoint {
  const { x, y, zoom } = camera.getState();
  return {
    x: width / 2 + (world.x - x) * zoom,
    y: height / 2 + (world.y - y) * zoom,
  };
}

function drawMap(ctx: CanvasRenderingContext2D, width: number, height: number, camera: WorldCamera, map: WorldMapConfig) {
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#07111f";
  ctx.fillRect(0, 0, width, height);

  const originX = 0;
  const originY = -height * 0.34;
  const { zoom } = camera.getState();

  for (let row = 0; row < map.rows; row += 1) {
    for (let col = 0; col < map.columns; col += 1) {
      const worldX = originX + (col - row) * (map.tileWidth / 2);
      const worldY = originY + (col + row) * (map.tileHeight / 2);
      const point = screenPoint({ x: worldX, y: worldY }, camera, width, height);
      const tw = map.tileWidth * zoom;
      const th = map.tileHeight * zoom;

      ctx.beginPath();
      ctx.moveTo(point.x, point.y);
      ctx.lineTo(point.x + tw / 2, point.y + th / 2);
      ctx.lineTo(point.x, point.y + th);
      ctx.lineTo(point.x - tw / 2, point.y + th / 2);
      ctx.closePath();
      ctx.fillStyle = (row + col) % 2 === 0 ? "#15253a" : "#122136";
      ctx.fill();
      ctx.strokeStyle = "#29415f";
      ctx.stroke();
    }
  }

  const buildings = [
    { col: 2, row: 2, label: "COMMAND" },
    { col: 6, row: 1, label: "SALES" },
    { col: 7, row: 5, label: "SUPPORT" },
    { col: 2, row: 5, label: "OPS" },
    { col: 5, row: 4, label: "ENGINEERING" },
  ];

  for (const building of buildings) {
    const world = {
      x: (building.col - building.row) * (map.tileWidth / 2),
      y: (building.col + building.row) * (map.tileHeight / 2) - 18,
    };
    const point = screenPoint(world, camera, width, height);
    const bw = 94 * zoom;
    const bh = 48 * zoom;

    ctx.fillStyle = "#1d3552";
    ctx.fillRect(point.x - bw / 2, point.y - bh / 2, bw, bh);
    ctx.strokeStyle = "#4b79a6";
    ctx.strokeRect(point.x - bw / 2, point.y - bh / 2, bw, bh);
    ctx.fillStyle = "#dbeafe";
    ctx.font = `${Math.max(9, 11 * zoom)}px sans-serif`;
    ctx.textAlign = "center";
    ctx.fillText(building.label, point.x, point.y + 4 * zoom);
  }
}

function drawEmployees(ctx: CanvasRenderingContext2D, employees: WorldEmployee[], camera: WorldCamera, width: number, height: number, map: WorldMapConfig, selectedId: string | null) {
  for (const employee of employees) {
    const world = worldPositionForSlot(employee.slot, map);
    const point = screenPoint(world, camera, width, height);
    const radius = Math.max(9, 13 * camera.getState().zoom);

    ctx.beginPath();
    ctx.arc(point.x, point.y, radius + 3, 0, Math.PI * 2);
    ctx.fillStyle = selectedId === employee.id ? "#e0f2fe" : "#0f1d2e";
    ctx.fill();

    ctx.beginPath();
    ctx.arc(point.x, point.y, radius, 0, Math.PI * 2);
    ctx.fillStyle = STATE_TONE[employee.state];
    ctx.fill();

    ctx.fillStyle = "#06111f";
    ctx.font = `${Math.max(10, 12 * camera.getState().zoom)}px sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(STATE_GLYPH[employee.state], point.x, point.y);

    ctx.textBaseline = "alphabetic";
    ctx.fillStyle = "#e2e8f0";
    ctx.font = `${Math.max(9, 11 * camera.getState().zoom)}px sans-serif`;
    ctx.fillText(employee.name.slice(0, 16), point.x, point.y + radius + 14);
  }
}

export function WorldViewport({
  employees,
  selectedEmployeeId,
  onEmployeeSelect,
}: {
  employees: WorldEmployee[];
  selectedEmployeeId: string | null;
  onEmployeeSelect: (employeeId: string | null) => void;
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

    const onZoom = (event: Event) => {
      const { delta } = (event as CustomEvent<{ delta: number }>).detail;
      camera.zoomBy(delta);
    };

    const onMapToggle = () => handleMapToggle();\n\n    const onMobileMove = (event: Event) => {
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
    canvas.addEventListener("world:tap", onTap);\n    canvas.addEventListener("world:map-toggle", onMapToggle);
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
      canvas.removeEventListener("world:tap", onTap);\n      canvas.removeEventListener("world:map-toggle", onMapToggle);
      host.removeEventListener("world:mobilemove", onMobileMove);
      input.destroy();
    };
  }, [employees, selectedEmployeeId, onEmployeeSelect]);

  return (
    <div className="relative h-[min(72vh,720px)] min-h-[420px] w-full overflow-hidden rounded-2xl border border-slate-800 bg-slate-950 shadow-2xl">
      <canvas ref={canvasRef} aria-label="AI Company World viewport" className="block h-full w-full outline-none" />
      <div className="pointer-events-none absolute left-4 top-4 rounded-xl border border-slate-700/80 bg-slate-950/80 px-3 py-2 text-xs text-slate-300 backdrop-blur">
        <div className="font-medium text-white">HQ World</div>
        <div className="hidden sm:block">WASD / Arrow keys · drag to pan · wheel to zoom</div>
        <div className="sm:hidden">Joystick · drag to pan</div>
      </div>
    </div>
  );
}
