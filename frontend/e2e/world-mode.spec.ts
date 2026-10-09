import { test, expect } from "@playwright/test";

const authState = JSON.stringify({
  state: {
    accessToken: "e2e-access-token",
    refreshToken: "e2e-refresh-token",
    user: { id: "user-e2e", email: "e2e@example.test", full_name: "E2E Admin" },
    tenant: { id: "tenant-e2e", name: "E2E Tenant" },
  },
  version: 0,
});

const office = {
  success: true,
  data: {
    office_state: "ACTIVE",
    hq_tier: "BUSINESS",
    hq_metrics: {
      plan_code: "business",
      plan_name: "Business",
      subscription_status: "active",
      active_employees: 1,
      employee_limit: 10,
      active_workflows: 1,
      workflow_limit: 5,
      monthly_runs: 2,
      monthly_run_limit: 100,
      monthly_tokens: 100,
      monthly_token_limit: 10000,
      enabled_capabilities: ["sales"],
    },
    employee_count: 1,
    working_count: 1,
    waiting_count: 0,
    idle_count: 0,
    blocked_count: 0,
    escalated_count: 0,
    employees: [{
      id: "employee-e2e",
      name: "Sales AI",
      slug: "sales-ai",
      avatar_url: null,
      kind: "sales",
      is_active: true,
      presentation_state: "WORKING",
      latest_run_id: "run-e2e",
      latest_run_status: "success",
      latest_run_created_at: "2026-10-08T10:00:00Z",
      current_work_item: { id: "work-e2e", title: "Qualify lead", status: "running" },
    }],
    pending_approvals: [],
    generated_at: "2026-10-08T10:00:00Z",
  },
};

test("World Mode renders authoritative employee projection and management bridge", async ({ page }) => {
  await page.addInitScript((state) => localStorage.setItem("aiep-auth", state), authState);
  await page.route("**/customer-dashboard/office", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(office) });
  });
  await page.route("**/analytics/roi", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        data: {
          conversations: 4,
          ai_resolved: 3,
          human_handoffs: 1,
          runs: 2,
          successful_runs: 2,
          orders: 1,
          revenue: 100,
          influenced_orders: 1,
          influenced_revenue: 100,
          ai_resolution_rate: 75,
          handoff_rate: 25,
        },
      }),
    });
  });

  await page.goto("/world");
  await expect(page.getByRole("heading", { name: "World Mode" })).toBeVisible();
  await expect(page.getByText("WORKING 1", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: /Management Mode/i })).toHaveAttribute("href", "/dashboard");

  const canvas = page.getByLabel("AI Company World viewport");
  await expect(canvas).toBeVisible();

  // Use the accessible employee selector so this contract test does not depend on camera projection.
  await page.getByRole("button", { name: "Select Sales AI" }).click({ force: true });

  await expect(page.getByRole("complementary", { name: "Selected employee" })).toBeVisible();
  await expect(page.getByText("Sales AI")).toBeVisible();
  await expect(page.getByText("Qualify lead")).toBeVisible();
  await expect(page.getByRole("link", { name: "Open Employee Management" })).toHaveAttribute("href", "/employees/employee-e2e");
  await expect(page.getByText("Business outcome loop")).toBeVisible();
});
