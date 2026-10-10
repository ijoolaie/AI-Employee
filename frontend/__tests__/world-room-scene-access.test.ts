import { describe, expect, it } from "vitest";
import { isRoomSceneAccessUsable } from "../features/world/WorldRoomSceneAccess";

const futureExpiry = "2035-01-01T00:00:00.000Z";
const now = Date.parse("2030-01-01T00:00:00.000Z");

describe("isRoomSceneAccessUsable", () => {
  it("allows a granted room instance with a future server expiry", () => {
    expect(isRoomSceneAccessUsable({ granted: true, roomInstanceId: "room-1", expiresAt: futureExpiry }, false, now)).toBe(true);
  });

  it("denies a prior grant when the latest authorization query errors", () => {
    expect(isRoomSceneAccessUsable({ granted: true, roomInstanceId: "room-1", expiresAt: futureExpiry }, true, now)).toBe(false);
  });

  it("denies expired, missing-instance, missing-expiry and invalid-expiry responses", () => {
    expect(isRoomSceneAccessUsable({ granted: true, roomInstanceId: "room-1", expiresAt: "2029-01-01T00:00:00Z" }, false, now)).toBe(false);
    expect(isRoomSceneAccessUsable({ granted: true, roomInstanceId: null, expiresAt: futureExpiry }, false, now)).toBe(false);
    expect(isRoomSceneAccessUsable({ granted: true, roomInstanceId: "room-1", expiresAt: null }, false, now)).toBe(false);
    expect(isRoomSceneAccessUsable({ granted: true, roomInstanceId: "room-1", expiresAt: "not-a-date" }, false, now)).toBe(false);
  });

  it("denies an explicit server denial", () => {
    expect(isRoomSceneAccessUsable({ granted: false, roomInstanceId: "room-1", expiresAt: futureExpiry }, false, now)).toBe(false);
  });
});

import { DEFAULT_ROOM_SCENE_CONFIG, normalizeRoomSceneConfig } from "../features/world/WorldRoomSceneConfig";

describe("normalizeRoomSceneConfig", () => {
  it("uses the safe starter layout for legacy empty scene_config", () => {
    expect(normalizeRoomSceneConfig({})).toEqual(DEFAULT_ROOM_SCENE_CONFIG);
  });

  it("preserves a valid versioned room layout", () => {
    const config = normalizeRoomSceneConfig({
      schema_version: 1,
      layout_preset: "starter",
      furniture: [{ placement_id: "desk-1", kind: "desk", x: 1, z: -2, rotation: 90 }],
    });
    expect(config.furniture).toEqual([{ placement_id: "desk-1", kind: "desk", x: 1, z: -2, rotation: 90 }]);
  });

  it("filters unknown, duplicate, malformed and out-of-bounds placements", () => {
    const config = normalizeRoomSceneConfig({
      schema_version: 1,
      layout_preset: "starter",
      furniture: [
        { placement_id: "valid", kind: "plant", x: 2, z: 2, rotation: 0 },
        { placement_id: "valid", kind: "desk", x: 0, z: 0, rotation: 0 },
        { placement_id: "outside", kind: "desk", x: 2.3, z: 0, rotation: 0 },
        { placement_id: "unknown", kind: "script", x: 0, z: 0, rotation: 0 },
        { placement_id: "bad-rotation", kind: "chair", x: 0, z: 0, rotation: 360 },
      ],
    });
    expect(config.furniture).toEqual([{ placement_id: "valid", kind: "plant", x: 2, z: 2, rotation: 0 }]);
  });

  it("does not pass through unsupported schema versions", () => {
    expect(normalizeRoomSceneConfig({ schema_version: 99, layout_preset: "custom", furniture: [] })).toEqual(DEFAULT_ROOM_SCENE_CONFIG);
  });
});

