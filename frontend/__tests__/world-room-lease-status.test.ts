import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

const source = readFileSync("features/world/WorldShell.tsx", "utf8");

describe("World room inventory access status", () => {
  it("reads access from tenant-scoped room inventory and access endpoints", () => {
    expect(source).toContain('"/world-commerce/room-inventory"');
    expect(source).toContain("/world-commerce/room-inventory/");
    expect(source).toContain("roomAccessQuery.data?.granted === true");
    expect(source).toContain("roomAccessQuery.data?.expires_at ?? null");
  });

  it("does not display access as granted when the latest query is unavailable", () => {
    expect(source).toContain("roomInventoryQuery.error || roomCatalogueQuery.error || roomAccessQuery.error");
    expect(source).toContain("unavailable={roomAccessUnavailable}");
    expect(source).toContain("granted={roomAccessGranted}");
    expect(source).toContain("وضعیت موجودی یا مجوز قابل بررسی نیست؛ دسترسی مسدود می‌ماند.");
  });

  it("schedules a re-check at server expiry and passes expiry to the scene", () => {
    expect(source).toContain("window.setTimeout(() => { void roomAccessQuery.refetch(); }, delay)");
    expect(source).toContain("expiresAt: roomAccessQuery.data?.expires_at ?? null");
    expect(source).toContain("roomAccess={roomSceneAccess}");
  });
});
