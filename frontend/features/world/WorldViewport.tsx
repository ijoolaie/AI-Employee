"use client";

import { useEffect, useRef } from "react";
import { WorldCamera } from "./WorldCamera";
import { WorldInput } from "./WorldInput";
import type { WorldMapConfig } from "./worldTypes";

const DEFAULT_MAP: WorldMapConfig = { columns: 12, rows: 8, tileWidth: 72, tileHeight: 36 };

function drawIsometricMap(ctx: CanvasRenderingContext2D, width: number, height: number, camera: WorldCamera, map: WorldMapConfig) {
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#07111f";
  ctx.fillRect(0, 0, width, height);

  const { x: cameraX, y: cameraY, zoom } = camera.getState();
  const originX = width / 2;
  const originY = height * 0.16;

  for (let row = 0; row < map.rows; row += 1) {
    for (let col = 0; col < map.columns; col += 1) {
      const worldX = originX + (col - row) * (map.tileWidth / 2);
      const worldY = originY + (col + row) * (map.tileHeight / 2);
      const sx = width / 2 + (worldX - width / 2 - cameraX) * zoom;
      const sy = height / 2 + (worldY - height / 2 - cameraY) * zoom;
      const tw = map.tileWidth * zoom;
      const th = map.tileHeight * zoom;

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
    { col: 2, row: 2, label: "COMMAND" },
    { col: 6, row: 1, label: "SALES" },
    { col: 7, row: 5, label: "SUPPORT" },
    { col: 2, row: 5, label: "OPS" },
  ];

  for (const building of buildings) {
    const worldX = originX + (building.col - building.row) * (map.tileWidth / 2);
    const worldY = originY + (building.col + building.row) * (map.tileHeight / 2) - 18;
    const sx = width / 2 + (worldX - width / 2 - cameraX) * zoom;
    const sy = height / 2 + (worldY - height / 2 - cameraY) * zoom;
    const bw = 92 * zoom;
    const bh = 48 * zoom;

    ctx.fillStyle = "#1d3552";
    ctx.fillRect(sx - bw / 2, sy - bh / 2, bw, bh);
    ctx.strokeStyle = "#4b79a6";
    ctx.strokeRect(sx - bw / 2, sy - bh / 2, bw, bh);
    ctx.fillStyle = "#dbeafe";
    ctx.font = `${Math.max(9, 11 * zoom)}px sans-serif`;
    ctx.textAlign = "center";
    ctx.fillText(building.label, sx, sy + 4 * zoom);
  }
}

export function WorldViewport() {
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

    const onMobileMove = (event: Event) => {
      mobileMove = (event as CustomEvent<{ x: number; y: number }>).detail;
    };

    canvas.addEventListener("world:pan", onPan);
    canvas.addEventListener("world:zoom", onZoom);
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
      drawIsometricMap(context, host.clientWidth, host.clientHeight, camera, DEFAULT_MAP);
      frame = requestAnimationFrame(tick);
    };

    frame = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      canvas.removeEventListener("world:pan", onPan);
      canvas.removeEventListener("world:zoom", onZoom);
      host.removeEventListener("world:mobilemove", onMobileMove);
      input.destroy();
    };
  }, []);

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
