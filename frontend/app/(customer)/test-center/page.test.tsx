import { describe, expect, it, vi } from "vitest";

const { get } = vi.hoisted(() => ({
  get: vi.fn(async (path: string) => ({
    data: path.includes("/runs/run-1")
      ? { success: true, data: { id: "run-1", status: "passed", updated_at: "2026-09-03T00:00:00Z" } }
      : { success: true, data: [] },
  })),
}));

vi.mock("@/lib/api", () => ({
  api: {
    get,
    post: vi.fn(async (path: string) => ({
      data: path.endsWith("/execute")
        ? { success: true, data: { run_id: "run-1", task_id: "task-1", status: "dispatched" } }
        : { success: true, data: { id: "run-1", status: "queued" } },
    })),
  },
}));

import { createTestRun, dispatchTestRun, getTestRun } from "@/lib/test-center";

describe("Test Center execution client", () => {
  it("creates a run and dispatches the same run to the worker boundary", async () => {
    const run = await createTestRun({ test_definition_id: "definition-1" });
    const dispatch = await dispatchTestRun(run.id);

    expect(run.id).toBe("run-1");
    expect(dispatch).toEqual({ run_id: "run-1", task_id: "task-1", status: "dispatched" });
  });

  it("fetches the latest selected run state for lifecycle refresh", async () => {
    const run = await getTestRun("run-1");

    expect(run).toMatchObject({ id: "run-1", status: "passed" });
    expect(get).toHaveBeenCalledWith("/test-center/runs/run-1");
  });
});
