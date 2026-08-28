import { expect, test } from "@playwright/test";

test("workspace exposes unified execution state", async ({ page }) => {
  await page.goto("/workspace");
  await expect(page.getByText("Execution Workspace")).toBeVisible();
  await expect(page.getByText("Unified WorkItem")).toBeVisible();
  await expect(page.getByText("Tenant scoped")).toBeVisible();
  await expect(page.getByText("Correlated")).toBeVisible();
});
