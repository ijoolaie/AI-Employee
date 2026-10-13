export type WalkBlocker = { x: number; z: number; halfWidth: number; halfDepth: number };
export type WalkZone = { x: number; z: number };

// Conservative ground-plane footprints for fixed office furniture and room partitions.
// The center of each room's inner wall contains a doorway; the remaining wall segments
// block movement. X/Z resolution lets the player slide along blockers rather than tunnel.
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

  const roomWalls: WalkBlocker[] = zones.flatMap((zone) => {
    const verticalWalls: WalkBlocker[] = [
      { x: zone.x - 4.5, z: zone.z, halfWidth: 0.08, halfDepth: 3.95 },
      { x: zone.x + 4.5, z: zone.z, halfWidth: 0.08, halfDepth: 3.95 },
    ];
    const innerWallZ = zone.z < 0 ? zone.z + 4 : zone.z - 4;
    const doorwayHalfWidth = 1.25;
    const segmentHalfWidth = 1.575;
    const segmentCenterOffset = doorwayHalfWidth + segmentHalfWidth;
    const innerWallSegments: WalkBlocker[] = [
      { x: zone.x - segmentCenterOffset, z: innerWallZ, halfWidth: segmentHalfWidth, halfDepth: 0.08 },
      { x: zone.x + segmentCenterOffset, z: innerWallZ, halfWidth: segmentHalfWidth, halfDepth: 0.08 },
    ];
    const outerWall: WalkBlocker[] = zone.z > 0
      ? [{ x: zone.x, z: zone.z + 4, halfWidth: 4.4, halfDepth: 0.08 }]
      : [];
    return [...verticalWalls, ...innerWallSegments, ...outerWall];
  });

  return [
    ...desks,
    ...roomWalls,
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
