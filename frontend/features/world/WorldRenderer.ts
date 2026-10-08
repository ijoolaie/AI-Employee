import { worldPositionForSlot } from "./WorldState";
import type { WorldEmployee } from "./WorldState";
import type { WorldMapConfig, WorldPoint } from "./worldTypes";

export const DEFAULT_MAP: WorldMapConfig = { columns: 12, rows: 8, tileWidth: 72, tileHeight: 36 };

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

export function screenPoint(world: WorldPoint, camera: { getState: () => { x: number; y: number; zoom: number } }, width: number, height: number): WorldPoint {
  const { x, y, zoom } = camera.getState();
  return { x: width / 2 + (world.x - x) * zoom, y: height / 2 + (world.y - y) * zoom };
}

export function drawMap(ctx: CanvasRenderingContext2D, width: number, height: number, camera: { getState: () => { x: number; y: number; zoom: number } }, map: WorldMapConfig) {
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#07111f";
  ctx.fillRect(0, 0, width, height);
  const { zoom } = camera.getState();

  for (let row = 0; row < map.rows; row += 1) {
    for (let col = 0; col < map.columns; col += 1) {
      const worldX = (col - row) * (map.tileWidth / 2);
      const worldY = -height * 0.34 + (col + row) * (map.tileHeight / 2);
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
    const point = screenPoint({
      x: (building.col - building.row) * (map.tileWidth / 2),
      y: (building.col + building.row) * (map.tileHeight / 2) - 18,
    }, camera, width, height);
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

export function drawEmployees(ctx: CanvasRenderingContext2D, employees: WorldEmployee[], camera: { getState: () => { x: number; y: number; zoom: number } }, width: number, height: number, map: WorldMapConfig, selectedId: string | null) {
  const zoom = camera.getState().zoom;
  for (const employee of employees) {
    const point = screenPoint(worldPositionForSlot(employee.slot, map), camera, width, height);
    const radius = Math.max(9, 13 * zoom);

    ctx.beginPath();
    ctx.arc(point.x, point.y, radius + 3, 0, Math.PI * 2);
    ctx.fillStyle = selectedId === employee.id ? "#e0f2fe" : "#0f1d2e";
    ctx.fill();

    ctx.beginPath();
    ctx.arc(point.x, point.y, radius, 0, Math.PI * 2);
    ctx.fillStyle = STATE_TONE[employee.state];
    ctx.fill();

    ctx.fillStyle = "#06111f";
    ctx.font = `${Math.max(10, 12 * zoom)}px sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(STATE_GLYPH[employee.state], point.x, point.y);

    ctx.textBaseline = "alphabetic";
    ctx.fillStyle = "#e2e8f0";
    ctx.font = `${Math.max(9, 11 * zoom)}px sans-serif`;
    ctx.fillText(employee.name.slice(0, 16), point.x, point.y + radius + 14);
  }
}
