import { describe, expect, it } from "vitest";
import { canOccupyGround, getWalkBlockers } from "../features/world/WorldNavigation";

describe("World ground navigation", () => {
  const blockers = getWalkBlockers([{ x: 0, z: -7 }]);

  it("blocks the player from entering the coffee-table footprint", () => {
    expect(canOccupyGround(0, 3, blockers)).toBe(false);
    expect(canOccupyGround(1.5, 3, blockers)).toBe(true);
  });

  it("blocks workstation footprints but allows nearby aisle space", () => {
    expect(canOccupyGround(-1.8, -8.9, blockers)).toBe(false);
    expect(canOccupyGround(5, -7, blockers)).toBe(true);
  });

  it("keeps movement inside the office walkable bounds", () => {
    expect(canOccupyGround(15.9, 8.9, [])).toBe(true);
    expect(canOccupyGround(16.1, 0, [])).toBe(false);
    expect(canOccupyGround(0, 9.3, [])).toBe(false);
  });
});
