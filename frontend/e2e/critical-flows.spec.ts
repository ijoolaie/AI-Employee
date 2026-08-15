import { test, expect } from "@playwright/test";

test.describe("critical platform flows", () => {
  test("authentication entry and password recovery routes", async ({ page }) => {
    await page.goto("/login");
    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
    await expect(page.getByRole("link", { name: /forgot your password/i })).toHaveAttribute("href", "/forgot-password");

    await page.goto("/forgot-password");
    await expect(page.getByRole("heading", { name: "Forgot your password?" })).toBeVisible();

    await page.goto("/reset-password");
    await expect(page.getByRole("heading", { name: "Set a new password" })).toBeVisible();
  });

  test("customer workspace unauthenticated redirect", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login/);
  });

  test("admin route unauthenticated redirect", async ({ page }) => {
    await page.goto("/admin");
    await expect(page).toHaveURL(/\/login/);
  });
});
