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

test.describe("critical platform flows", () => {
  test("authentication entry and password recovery routes", async ({ page }) => {
    await page.goto("/login");
    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
    await expect(page.getByRole("link", { name: /forgot your password/i })).toHaveAttribute("href", "/forgot-password");

    await page.goto("/forgot-password");
    await expect(page.getByRole("heading", { name: "Forgot your password?" })).toBeVisible();

    await page.goto("/reset-password?token=test-reset-token-123456789012345678901234567890");
    await expect(page.getByRole("heading", { name: "Set a new password" })).toBeVisible();
    await expect(page.getByRole("textbox", { name: "New password", exact: true })).toBeVisible();
    await expect(page.getByRole("textbox", { name: "Confirm new password", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Reset password" })).toBeEnabled();
  });

  test("customer workspace unauthenticated redirect", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login/);
  });

  test("admin route unauthenticated redirect", async ({ page }) => {
    await page.goto("/admin");
    await expect(page).toHaveURL(/\/login/);
  });

  test("marketplace installation surface requires authentication", async ({ page }) => {
    await page.goto("/marketplace");
    await expect(page).toHaveURL(/\/login/);
  });

  test("authorized marketplace flow reviews and installs a tenant-local copy", async ({ page }) => {
    await page.addInitScript((state) => localStorage.setItem("aiep-auth", state), authState);
    await page.route("**/marketplace/publications*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          data: [{
            id: "pub-e2e",
            owner_tenant_id: "publisher-tenant",
            team_version_id: "version-e2e",
            visibility: "public",
            status: "published",
            title: "Support Team",
            summary: "Handles customer support triage.",
            published_by: "publisher-user",
            published_at: "2026-09-03T12:00:00Z",
            withdrawn_at: null,
            customer_acceptance: "not_implied",
            production_deployment: "not_implied",
            trust_basis: "recorded_evidence_only",
          }],
        }),
      });
    });
    await page.route("**/marketplace/publications/pub-e2e/install", async (route) => {
      expect(route.request().method()).toBe("POST");
      expect(route.request().postDataJSON()).toEqual({ workspace_key: "ops" });
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          data: {
            id: "install-e2e",
            tenant_id: "tenant-e2e",
            team_version_id: "local-version-e2e",
            source_publication_id: "pub-e2e",
            workspace_key: "ops",
            enabled: true,
            installed_by: "user-e2e",
            installed_at: "2026-09-03T12:01:00Z",
          },
        }),
      });
    });

    await page.goto("/marketplace");
    await expect(page.getByRole("heading", { name: "Marketplace" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Support Team" })).toBeVisible();

    await page.getByLabel("Target workspace").fill("ops");
    await page.getByRole("button", { name: /Review & install/i }).click();
    await expect(page.getByRole("heading", { name: "Installation review" })).toBeVisible();
    await expect(page.getByText(/Installing creates tenant-local definitions and provenance/i)).toBeVisible();
    await expect(page.getByText("Customer acceptance", { exact: true }).locator("..")).toContainText("Not implied");
    await page.getByRole("button", { name: /Install tenant-local copy/i }).click();
    await expect(page.getByText(/Installation completed\./i)).toBeVisible();
    await expect(page.getByText(/Installation creates a tenant-local copy\./i)).toBeVisible();
  });

  test("marketplace install failure is surfaced without implying deployment", async ({ page }) => {
    await page.addInitScript((state) => localStorage.setItem("aiep-auth", state), authState);
    await page.route("**/marketplace/publications*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          data: [{
            id: "pub-denied",
            owner_tenant_id: "publisher-tenant",
            team_version_id: "version-denied",
            visibility: "public",
            status: "published",
            title: "Restricted Support Team",
            summary: "Requires explicit installation permission.",
            published_by: "publisher-user",
            published_at: "2026-09-03T12:00:00Z",
            withdrawn_at: null,
            customer_acceptance: "not_implied",
            production_deployment: "not_implied",
            trust_basis: "recorded_evidence_only",
          }],
        }),
      });
    });
    await page.route("**/marketplace/publications/pub-denied/install", async (route) => {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ success: false, error: "Permission denied" }),
      });
    });

    await page.goto("/marketplace");
    await page.getByLabel("Target workspace").fill("ops");
    await page.getByRole("button", { name: /Review & install/i }).click();
    await page.getByRole("button", { name: /Install tenant-local copy/i }).click();
    await expect(page.getByText(/Permission denied/i)).toBeVisible();
    await expect(page.getByText("Production deployment", { exact: true })).toBeVisible();
  });
  test("customer workspace switches between English and Persian RTL", async ({ page }) => {
    await page.addInitScript((state) => {
      localStorage.setItem("aiep-auth", state);
      localStorage.setItem("aiep.locale", "en");
    }, authState);
    await page.route("**/api/proxy/auth/refresh", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          data: { access_token: "e2e-access-token", refresh_token: "e2e-refresh-token" },
        }),
      });
    });

    await page.goto("/dashboard");
    await expect(page.locator("html")).toHaveAttribute("lang", "en");
    await expect(page.locator("html")).toHaveAttribute("dir", "ltr");
    await expect(page.getByRole("button", { name: "فا" })).toBeVisible();

    await page.getByRole("button", { name: "فا" }).click();
    await expect.poll(() => page.locator("html").getAttribute("lang")).toBe("fa");
    await expect.poll(() => page.locator("html").getAttribute("dir")).toBe("rtl");

    await page.getByRole("button", { name: "EN" }).click();
    await expect(page.locator("html")).toHaveAttribute("lang", "en");
    await expect(page.locator("html")).toHaveAttribute("dir", "ltr");
  });

  test("customer operational workspace routes retain locale and RTL shell", async ({ page }) => {
    await page.addInitScript((state) => {
      localStorage.setItem("aiep-auth", state);
    }, authState);

    await page.route("**/api/proxy/auth/refresh", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          data: { access_token: "e2e-access-token", refresh_token: "e2e-refresh-token" },
        }),
      });
    });

    const routes = [
      "/dashboard", "/office", "/customers", "/products", "/orders", "/sales",
      "/analytics", "/reports", "/employees", "/templates", "/knowledge",
      "/memory", "/inbox", "/conversations", "/channels", "/workflows",
      "/tasks", "/approvals", "/schedules", "/files", "/runs",
      "/traces", "/usage", "/integrations", "/billing", "/api-keys",
      "/webhooks", "/settings", "/settings/security",
    ];

    await page.goto("/dashboard", { waitUntil: "domcontentloaded" });
    for (const locale of ["en", "fa"] as const) {
      await page.evaluate((value) => localStorage.setItem("aiep.locale", value), locale);
      await page.reload({ waitUntil: "domcontentloaded" });
      for (const route of routes) {
        await page.goto(route, { waitUntil: "commit" });
        await expect(page).toHaveURL(new RegExp(route.replace("/", "\\/")));
        await expect(page.locator("html")).toHaveAttribute("lang", locale);
        await expect(page.locator("html")).toHaveAttribute("dir", locale === "fa" ? "rtl" : "ltr");
      }
    }
  });


  test("customer tenant cannot enter reseller-only support workspace", async ({ page }) => {
    const customerState = JSON.stringify({
      state: {
        accessToken: "e2e-access-token",
        refreshToken: "e2e-refresh-token",
        user: { id: "customer-user-e2e", email: "customer@example.test", full_name: "E2E Customer" },
        tenant: { id: "customer-tenant-e2e", name: "E2E Customer", tenant_kind: "customer" },
      },
      version: 0,
    });
    await page.addInitScript((state) => localStorage.setItem("aiep-auth", state), customerState);
    await page.route("**/api/proxy/auth/refresh", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          data: { access_token: "e2e-access-token", refresh_token: "e2e-refresh-token" },
        }),
      });
    });

    await page.goto("/reseller/support", { waitUntil: "domcontentloaded" });
    await expect(page).toHaveURL(/\\/dashboard$/);
    await expect(page.getByRole("heading", { name: "Support" })).toBeVisible();
  });

  test("reseller tenant cannot enter customer support ticket workspace", async ({ page }) => {
    const resellerState = JSON.stringify({
      state: {
        accessToken: "e2e-access-token",
        refreshToken: "e2e-refresh-token",
        user: { id: "reseller-user-e2e", email: "reseller@example.test", full_name: "E2E Reseller" },
        tenant: { id: "reseller-tenant-e2e", name: "E2E Reseller", tenant_kind: "reseller" },
      },
      version: 0,
    });
    await page.addInitScript((state) => localStorage.setItem("aiep-auth", state), resellerState);
    await page.route("**/api/proxy/auth/refresh", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          data: { access_token: "e2e-access-token", refresh_token: "e2e-refresh-token" },
        }),
      });
    });

    await page.goto("/support", { waitUntil: "domcontentloaded" });
    await expect(page).toHaveURL(/\\/reseller\\/dashboard$/);
    await expect(page.getByRole("heading", { name: /Overview|Dashboard/i })).toBeVisible();
  });

  test("customer support ticket survives reload and supports a persisted reply", async ({ page }) => {
    await page.addInitScript((state) => {
      localStorage.setItem("aiep-auth", state);
      localStorage.setItem("aiep.locale", "en");
    }, JSON.stringify({
      state: {
        accessToken: "e2e-access-token",
        refreshToken: "e2e-refresh-token",
        user: { id: "user-e2e", email: "e2e@example.test", full_name: "E2E Customer" },
        tenant: { id: "tenant-customer-e2e", name: "E2E Customer", tenant_kind: "customer" },
      },
      version: 0,
    }));

    await page.route("**/api/proxy/auth/refresh", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          data: { access_token: "e2e-access-token", refresh_token: "e2e-refresh-token" },
        }),
      });
    });

    const ticketId = "support-ticket-e2e";
    const tickets: Array<Record<string, unknown>> = [];
    const messages: Array<Record<string, unknown>> = [];

    await page.route("**/edition/support/escalations**", async (route) => {
      const request = route.request();
      const url = new URL(request.url());
      if (url.pathname.endsWith("/messages") && request.method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ success: true, data: messages }),
        });
        return;
      }
      if (url.pathname.endsWith("/messages") && request.method() === "POST") {
        const payload = request.postDataJSON() as { body: string };
        const message = {
          id: `support-message-${messages.length + 1}`,
          escalation_id: ticketId,
          author_tenant_id: "tenant-customer-e2e",
          author_user_id: "user-e2e",
          body: payload.body,
          created_at: "2026-10-17T12:00:00Z",
          attachments: [],
        };
        messages.push(message);
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({ success: true, data: message }),
        });
        return;
      }
      if (!url.pathname.endsWith("/messages") && request.method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ success: true, data: tickets }),
        });
        return;
      }
      if (!url.pathname.endsWith("/messages") && request.method() === "POST") {
        const payload = request.postDataJSON() as { subject: string; description: string };
        const ticket = {
          id: ticketId,
          from_tenant_id: "tenant-customer-e2e",
          to_tenant_id: "provider-tenant-e2e",
          status: "open",
          subject: payload.subject,
          description: payload.description,
        };
        tickets.push(ticket);
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({ success: true, data: ticket }),
        });
        return;
      }
      await route.continue();
    });

    await page.goto("/support");
    await expect(page.getByRole("heading", { name: "Support" })).toBeVisible();
    await page.getByLabel("Subject").fill("Order status question");
    await page.getByLabel("Description").fill("Please help me check my order status.");
    await page.getByRole("button", { name: "Create ticket" }).click();
    await expect(page.getByText("Support ticket created.")).toBeVisible();
    await expect(page.getByRole("button", { name: /Order status question/ })).toBeVisible();

    await page.reload();
    await expect(page.getByRole("button", { name: /Order status question/ })).toBeVisible();
    await page.getByLabel("Reply").fill("Could you please provide an update?");
    await page.getByRole("button", { name: "Send reply" }).click();
    await expect(page.getByText("Reply sent.")).toBeVisible();
    await expect(page.getByText("Could you please provide an update?")).toBeVisible();

    await page.reload();
    await expect(page.getByRole("button", { name: /Order status question/ })).toBeVisible();
    await expect(page.getByText("Could you please provide an update?")).toBeVisible();
  });

});
