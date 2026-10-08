import { defineConfig } from "@playwright/test";

const chromiumExecutable = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE;

export default defineConfig({
  testDir: "./e2e",
  use: {
    baseURL: process.env.BASE_URL ?? "http://127.0.0.1:3000",
    ...(chromiumExecutable
      ? {
          launchOptions: {
            executablePath: chromiumExecutable,
          },
        }
      : {}),
  },
  reporter: "html",
});
