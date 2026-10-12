import { describe, expect, it } from "vitest";
import { screenPanToWorldDelta } from "../features/world/WorldPan";

describe("screenPanToWorldDelta", () => {
  const cameraRight = { x: 0.8, z: -0.6 };
  const cameraUp = { x: -0.6, z: -0.8 };

  it("maps horizontal dragging to the camera's projected right axis", () => {
    const delta = screenPanToWorldDelta(10, 0, 0.5, cameraRight, cameraUp);

    expect(delta.x).toBeCloseTo(-4);
    expect(delta.z).toBeCloseTo(3);
  });

  it("maps vertical dragging to the camera's projected ground-up axis", () => {
    const delta = screenPanToWorldDelta(0, 10, 0.5, cameraRight, cameraUp);

    expect(delta.x).toBeCloseTo(-3);
    expect(delta.z).toBeCloseTo(-4);
  });

  it("does not move the camera target for a stationary pointer", () => {
    expect(screenPanToWorldDelta(0, 0, 0.5, cameraRight, cameraUp)).toEqual({ x: 0, z: 0 });
  });
});
