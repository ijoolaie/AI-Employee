import type { WorldEmployee } from "./WorldState";

const WORKING_SWAY_AMPLITUDE = 0.035;
const WORKING_SWAY_SPEED = 0.0014;

/**
 * Small, deterministic upper-body sway for working employees.
 * Static employee GLBs remain unrigged; this is a low-cost presentation cue,
 * not a skeletal walk cycle. Respect reduced-motion preferences.
 */
export function getWorkerBodySway(
  state: WorldEmployee["state"],
  timeMs: number,
  phase: number,
  reducedMotion: boolean,
): number {
  if (state !== "WORKING" || reducedMotion) return 0;
  return Math.sin(timeMs * WORKING_SWAY_SPEED + phase) * WORKING_SWAY_AMPLITUDE;
}
