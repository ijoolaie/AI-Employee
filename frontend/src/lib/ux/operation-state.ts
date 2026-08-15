export type OperationState =
  | "idle"
  | "submitting"
  | "queued"
  | "running"
  | "waiting_approval"
  | "succeeded"
  | "failed"
  | "cancelled";

export const operationStateLabel: Record<OperationState, string> = {
  idle: "Ready",
  submitting: "Submitting",
  queued: "Queued",
  running: "Running",
  waiting_approval: "Approval required",
  succeeded: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
};
