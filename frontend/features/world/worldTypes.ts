export type WorldDirection = "up" | "down" | "left" | "right";

export interface WorldPoint {
  x: number;
  y: number;
}

export interface WorldCameraState {
  x: number;
  y: number;
  zoom: number;
}

export interface WorldInputState {
  moveX: number;
  moveY: number;
  zoomDelta: number;
}

export interface WorldMapConfig {
  columns: number;
  rows: number;
  tileWidth: number;
  tileHeight: number;
}
