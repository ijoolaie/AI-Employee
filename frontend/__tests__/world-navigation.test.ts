import { describe, expect, it } from "vitest";
import { canOccupyGround, getWalkBlockers } from "../features/world/WorldNavigation";

describe("World ground navigation", () => {
  const upperRoomBlockers = getWalkBlockers([{ x: 0, z: -7 }]);

  it("blocks the player from entering the coffee-table footprint", () => {
    expect(canOccupyGround(0, 3, upperRoomBlockers)).toBe(false);
    expect(canOccupyGround(1.5, 3, upperRoomBlockers)).toBe(true);
  });

  it("blocks workstation footprints but leaves the circulation aisle clear", () => {
    expect(canOccupyGround(-1.8, -8.9, upperRoomBlockers)).toBe(false);
    expect(canOccupyGround(0, -2, upperRoomBlockers)).toBe(true);
  });

  it("blocks room partition walls but leaves the centered upper-room doorway open", () => {
    expect(canOccupyGround(4.5, -7, upperRoomBlockers)).toBe(false);
    expect(canOccupyGround(0, -3, upperRoomBlockers)).toBe(true);
    expect(canOccupyGround(2.2, -3, upperRoomBlockers)).toBe(false);
  });

  it("leaves the lower-room doorway open and blocks its outer wall", () => {
    const lowerRoomBlockers = getWalkBlockers([{ x: 6, z: 6 }]);
    expect(canOccupyGround(6, 2, lowerRoomBlockers)).toBe(true);
    expect(canOccupyGround(9, 2, lowerRoomBlockers)).toBe(false);
    expect(canOccupyGround(6, 10, lowerRoomBlockers)).toBe(false);
  });

  it("keeps movement inside the office walkable bounds", () => {
    expect(canOccupyGround(15.9, 8.9, [])).toBe(true);
    expect(canOccupyGround(16.1, 0, [])).toBe(false);
    expect(canOccupyGround(0, 9.3, [])).toBe(false);
  });
});
