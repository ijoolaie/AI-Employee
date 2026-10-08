import type { WorldCameraState, WorldPoint } from "./worldTypes";

const MIN_ZOOM = 0.65;
const MAX_ZOOM = 1.8;

export class WorldCamera {
  private state: WorldCameraState;

  constructor(initial: WorldCameraState) {
    this.state = { ...initial };
  }

  getState(): WorldCameraState {
    return { ...this.state };
  }

  pan(dx: number, dy: number): void {
    this.state.x += dx / this.state.zoom;
    this.state.y += dy / this.state.zoom;
  }

  zoomBy(delta: number, anchor?: WorldPoint): void {
    const previous = this.state.zoom;
    const next = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, previous * (1 + delta)));
    if (next === previous) return;

    if (anchor) {
      this.state.x = anchor.x - ((anchor.x - this.state.x) * previous) / next;
      this.state.y = anchor.y - ((anchor.y - this.state.y) * previous) / next;
    }
    this.state.zoom = next;
  }

  worldToScreen(point: WorldPoint, width: number, height: number): WorldPoint {
    return {
      x: width / 2 + (point.x - this.state.x) * this.state.zoom,
      y: height / 2 + (point.y - this.state.y) * this.state.zoom,
    };
  }
}
