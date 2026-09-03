import { describe, expect, it, vi } from "vitest";

import { createTestRun, dispatchTestRun } from "@/lib/test-center";

vi.mock("@/lib/api", () => ({
  api: {
    post: vi.fn(async (path: string) => ({
      data: path.endsWith("/execute")
        ? { success: true, data: { run_id: "run-1", task_id: "task-1", status: "dispatched" } }
        : { success: true, data: { id: "run-1", status: "queued" } },
    })),
  },
}));

describe("Test Center execution client", () => {
  it("creates a run and dispatches the same run to the worker boundary", async () => {
    const run = await createTestRun({ test_definition_id: "definition-1" });
    const dispatch = await dispatchTestRun(run.id);

    expect(run.id).toBe("run-1");
    expect(dispatch).toEqual({ run_id: "run-1", task_id: "task-1", status: "dispatched" });
  });
});
