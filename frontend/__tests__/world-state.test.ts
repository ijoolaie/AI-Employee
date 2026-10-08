import { describe, expect, it } from "vitest";
import { projectWorldReadModel } from "../features/world/WorldState";
import type { CustomerOffice } from "../types";

const office: CustomerOffice = {
  office_state: "ACTIVE",
  hq_tier: "BUSINESS",
  hq_metrics: {
    plan_code: "business",
    plan_name: "Business",
    subscription_status: "active",
    active_employees: 2,
    employee_limit: 10,
    active_workflows: 1,
    workflow_limit: 5,
    monthly_runs: 20,
    monthly_run_limit: 100,
    monthly_tokens: 2000,
    monthly_token_limit: 10000,
    enabled_capabilities: ["sales"],
  },
  employee_count: 2,
  working_count: 1,
  waiting_count: 0,
  idle_count: 1,
  blocked_count: 0,
  escalated_count: 0,
  employees: [
    {
      id: "e1",
      name: "Sales AI",
      slug: "sales-ai",
      avatar_url: null,
      kind: "sales",
      is_active: true,
      presentation_state: "WORKING",
      latest_run_id: "r1",
      latest_run_status: "success",
      latest_run_created_at: "2026-10-08T10:00:00Z",
      current_work_item: { id: "w1", title: "Qualify lead", status: "running" },
    },
    {
      id: "e2",
      name: "Ops AI",
      slug: "ops-ai",
      avatar_url: null,
      kind: "operations",
      is_active: true,
      presentation_state: "UNKNOWN",
      latest_run_id: null,
      latest_run_status: null,
      latest_run_created_at: null,
      current_work_item: null,
    },
  ],
  pending_approvals: [],
  generated_at: "2026-10-08T10:00:00Z",
};

describe("projectWorldReadModel", () => {
  it("preserves authoritative employee identity and runtime state", () => {
    const world = projectWorldReadModel(office);
    expect(world.employees[0]).toMatchObject({
      id: "e1",
      name: "Sales AI",
      state: "WORKING",
      latestRunId: "r1",
    });
    expect(world.employees[1].state).toBe("IDLE");
  });

  it("derives only presentation capacity metadata from authoritative limits", () => {
    const world = projectWorldReadModel(office);
    expect(world.progression.tier).toBe("BUSINESS");
    expect(world.progression.activeEmployees).toBe(2);
    expect(world.progression.employeeLimit).toBe(10);
    expect(world.progression.completionPercent).toBe(20);
  });
});
