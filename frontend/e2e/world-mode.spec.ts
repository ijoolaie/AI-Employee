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
  const employeeSelector = page.getByRole("button", { name: "Select Sales AI" });
  await employeeSelector.focus();
  await employeeSelector.press("Enter");

  const employeePanel = page.getByRole("complementary", { name: "Selected employee" });
  await expect(employeePanel).toBeVisible();
  await expect(employeePanel.getByText("Sales AI", { exact: true })).toBeVisible();
  await expect(employeePanel.getByText("Qualify lead", { exact: true })).toBeVisible();
  await expect(employeeSelector).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("link", { name: "Open Employee Management" })).toHaveAttribute("href", "/employees/employee-e2e");

  // Selection is keyboard-accessible and Escape returns the world to its unselected state.
  await page.keyboard.press("Escape");
  await expect(employeePanel).toBeHidden();
  await expect(employeeSelector).toHaveAttribute("aria-pressed", "false");
  await expect(page.getByText("Business outcome loop")).toBeVisible();
});


test("World room offer loads server prices and creates an order without charging", async ({ page }) => {
  await page.addInitScript((state) => localStorage.setItem("aiep-auth", state), authState);
  await page.route("**/customer-dashboard/office", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(office) });
  });
  await page.route("**/analytics/roi", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ success: true, data: { conversations: 0, ai_resolved: 0, human_handoffs: 0, runs: 0, successful_runs: 0, orders: 0, revenue: 0, influenced_orders: 0, influenced_revenue: 0, ai_resolution_rate: 0, handoff_rate: 0 } }),
    });
  });
  await page.route("**/world-commerce/catalogue", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        data: [{
          id: "room-offer-e2e",
          code: "room_monthly",
          item_type: "room",
          name: "اتاق توسعه",
          description: "پیشنهاد آزمایشی",
          is_free: false,
          price_options: {
            IRR: { amount: "2500000", providers: ["manual"], payment_methods: ["manual_transfer"] },
            USD: { amount: "12", providers: ["sandbox"], payment_methods: ["gateway"] },
            USDT: { amount: "10", providers: ["crypto-sandbox"], payment_methods: ["crypto"] },
          },
        }],
      }),
    });
  });

  let orderPayload: Record<string, unknown> | null = null;
  await page.route("**/world-commerce/orders", async (route) => {
    orderPayload = route.request().postDataJSON() as Record<string, unknown>;
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        data: {
          id: "order-e2e-001",
          item_code_snapshot: "room_monthly",
          amount: "12",
          currency: "USD",
          payment_method: "gateway",
          payment_provider: "sandbox",
          status: "pending",
        },
      }),
    });
  });

  await page.goto("/world");
  await expect(page.getByRole("heading", { name: "World Mode" })).toBeVisible();
  const canvas = page.getByLabel("AI Company World viewport");
  await expect(canvas).toBeVisible();

  // Walk toward the locked-room entrance; avoid relying on a 3D pixel coordinate.
  await canvas.focus();
  await page.keyboard.down("s");
  await page.waitForTimeout(900);
  await page.keyboard.up("s");
  const inspectRoom = page.getByRole("button", { name: /Locked room nearby/ });
  await expect(inspectRoom).toBeVisible({ timeout: 5000 });
  await canvas.press("e");

  const offer = page.getByRole("dialog", { name: "اتاق بعدی شرکت" });
  await expect(offer).toBeVisible();
  await expect(offer.getByText("اتاق توسعه", { exact: true })).toBeVisible();
  await expect(offer.getByText("2500000 IRR", { exact: true })).toBeVisible();

  await offer.getByRole("button", { name: "دلار آمریکا" }).click();
  await expect(offer.getByText("12 USD", { exact: true })).toBeVisible();
  await offer.getByRole("button", { name: "ثبت سفارش (بدون پرداخت)" }).click();
  await expect(offer.getByText("سفارش ثبت شد؛ پرداخت انجام نشده است.")).toBeVisible();
  await expect(offer.getByText("شناسه سفارش: order-e2e-001")).toBeVisible();

  expect(orderPayload).not.toBeNull();
  expect(orderPayload).toMatchObject({
    item_code: "room_monthly",
    currency: "USD",
    payment_method: "gateway",
    payment_provider: "sandbox",
  });
  expect(orderPayload).toHaveProperty("idempotency_key");
  expect(orderPayload).not.toHaveProperty("amount");
});
