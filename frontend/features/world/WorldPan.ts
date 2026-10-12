export interface GroundDirection {
  x: number;
  z: number;
}

/**
 * Convert pointer drag deltas into ground-plane movement aligned with the
 * camera's projected horizontal and vertical axes. Dragging the scene to the
 * right/down moves the camera target in the opposite projected direction.
 */
export function screenPanToWorldDelta(
  dx: number,
  dy: number,
  worldPerPixel: number,
  cameraRight: GroundDirection,
  cameraUp: GroundDirection,
): GroundDirection {
  return {
    x: -dx * worldPerPixel * cameraRight.x + dy * worldPerPixel * cameraUp.x,
    z: -dx * worldPerPixel * cameraRight.z + dy * worldPerPixel * cameraUp.z,
  };
}
