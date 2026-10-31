import { expect, test } from "@playwright/test";

test("public widget uses the real API, Celery worker, and persisted assistant transcript", async ({ page }) => {
  const publicKey = process.env.PUBLIC_CHAT_KEY;
  expect(publicKey, "the CI fixture must provision a public channel").toBeTruthy();

  const channelLookup = page.waitForResponse((response) =>
    response.url().includes(`/api/proxy/public/chat/channels/${publicKey}`) &&
    response.request().method() === "GET"
  );
  await page.goto(`/chat/${publicKey}`);
  expect((await channelLookup).status()).toBe(200);
  await expect(page.locator("section header h1")).toHaveText("CI Public Support Employee");

  await page.locator('input[type="email"]').fill(`browser-acceptance-${Date.now()}@example.com`);
  await page.getByRole("button").first().click();
  const storageKey = `aiep-chat-${publicKey}`;
  await expect.poll(() => page.evaluate((key) => window.localStorage.getItem(key), storageKey)).not.toBeNull();
  const stored = await page.evaluate((key) => {
    const value = window.localStorage.getItem(key);
    return value ? JSON.parse(value) as { id: string; token: string } : null;
  }, storageKey);
  expect(stored?.id).toBeTruthy();
  expect(stored?.token).toBeTruthy();

  const customerMessage = `browser-worker-acceptance-${Date.now()}`;
  await page.locator("form textarea").fill(customerMessage);
  const sendRequest = page.waitForResponse((response) =>
    response.url().includes(`/api/proxy/public/chat/conversations/${stored!.id}/messages`) &&
    response.request().method() === "POST"
  );
  await page.locator("form").filter({ has: page.locator("textarea") }).locator("button").click();
  const sendResponse = await sendRequest;
  const envelope = await sendResponse.json();
  expect(sendResponse.status(), JSON.stringify(envelope)).toBe(200);
  expect(envelope.success).toBe(true);
  expect(envelope.data.conversation_id).toBe(stored!.id);
  expect(envelope.data.run_id).toMatch(/^[0-9a-f-]{36}$/i);
  expect(envelope.data.status).toBeTruthy();

  // The browser must render both the customer turn and the assistant turn
  // returned by the token-protected transcript after the real Celery worker runs.
  await expect(page.getByText(customerMessage, { exact: true })).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText(/^Deterministic certification result:/)).toBeVisible({ timeout: 30_000 });

  const wrongTokenStatus = await page.evaluate(async (conversationId) => {
    const response = await fetch(`/api/proxy/public/chat/conversations/${conversationId}`, {
      headers: { "X-Customer-Token": "not-the-owner-token" },
    });
    return response.status;
  }, stored.id);
  expect(wrongTokenStatus).toBe(404);
});
