export type RoomFurnitureKind = "desk" | "chair" | "plant" | "cabinet" | "meeting_table";

export type RoomFurniturePlacement = {
  placement_id: string;
  kind: RoomFurnitureKind;
  x: number;
  z: number;
  rotation: number;
};

export type RoomEmployeePlacement = {
  employee_id: string;
  x: number;
  z: number;
  rotation: number;
};

export type WorldRoomSceneConfig = {
  schema_version: 1;
  layout_preset: "starter";
  furniture: RoomFurniturePlacement[];
  employee_placements: RoomEmployeePlacement[];
};

export const DEFAULT_ROOM_SCENE_CONFIG: WorldRoomSceneConfig = {
  schema_version: 1,
  layout_preset: "starter",
  furniture: [
    { placement_id: "starter-desk", kind: "desk", x: 0, z: -1.3, rotation: 0 },
    { placement_id: "starter-plant", kind: "plant", x: 2.2, z: 2.2, rotation: 0 },
  ],
  employee_placements: [],
};

const FURNITURE_KINDS = new Set<RoomFurnitureKind>(["desk", "chair", "plant", "cabinet", "meeting_table"]);
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function normalizeRoomSceneConfig(
  value: unknown,
  allowedEmployeeIds?: ReadonlySet<string>,
): WorldRoomSceneConfig {
  if (!value || typeof value !== "object" || Array.isArray(value)) return DEFAULT_ROOM_SCENE_CONFIG;
  const raw = value as Record<string, unknown>;
  if (Object.keys(raw).length === 0) return DEFAULT_ROOM_SCENE_CONFIG;
  if (raw.schema_version !== 1 || raw.layout_preset !== "starter" || !Array.isArray(raw.furniture)) return DEFAULT_ROOM_SCENE_CONFIG;

  const ids = new Set<string>();
  const furniture: RoomFurniturePlacement[] = [];
  for (const entry of raw.furniture.slice(0, 40)) {
    if (!entry || typeof entry !== "object" || Array.isArray(entry)) continue;
    const item = entry as Record<string, unknown>;
    if (
      typeof item.placement_id !== "string" ||
      !/^[a-zA-Z0-9_-]{1,64}$/.test(item.placement_id) ||
      ids.has(item.placement_id) ||
      typeof item.kind !== "string" ||
      !FURNITURE_KINDS.has(item.kind as RoomFurnitureKind) ||
      typeof item.x !== "number" || !Number.isFinite(item.x) || item.x < -2.2 || item.x > 2.2 ||
      typeof item.z !== "number" || !Number.isFinite(item.z) || item.z < -2.2 || item.z > 2.2 ||
      typeof item.rotation !== "number" || !Number.isInteger(item.rotation) || item.rotation < 0 || item.rotation > 359
    ) continue;
    ids.add(item.placement_id);
    furniture.push({
      placement_id: item.placement_id,
      kind: item.kind as RoomFurnitureKind,
      x: item.x,
      z: item.z,
      rotation: item.rotation,
    });
  }

  const placedEmployeeIds = new Set<string>();
  const employeePlacements: RoomEmployeePlacement[] = [];
  const rawEmployeePlacements = Array.isArray(raw.employee_placements) ? raw.employee_placements.slice(0, 100) : [];
  for (const entry of rawEmployeePlacements) {
    if (!entry || typeof entry !== "object" || Array.isArray(entry)) continue;
    const item = entry as Record<string, unknown>;
    if (
      typeof item.employee_id !== "string" ||
      !UUID_PATTERN.test(item.employee_id) ||
      placedEmployeeIds.has(item.employee_id) ||
      (allowedEmployeeIds !== undefined && !allowedEmployeeIds.has(item.employee_id)) ||
      typeof item.x !== "number" || !Number.isFinite(item.x) || item.x < -2.2 || item.x > 2.2 ||
      typeof item.z !== "number" || !Number.isFinite(item.z) || item.z < -2.2 || item.z > 2.2 ||
      typeof item.rotation !== "number" || !Number.isInteger(item.rotation) || item.rotation < 0 || item.rotation > 359
    ) continue;
    placedEmployeeIds.add(item.employee_id);
    employeePlacements.push({
      employee_id: item.employee_id,
      x: item.x,
      z: item.z,
      rotation: item.rotation,
    });
  }

  return { schema_version: 1, layout_preset: "starter", furniture, employee_placements: employeePlacements };
}
