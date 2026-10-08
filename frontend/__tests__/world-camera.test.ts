import { describe, expect, it } from "vitest";
import { WorldCamera } from "../features/world/WorldCamera";

describe("WorldCamera", () => {
  it("pans in world coordinates", () => {
    const camera = new WorldCamera({ x: 0, y: 0, zoom: 1 });
    camera.pan(20, -10);
    expect(camera.getState()).toEqual({ x: 20, y: -10, zoom: 1 });
  });

  it("clamps zoom", () => {
    const camera = new WorldCamera({ x: 0, y: 0, zoom: 1 });
    camera.zoomBy(-0.9);
    expect(camera.getState().zoom).toBeGreaterThanOrEqual(0.65);
    camera.zoomBy(10);
    expect(camera.getState().zoom).toBeLessThanOrEqual(1.8);
  });

  it("projects a world point around the camera", () => {
    const camera = new WorldCamera({ x: 10, y: 20, zoom: 2 });
    expect(camera.worldToScreen({ x: 10, y: 20 }, 800, 600)).toEqual({ x: 400, y: 300 });
  });
});
