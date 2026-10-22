import { test, expect } from "@playwright/test";
import { mkdir } from "node:fs/promises";

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
  // This full World smoke includes WebGL interaction and two viewport captures; allow slower software-rendered CI runners to finish the complete acceptance path.
  test.setTimeout(60_000);
  await page.emulateMedia({ reducedMotion: "reduce" });
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
  await page.route("**/world-commerce/catalogue", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ success: true, data: [{ code: "room-e2e", item_type: "room", is_free: false }] }),
    });
  });
  await page.route("**/world-commerce/room-inventory", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ success: true, data: [] }),
    });
  });
  await page.route("**/world-commerce/room-inventory/room-e2e/access", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        data: { item_code: "room-e2e", granted: false, reason: "not_owned", room_instance_id: null, expires_at: null },
      }),
    });
  });

  const browserErrors: string[] = [];
  const serverErrors: string[] = [];
  const materialWarnings: string[] = [];
  page.on("pageerror", (error) => browserErrors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") browserErrors.push(message.text());
    if (message.type() === "warning" && message.text().includes("THREE.Material: parameter 'map' has value of undefined")) {
      materialWarnings.push(message.text());
    }
  });
  page.on("response", (response) => {
    if (response.status() >= 500) serverErrors.push(`${response.status()} ${response.url()}`);
  });

  await page.goto("/world");
  await expect(page.getByRole("heading", { name: "World Mode" })).toBeVisible();
  await expect(page.getByText("WORKING 1", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: /Management Mode/i })).toHaveAttribute("href", "/dashboard");

  const canvas = page.getByLabel("AI Company World viewport");
  await expect(canvas).toBeVisible();
  await expect.poll(() => canvas.getAttribute("data-worker-asset-state"), { timeout: 10_000 }).toBe("glb-loaded");
  expect(materialWarnings, "World scene should not pass an undefined map option to Three.js materials").toEqual([]);

  // Verify that camera controls change the actual scene distance, not just the control UI.
  const zoomIn = page.getByRole("button", { name: "Zoom in" });
  const zoomOut = page.getByRole("button", { name: "Zoom out" });
  const resetView = page.getByRole("button", { name: "Reset world view" });
  const overviewDistance = Number(await canvas.getAttribute("data-camera-distance"));
  for (let step = 0; step < 5; step += 1) await zoomIn.click();
  const closeupDistance = Number(await canvas.getAttribute("data-camera-distance"));
  expect(closeupDistance).toBeLessThan(overviewDistance);
  await zoomOut.click();
  expect(Number(await canvas.getAttribute("data-camera-distance"))).toBeGreaterThan(closeupDistance);
  await resetView.click();
  expect(Number(await canvas.getAttribute("data-camera-distance"))).toBe(31);

  // Use the accessible employee selector so this contract test does not depend on camera projection.
  const employeeSelector = page.getByRole("button", { name: "Select Sales AI" });
  await employeeSelector.evaluate((element) => (element as HTMLButtonElement).focus());
  await expect(employeeSelector).toBeFocused();
  await page.keyboard.press("Enter");

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


  // Exercise mobile pointer panning before expensive visual captures; software-rendered CI
  // can stall pointer dispatch after repeated full-page WebGL screenshots/resizes.
  await page.setViewportSize({ width: 390, height: 844 });
  // Let the WebGL renderer finish its responsive resize before sending mobile camera input.
  await page.waitForTimeout(300);
  await canvas.evaluate((element) => element.dispatchEvent(new CustomEvent("world:reset")));
  const mobileOverviewDistance = Number(await canvas.getAttribute("data-camera-distance"));
  // One equivalent zoom event avoids repeated browser evaluations on software-rendered CI.
  await canvas.evaluate((element) => element.dispatchEvent(new CustomEvent("world:zoom", { detail: { delta: 0.12 } })));
  const mobileCloseupDistance = Number(await canvas.getAttribute("data-camera-distance"));
  expect(mobileCloseupDistance).toBeLessThan(mobileOverviewDistance);
  await canvas.evaluate((element) => element.dispatchEvent(new CustomEvent("world:reset")));
  expect(Number(await canvas.getAttribute("data-camera-distance"))).toBe(31);
  await page.waitForTimeout(250);
  await canvas.evaluate((element) => {
    (window as Window & { __worldPanEvents?: number }).__worldPanEvents = 0;
    element.addEventListener("world:pan", () => {
      const state = window as Window & { __worldPanEvents?: number };
      state.__worldPanEvents = (state.__worldPanEvents ?? 0) + 1;
    });
  });
  const mobileCanvasBox = await canvas.boundingBox();
  expect(mobileCanvasBox).toBeTruthy();
  if (mobileCanvasBox) {
    await page.mouse.move(mobileCanvasBox.x + mobileCanvasBox.width * 0.55, mobileCanvasBox.y + mobileCanvasBox.height * 0.55);
    await page.mouse.down();
    await page.mouse.move(mobileCanvasBox.x + mobileCanvasBox.width * 0.68, mobileCanvasBox.y + mobileCanvasBox.height * 0.61, { steps: 5 });
    await page.mouse.up();
    await expect.poll(() => page.evaluate(() => (window as Window & { __worldPanEvents?: number }).__worldPanEvents ?? 0))
      .toBeGreaterThan(0);
  }

  // Capture real-browser visual evidence from the same deterministic fixture at both target sizes.
  // These artifacts support human review; they do not constitute visual acceptance by themselves.
  await mkdir("artifacts/world-visual-review", { recursive: true });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: "artifacts/world-visual-review/world-desktop.png", fullPage: false });
  await canvas.evaluate((element) => element.dispatchEvent(new CustomEvent("world:reset")));
  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: "artifacts/world-visual-review/world-mobile.png", fullPage: false });
  // Verify mobile HUD/controls at a narrow, target, and wider-narrow viewport, and retain full-page review artifacts.
  for (const width of [360, 390, 430]) {
    await page.setViewportSize({ width, height: 844 });
    await page.waitForTimeout(250);
    await page.screenshot({ path: "artifacts/world-visual-review/world-mobile-" + width + ".png", fullPage: true });
    const probeHud = await page.getByTestId("world-viewport-hud").boundingBox();
    const probeControls = await page.getByRole("group", { name: "World camera controls" }).boundingBox();
    const probeJoystick = await page.getByLabel("World movement joystick").boundingBox();
    expect(probeHud && probeControls && probeJoystick).toBeTruthy();
    if (probeHud && probeControls && probeJoystick) {
      const overlapsProbe = (a: NonNullable<typeof probeHud>, b: NonNullable<typeof probeControls>) =>
        a.x < b.x + b.width && a.x + a.width > b.x && a.y < b.y + b.height && a.y + a.height > b.y;
      expect(probeControls.x).toBeGreaterThanOrEqual(0);
      expect(probeControls.x + probeControls.width).toBeLessThanOrEqual(width);
      expect(probeJoystick.x).toBeGreaterThanOrEqual(0);
      expect(probeJoystick.x + probeJoystick.width).toBeLessThanOrEqual(width);
      expect(overlapsProbe(probeHud, probeControls)).toBe(false);
      expect(overlapsProbe(probeJoystick, probeControls)).toBe(false);
      expect(overlapsProbe(probeJoystick, probeHud)).toBe(false);
    }
  }
  await page.setViewportSize({ width: 390, height: 844 });

  const hud = page.getByTestId("world-viewport-hud");
  const cameraControls = page.getByRole("group", { name: "World camera controls" });
  const joystick = page.getByLabel("World movement joystick");
  await expect(hud).toBeVisible();
  await expect(cameraControls).toBeVisible();
  await expect(joystick).toBeVisible();
  const hudBox = await hud.boundingBox();
  const controlsBox = await cameraControls.boundingBox();
  const joystickBox = await joystick.boundingBox();
  expect(hudBox && controlsBox && joystickBox).toBeTruthy();
  if (hudBox && controlsBox && joystickBox) {
    const overlaps = (a: NonNullable<typeof hudBox>, b: NonNullable<typeof controlsBox>) =>
      a.x < b.x + b.width && a.x + a.width > b.x &&
      a.y < b.y + b.height && a.y + a.height > b.y;
    // Mobile HUD stays in the viewport's top-left; camera controls stay bottom-right.
    expect(overlaps(hudBox, controlsBox), `mobile HUD and camera controls overlap: hud=${JSON.stringify(hudBox)} controls=${JSON.stringify(controlsBox)}`).toBe(false);
    expect(controlsBox.x).toBeGreaterThanOrEqual(0);
    expect(controlsBox.x + controlsBox.width).toBeLessThanOrEqual(390);
    expect(joystickBox.x).toBeGreaterThanOrEqual(0);
    expect(joystickBox.x + joystickBox.width).toBeLessThanOrEqual(390);
    expect(overlaps(joystickBox, controlsBox), "mobile joystick and camera controls overlap").toBe(false);
    expect(overlaps(joystickBox, hudBox), "mobile joystick and HUD overlap").toBe(false);
  }

  await canvas.evaluate((element) => element.dispatchEvent(new CustomEvent("world:reset")));
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.waitForTimeout(250);
  const desktopCanvasBox = await canvas.boundingBox();
  const desktopControlsBox = await cameraControls.boundingBox();
  expect(desktopCanvasBox && desktopControlsBox).toBeTruthy();
  if (desktopCanvasBox && desktopControlsBox) {
    expect(desktopControlsBox.x).toBeLessThanOrEqual(desktopCanvasBox.x + 24);
    expect(desktopControlsBox.y).toBeGreaterThan(desktopCanvasBox.y + desktopCanvasBox.height / 2);
  }
  await expect(hud.getByText(/WASD/)).toBeVisible();

  await expect(page.getByText("Business outcome loop")).toBeVisible();
  expect(browserErrors, "browser console/page errors during World viewport smoke").toEqual([]);
  expect(serverErrors, "unexpected 5xx responses during World viewport smoke").toEqual([]);
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
  const inspectRoom = page.getByRole("button", { name: /Locked room nearby/ });
  // Keep moving until the proximity affordance appears; eased movement makes fixed holds brittle.
  await expect(inspectRoom).toBeVisible({ timeout: 7000 });
  await page.keyboard.up("s");
  await canvas.press("e");

  const offer = page.getByRole("dialog", { name: "اجاره یا تمدید اتاق شرکت" });
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
      body: JSON.stringify({ success: true, data: [{ id: "room-offer-e2e", code: "room_monthly", item_type: "room", name: "اتاق توسعه", description: "پیشنهاد آزمایشی", is_free: false, price_options: { IRR: { amount: "2500000", providers: ["manual"], payment_methods: ["manual_transfer"] }, USD: { amount: "12", providers: ["sandbox"], payment_methods: ["gateway"] }, USDT: { amount: "10", providers: ["crypto-sandbox"], payment_methods: ["crypto"] } } }] }),
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
      body: JSON.stringify({ success: true, data: { item_code: "room_monthly", granted, reason: granted && Date.parse(expiresAt) <= Date.now() ? "lease_expired" : granted ? "active" : "not_entitled", room_instance_id: "room-instance-e2e-001", expires_at: expiresAt } }),
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

