import { test, expect } from "@playwright/test";

const authState = JSON.stringify({
  state: {
    accessToken: "e2e-access-token",
    refreshToken: "e2e-refresh-token",
    user: {
      id: "user-e2e",
      email: "e2e@example.test",
      full_name: "E2E Admin",
    },
    tenant: {
      id: "tenant-e2e",
      name: "E2E Tenant",
      tenant_kind: "reseller",
    },
  },
  version: 0,
});

test("support escalation remains visible after reload with mocked API", async ({ page }) => {
  const subject = "Support ticket persistence regression";
  const description = "Regression test for support ticket persistence.";
  let createdTicket: Record<string, unknown> | null = null;

  await page.addInitScript((state) => {
    localStorage.setItem("aiep-auth", state);
  }, authState);

  await page.route("**/api/proxy/auth/refresh", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        data: {
          access_token: "e2e-access-token",
          refresh_token: "e2e-refresh-token",
        },
      }),
    });
  });

  await page.route(
    "**/api/proxy/edition/reseller/support/escalations/sent",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          data: createdTicket ? [createdTicket] : [],
        }),
      });
    },
  );

  await page.route(
    "**/api/proxy/edition/reseller/support/escalations",
    async (route) => {
      if (route.request().method() === "POST") {
        const now = new Date().toISOString();
        createdTicket = {
          id: "e2e-support-ticket-001",
          from_tenant_id: "tenant-e2e",
          to_tenant_id: "platform-tenant",
          opened_by: "user-e2e",
          subject,
          description,
          status: "open",
          created_at: now,
          updated_at: now,
        };

        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            success: true,
            data: createdTicket,
          }),
        });
        return;
      }

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ success: true, data: [] }),
      });
    },
  );

  await page.route(
    "**/api/proxy/edition/reseller/support/escalations/*/messages",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ success: true, data: [] }),
      });
    },
  );

  await page.route("**/api/proxy/files", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ success: true, data: [] }),
    });
  });

  await page.goto("/reseller/support", { waitUntil: "domcontentloaded" });

  await page.locator("#reseller-support-subject").fill(subject);
  await page.locator("#reseller-support-description").fill(description);
  await page.getByRole("button", { name: "Create escalation" }).click();

  await expect(
    page.getByText(subject, { exact: true }).first(),
  ).toBeVisible();

  expect(createdTicket).not.toBeNull();

  await page.reload();

  await expect(
    page.getByText(subject, { exact: true }).first(),
  ).toBeVisible();
});
