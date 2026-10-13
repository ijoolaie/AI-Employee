import { describe, expect, it } from "vitest";
import { getWorkerBodySway } from "../features/world/WorldAnimation";

describe("getWorkerBodySway", () => {
  it("keeps non-working employee states still", () => {
    expect(getWorkerBodySway("IDLE", 1000, 0, false)).toBe(0);
    expect(getWorkerBodySway("WAITING_APPROVAL", 1000, 0, false)).toBe(0);
  });

  it("respects reduced-motion preferences", () => {
    expect(getWorkerBodySway("WORKING", 1000, 0.5, true)).toBe(0);
  });

  it("produces a small deterministic sway for working employees", () => {
    const quarterCycleMs = (Math.PI / 2) / 0.0014;
    expect(getWorkerBodySway("WORKING", quarterCycleMs, 0, false)).toBeCloseTo(0.035);
    expect(getWorkerBodySway("WORKING", quarterCycleMs, 0, false)).toBe(
      getWorkerBodySway("WORKING", quarterCycleMs, 0, false),
    );
  });

  it("uses per-employee phase to avoid synchronized motion", () => {
    expect(getWorkerBodySway("WORKING", 500, 0, false)).not.toBe(
      getWorkerBodySway("WORKING", 500, 1.7, false),
    );
  });
});