test("expired room access offers a renewal order without opening the 3D scene", async ({ page }) => {
  await mockRoomSceneAccess(page, "2020-01-01T00:00:00.000Z", true);
  const canvas = page.getByLabel("AI Company World viewport");
  await expect(canvas).toHaveAttribute("data-room-access-state", "denied");
  await canvas.focus();
  await page.keyboard.down("s");
  const inspectRoom = page.getByRole("button", { name: /Locked room nearby/ });
  // Use the real proximity affordance rather than a timing assumption.
  await expect(inspectRoom).toBeVisible({ timeout: 7000 });
  await page.keyboard.up("s");
  await canvas.press("e");
  const access = page.getByRole("dialog", { name: "دسترسی اتاق شرکت" });
  await expect(access.getByRole("alert")).toContainText("اجاره اتاق منقضی شده است");
  await access.getByRole("button", { name: "ثبت سفارش تمدید اجاره" }).click();
  await expect(page.getByRole("dialog", { name: "اجاره یا تمدید اتاق شرکت" })).toBeVisible();
  await expect(canvas).toHaveAttribute("data-room-access-state", "denied");
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

test("World room editor surfaces a server-side stale-layout conflict", async ({ page }) => {
  await mockRoomSceneAccess(page, "2035-01-01T00:00:00.000Z", true);
  await page.route("**/world-commerce/room-inventory/room_monthly/scene-config", async (route) => {
    await route.fulfill({
      status: 409,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Room layout changed since it was loaded; refresh before saving" }),
    });
  });

  await page.getByRole("button", { name: "Customize room" }).click();
  const editor = page.getByRole("dialog", { name: "Customize your room" });
  await editor.getByRole("button", { name: "Save layout" }).click();
  await expect(editor.getByRole("alert")).toContainText("Room layout changed since it was loaded");
});


test("World Mode keeps procedural employees when the local GLB asset cannot load", async ({ page }) => {
  await page.addInitScript((state) => localStorage.setItem("aiep-auth", state), authState);
  await page.route("**/customer-dashboard/office", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(office) });
  });
  await page.route("**/assets/world/employee-base.glb", async (route) => route.abort());
  await page.goto("/world");
  const canvas = page.getByLabel("AI Company World viewport");
  await expect(canvas).toBeVisible();
  await expect.poll(() => canvas.getAttribute("data-worker-asset-state"), { timeout: 10_000 }).toBe("procedural-fallback");
});
