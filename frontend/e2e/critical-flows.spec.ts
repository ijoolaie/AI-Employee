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
    await expect(page.getByText(/Installation does not imply customer acceptance/i)).toBeVisible();

    await page.getByLabel("Target workspace").fill("ops");
    await page.getByRole("button", { name: /Review & install/i }).click();
    await expect(page.getByRole("heading", { name: "Installation review" })).toBeVisible();
    await expect(page.getByText("Customer acceptance").locator("..")).toContainText("Not implied");
    await page.getByRole("button", { name: /Install tenant-local copy/i }).click();
    await expect(page.getByText(/Installed install-e2e locally/i)).toBeVisible();
    await expect(page.getByText(/No AI Employee instance was provisioned/i)).toBeVisible();
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
    await expect(page.getByText(/production deployment/i)).toBeVisible();
  });
});
