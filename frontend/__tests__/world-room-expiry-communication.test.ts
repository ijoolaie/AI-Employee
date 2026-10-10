import { describe, expect, it } from "vitest";
import { getRoomLeaseExpiryStatus } from "../features/world/WorldRoomAccessPanel";

const DAY_MS = 24 * 60 * 60 * 1000;
const NOW = Date.parse("2026-10-10T12:00:00.000Z");

describe("World room lease expiry communication", () => {
  it("treats a missing or invalid expiry as unknown", () => {
    expect(getRoomLeaseExpiryStatus(null, NOW)).toEqual({ kind: "unknown", daysRemaining: null });
    expect(getRoomLeaseExpiryStatus("not-a-date", NOW)).toEqual({ kind: "unknown", daysRemaining: null });
  });

  it("warns when a lease has seven days or less remaining", () => {
    expect(getRoomLeaseExpiryStatus(new Date(NOW + 7 * DAY_MS).toISOString(), NOW)).toEqual({
      kind: "urgent",
      daysRemaining: 7,
    });
    expect(getRoomLeaseExpiryStatus(new Date(NOW + 1).toISOString(), NOW)).toEqual({
      kind: "urgent",
      daysRemaining: 1,
    });
  });

  it("does not mark a lease urgent when more than seven days remain", () => {
    expect(getRoomLeaseExpiryStatus(new Date(NOW + 8 * DAY_MS).toISOString(), NOW)).toEqual({
      kind: "active",
      daysRemaining: 8,
    });
  });

  it("flags an expiry at or before now without implying renewal", () => {
    expect(getRoomLeaseExpiryStatus(new Date(NOW).toISOString(), NOW)).toEqual({
      kind: "expired",
      daysRemaining: 0,
    });
    expect(getRoomLeaseExpiryStatus(new Date(NOW - 1).toISOString(), NOW)).toEqual({
      kind: "expired",
      daysRemaining: 0,
    });
  });
});
