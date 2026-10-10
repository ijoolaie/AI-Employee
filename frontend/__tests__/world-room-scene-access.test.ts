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
