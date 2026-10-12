export type WalkBlocker = { x: number; z: number; halfWidth: number; halfDepth: number };
export type WalkZone = { x: number; z: number };

// Conservative ground-plane footprints for fixed office furniture. The player resolves
// X and Z independently so movement slides along furniture edges instead of tunnelling.
export function getWalkBlockers(zones: readonly WalkZone[]): WalkBlocker[] {
  const desks: WalkBlocker[] = zones.flatMap((zone) =>
    [-2.15, 1.0].flatMap((zOffset) =>
      [-1.8, 1.8].map((xOffset) => ({
        x: zone.x + xOffset,
        z: zone.z + zOffset + 0.25,
        halfWidth: 1.68,
        halfDepth: 1.45,
      })),
    ),
  );
  return [
    ...desks,
    { x: 0, z: 0.1, halfWidth: 2.35, halfDepth: 0.95 }, // reception island
    { x: -8, z: 1.6, halfWidth: 2.25, halfDepth: 1.55 }, // sofa and arms
    { x: 0, z: 2.75, halfWidth: 0.95, halfDepth: 0.95 }, // coffee table
    { x: -11.5, z: 2.2, halfWidth: 0.82, halfDepth: 0.82 },
    { x: 11.5, z: 2.2, halfWidth: 0.82, halfDepth: 0.82 },
  ];
}

export function canOccupyGround(x: number, z: number, blockers: readonly WalkBlocker[], radius = 0.43): boolean {
  if (x < -16 || x > 16 || z < -10 || z > 9.2) return false;
  return !blockers.some((item) =>
    Math.abs(x - item.x) < item.halfWidth + radius &&
    Math.abs(z - item.z) < item.halfDepth + radius,
  );
}
