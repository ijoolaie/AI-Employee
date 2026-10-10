export type RoomSceneAccess = {
  granted?: unknown;
  roomInstanceId?: string | null;
  expiresAt?: string | null;
};

export function isRoomSceneAccessUsable(
  access: RoomSceneAccess | null | undefined,
  unavailable = false,
  now = Date.now(),
): boolean {
  if (unavailable || access?.granted !== true) return false;
  if (typeof access.roomInstanceId !== "string" || access.roomInstanceId.trim().length === 0) return false;
  if (typeof access.expiresAt !== "string" || access.expiresAt.trim().length === 0) return false;

  const expiresAt = Date.parse(access.expiresAt);
  return Number.isFinite(expiresAt) && expiresAt > now;
}
