"use client";

import { useEffect, useRef } from "react";
import { WorldCamera } from "./WorldCamera";
import { WorldInput } from "./WorldInput";
import type { WorldMapConfig } from "./worldTypes";

const DEFAULT_MAP: WorldMapConfig = {
  columns: 12,
  rows: 8,
  tileWidth: 72,
  tileHeight: 36,
};

function drawIsometricMap(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  camera: WorldCamera,
  map: WorldMapConfig,
) {
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#07111f";
  ctx.fillRect(0, 0, width, height);

  const originX = width / 2;
  const originY = height * 0.18;

  for (let row = 0; row < map.rows; row += 1) {
    for (let col = 0; col < map.columns; col += 1) {
      const x = originX + (col - row) * (map.tileWidth / 2);
      const y = originY + (col + row) * (map.tileHeight / 2);
      const scale = camera.getState().zoom;
      const sx = width / 2 + (x - width / 2 - camera.getState().x) * scale;
      const sy = height / 2 + (y - height / 2 - camera.getState().y) * scale;
      const tw = map.tileWidth * scale;
      const th = map.tileHeight * scale;

      ctx.beginPath();
      ctx.moveTo(sx, sy);
      ctx.lineTo(sx + tw / 2, sy + th / 2);
      ctx.lineTo(sx, sy + th);
      ctx.lineTo(sx - tw / 2, sy + th / 2);
      ctx.closePath();
      ctx.fillStyle = (row + col) % 2 === 0 ? "#15253a" : "#122136";
      ctx.fill();
      ctx.strokeStyle = "#29415f";
      ctx.stroke();
    }
  }

  const buildings = [
    { col: 2, row: 2, w: 2, h: 2, label: "COMMAND" },
    { col: 6, row: 1, w: 3, h: 2, label: "SALES" },
    { col: 7, row: 5, w: 2, h: 2, label: "SUPPORT" },
    { col: 2, row: 5, w: 3, h: 2, label: "OPS" },
  ];

  for (const building of buildings) {
    const col = building.col + building.w / 2;
    const row = building.row + building.h / 2;
    const x = originX + (col - row) * (map.tileWidth / 2);
    const y = originY + (col + row) * (map.tileHeight / 2) - 18;
    const scale = camera.getState().zoom;
    const sx = width / 2 + (x - width / 2 - camera.getState().x) * scale;
    const sy = height / 2 + (y - height / 2 - camera.getState().y) * scale;

    ctx.fillStyle = "#1d3552";
    ctx.fillRect(sx - 46 * scale, sy - 24 * scale, 92 * scale, 48 * scale);
    ctx.strokeStyle = "#4b79a6";
    ctx.strokeRect(sx - 46 * scale, sy - 24 * scale, 92 * scale, 48 * scale);
    ctx.fillStyle = "#dbeafe";
    ctx.font = `${Math.max(9, 11 * scale)}px sans-serif`;
    ctx.textAlign = "center";
    ctx.fillText(building.label, sx, sy + 4 * scale);
  }
}

export function WorldViewport() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const host = canvas.parentElement;
    if (!host) return;

    const context = canvas.getContext("2d");
    if (!context) return;

    const camera = new WorldCamera({ x: 0, y: 0, zoom: 1 });
    const input = new WorldInput(canvas);
    let frame = 0;
    let last = performance.now();

    const resize = () => {
      const ratio = window.devicePixelRatio || 1;
      canvas.width = Math.max(1, host.clientWidth * ratio);
      canvas.height = Math.max(1, host.clientHeight * ratio);
      canvas.style.width = `${host.clientWidth}px`;
      canvas.style.height = `${host.clientHeight}px`;
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
    };

    const onPan = (event: Event) => {
      const detail = (event as CustomEvent<{ dx: number; dy: number }>).detail;
      camera.pan(-detail.dx, -detail.dy);
    };

    const onZoom = (event: Event) => {
      const detail = (event as CustomEvent<{ delta: number }>).detail;
      camera.zoomBy(detail.delta);
    };

    canvas.addEventListener("world:pan", onPan);
    canvas.addEventListener("world:zoom", onZoom);
    const observer = new ResizeObserver(resize);
    observer.observe(host);
    resize();

    const tick = (now: number) => {
      const delta = Math.min(64, now - last);
      last = now;
      const movement = input.consume();
      if (movement.moveX || movement.moveY) {
        const length = Math.hypot(movement.moveX, movement.moveY) || 1;
        camera.pan((movement.moveX / length) * delta * 0.45, (movement.moveY / length) * delta * 0.45);
      }

      drawIsometricMap(context, host.clientWidth, host.clientHeight, camera, DEFAULT_MAP);
      frame = requestAnimationFrame(tick);
    };

    frame = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      canvas.removeEventListener("world:pan", onPan);
      canvas.removeEventListener("world:zoom", onZoom);
      input.destroy();
    };
  }, []);

  return (
    <div className="relative h-[min(72vh,720px)] min-h-[420px] w-full overflow-hidden rounded-2xl border border-slate-800 bg-slate-950 shadow-2xl">
      <canvas ref={canvasRef} aria-label="AI Company World viewport" className="block h-full w-full outline-none" />
      <div className="pointer-events-none absolute left-4 top-4 rounded-xl border border-slate-700/80 bg-slate-950/80 px-3 py-2 text-xs text-slate-300 backdrop-blur">
        <div className="font-medium text-white">HQ World</div>
        <div>WASD / Arrow keys · drag to pan · wheel to zoom</div>
      </div>
    </div>
  );
}
