import { test, expect } from "@playwright/test";

test.describe("commercial portal sign-in routing", () => {
  test("portal query selects matching heading and marks the active portal", async ({ page }) => {
    for (const portal of ["customer", "reseller", "vendor"] as const) {
      await page.goto(`/login?portal=${portal}`);
      const label = portal === "customer" ? "Customer portal" : portal === "reseller" ? "Reseller portal" : "Vendor portal";
      await expect(page.getByRole("heading", { name: `Sign in to ${label}` })).toBeVisible();
      const nav = page.getByRole("navigation", { name: "Choose portal" });
      await expect(nav.getByRole("link", { name: label })).toHaveAttribute("aria-current", "page");
      for (const other of ["customer", "reseller", "vendor"] as const) {
        const otherLabel = other === "customer" ? "Customer portal" : other === "reseller" ? "Reseller portal" : "Vendor portal";
        await expect(nav.getByRole("link", { name: otherLabel })).toHaveAttribute("href", `/login/${other}`);
      }
    }
  });

  test("successful sign-in routes each account to its permitted portal", async ({ page }) => {
    const scenarios = [
      { kind: "vendor", requested: "vendor", expectedPath: "/vendor/dashboard", platformAdmin: false },
      { kind: "reseller", requested: "reseller", expectedPath: "/reseller/dashboard", platformAdmin: false },
      { kind: "customer", requested: "customer", expectedPath: "/dashboard", platformAdmin: false },
      { kind: "customer", requested: "vendor", expectedPath: "/dashboard", platformAdmin: false },
      { kind: "vendor", requested: "reseller", expectedPath: "/vendor/dashboard", platformAdmin: false },
      { kind: "reseller", requested: "customer", expectedPath: "/reseller/dashboard", platformAdmin: false },
      { kind: "vendor", requested: "customer", expectedPath: "/admin", platformAdmin: true },
    ] as const;
    let activeScenario = 0;
    const uncaughtPageErrors: string[] = [];
    page.on("pageerror", (error) => uncaughtPageErrors.push(error.message));

    // Never send fake E2E credentials to the real API. A null payload keeps
    // unrelated dashboard queries from accidentally rendering malformed data.
    await page.route("**/api/**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ success: true, data: null }),
      });
    });
    await page.route("**/auth/login", async (route) => {
      expect(route.request().method()).toBe("POST");
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          data: { access_token: "e2e-access-token", refresh_token: "e2e-refresh-token", token_type: "bearer" },
        }),
      });
    });
    await page.route("**/auth/me", async (route) => {
      const scenario = scenarios[activeScenario];
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          data: {
            user: {
              id: `user-${activeScenario}`,
              email: "portal@example.test",
              full_name: "Portal E2E",
              tenant_id: `tenant-${activeScenario}`,
              is_active: true,
              is_platform_admin: scenario.platformAdmin,
            },
            tenant: {
              id: `tenant-${activeScenario}`,
              name: "Portal Test Tenant",
              slug: "portal-test",
              status: "active",
              tenant_kind: scenario.kind,
              access_granted: true,
            },
          },
        }),
      });
    });
    await page.route("**/edition/reseller/customers", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ success: true, data: [] }),
      });
    });

    for (activeScenario = 0; activeScenario < scenarios.length; activeScenario += 1) {
      const scenario = scenarios[activeScenario];
      await page.goto(`/login?portal=${scenario.requested}`);
      await page.getByLabel("Tenant slug").fill("portal-test");
      await page.getByLabel("Email").fill("portal@example.test");
      await page.getByLabel("Password").fill("test-password-only");
      await page.getByRole("button", { name: "Sign in" }).click();
      await expect.poll(() => new URL(page.url()).pathname).toBe(scenario.expectedPath);
      if (scenario.kind === "reseller") {
        await page.setViewportSize({ width: 390, height: 844 });
        const mobileNavigation = page.getByRole("combobox", { name: "Reseller navigation" });
        await expect(mobileNavigation).toBeVisible();
        await expect(mobileNavigation.locator("option")).toHaveCount(13);
        await expect(mobileNavigation).toHaveValue("/reseller/dashboard");
        await mobileNavigation.selectOption("/reseller/integrations");
        await expect.poll(() => new URL(page.url()).pathname).toBe("/reseller/integrations");
        await expect(mobileNavigation).toHaveValue("/reseller/integrations");
      }
      if (scenario.expectedPath === "/vendor/dashboard") {
        await expect(page.getByRole("heading", { name: "Vendor portal" })).toBeVisible();
      }
      await expect.poll(() => uncaughtPageErrors).toEqual([]);
      await page.evaluate(() => localStorage.removeItem("aiep-auth"));
    }
  });
});
