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
      id: "2e3f1a10-0e6a-4e9d-8b9a-32c5d37f0b11",
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
  await expect(page.getByRole("link", { name: "Open Employee Management" })).toHaveAttribute("href", "/employees/2e3f1a10-0e6a-4e9d-8b9a-32c5d37f0b11");

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
  await page.route("**/world-commerce/entitlements", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ success: true, data: [] }),
    });
  });
  await page.route("**/world-commerce/room-inventory", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ success: true, data: [] }) });
  });
  await page.route("**/world-commerce/room-inventory/room_monthly/access", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ success: true, data: { item_code: "room_monthly", granted: false, reason: "not_provisioned", room_instance_id: null, expires_at: null } }),
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

// Regression: the Three.js scene must deny access even when the API returns a stale/expired grant.
async function mockRoomSceneAccess(page: import("@playwright/test").Page, expiresAt: string, granted = true) {
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
      body: JSON.stringify({ success: true, data: [{ code: "room_monthly", item_type: "room", is_free: false }] }),
    });
  });
  await page.route("**/world-commerce/room-inventory", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ success: true, data: [{ room_instance_id: "room-instance-e2e-001", item_code: "room_monthly", status: "provisioned", expires_at: expiresAt, updated_at: "2030-01-01T00:00:00.000Z", scene_config: {} }] }),
    });
  });
  await page.route("**/world-commerce/room-inventory/room_monthly/access", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ success: true, data: { item_code: "room_monthly", granted, reason: granted ? "active" : "not_entitled", room_instance_id: "room-instance-e2e-001", expires_at: expiresAt } }),
    });
  });
  await page.goto("/world");
}

test("World 3D room opens only for an unexpired server authorization", async ({ page }) => {
  await mockRoomSceneAccess(page, "2035-01-01T00:00:00.000Z", true);
  const canvas = page.getByLabel("AI Company World viewport");
  await expect(canvas).toBeVisible();
  await expect(canvas).toHaveAttribute("data-room-access-state", "granted");
  await expect(canvas).toHaveAttribute("data-room-instance-id", "room-instance-e2e-001");
});

test("World 3D room stays locked when a grant has expired", async ({ page }) => {
  await mockRoomSceneAccess(page, "2020-01-01T00:00:00.000Z", true);
  const canvas = page.getByLabel("AI Company World viewport");
  await expect(canvas).toBeVisible();
  await expect(canvas).toHaveAttribute("data-room-access-state", "denied");
  await expect(canvas).not.toHaveAttribute("data-room-instance-id", /.+/);
});

test("World room layout editor persists and applies furniture placements", async ({ page }) => {
  await mockRoomSceneAccess(page, "2035-01-01T00:00:00.000Z", true);
  const canvas = page.getByLabel("AI Company World viewport");
  await expect(canvas).toHaveAttribute("data-room-access-state", "granted");
  await expect(canvas).toHaveAttribute("data-room-furniture-count", "2");

  const savedPayloads: Array<{ expected_updated_at: string; scene_config: { schema_version: number; layout_preset: string; furniture: Array<{ placement_id: string; kind: string; x: number; z: number; rotation: number }>; employee_placements: Array<{ employee_id: string; x: number; z: number; rotation: number }> } }> = [];
  await page.route("**/world-commerce/room-inventory/room_monthly/scene-config", async (route) => {
    savedPayloads.push(route.request().postDataJSON());
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        data: {
          room_instance_id: "room-instance-e2e-001",
          item_code: "room_monthly",
          scene_config: savedPayloads[0].scene_config,
          updated_at: "2035-01-01T00:00:00.000Z",
        },
      }),
    });
  });

  await page.getByRole("button", { name: "Customize room" }).click();
  const editor = page.getByRole("dialog", { name: "Customize your room" });
  await expect(editor).toBeVisible();
  await editor.getByRole("button", { name: /Add chair/ }).click();
  await editor.getByRole("button", { name: "Save layout" }).click();
  await expect(editor.getByRole("status")).toContainText("Room layout saved to the server.");
  await expect(canvas).toHaveAttribute("data-room-furniture-count", "3");
  expect(savedPayloads).toHaveLength(1);
  const savedPayload = savedPayloads[0];
  expect(savedPayload.scene_config.schema_version).toBe(1);
  expect(savedPayload.scene_config.layout_preset).toBe("starter");
  expect(savedPayload.scene_config.furniture).toHaveLength(3);
  expect(savedPayload.scene_config.furniture.every((item) => item.x >= -2.2 && item.x <= 2.2 && item.z >= -2.2 && item.z <= 2.2)).toBe(true);
});

test("World room editor persists an active tenant employee placement", async ({ page }) => {
  await mockRoomSceneAccess(page, "2035-01-01T00:00:00.000Z", true);
  const canvas = page.getByLabel("AI Company World viewport");
  await expect(canvas).toHaveAttribute("data-room-access-state", "granted");
  await expect(canvas).toHaveAttribute("data-room-employee-count", "0");

  const savedPayloads: Array<{ expected_updated_at: string; scene_config: { schema_version: number; layout_preset: string; furniture: unknown[]; employee_placements: Array<{ employee_id: string; x: number; z: number; rotation: number }> } }> = [];
  await page.route("**/world-commerce/room-inventory/room_monthly/scene-config", async (route) => {
    savedPayloads.push(route.request().postDataJSON());
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        data: {
          room_instance_id: "room-instance-e2e-001",
          item_code: "room_monthly",
          scene_config: savedPayloads[0].scene_config,
          updated_at: "2035-01-01T00:00:00.000Z",
        },
      }),
    });
  });

  await page.getByRole("button", { name: "Customize room" }).click();
  const editor = page.getByRole("dialog", { name: "Customize your room" });
  await editor.getByRole("button", { name: "Place in room" }).click();
  await editor.getByRole("button", { name: "Save layout" }).click();
  await expect(editor.getByRole("status")).toContainText("Room layout saved to the server.");
  await expect(canvas).toHaveAttribute("data-room-employee-count", "1");
  expect(savedPayloads).toHaveLength(1);
  expect(savedPayloads[0].scene_config.employee_placements).toEqual([
    { employee_id: "2e3f1a10-0e6a-4e9d-8b9a-32c5d37f0b11", x: 0, z: 0, rotation: 0 },
  ]);
});
