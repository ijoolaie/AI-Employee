export interface GroundDirection {
  x: number;
  z: number;
}

/**
 * Convert pointer drag deltas into world-ground movement using camera-aligned
 * horizontal and vertical directions. A drag moves the scene with the pointer,
 * so the camera target moves in the opposite horizontal direction.
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
