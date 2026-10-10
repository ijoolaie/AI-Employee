import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

const source = readFileSync("features/world/WorldShell.tsx", "utf8");

describe("World room lease status", () => {
  it("reads active entitlements from the tenant-scoped server endpoint", () => {
    expect(source).toContain('"/world-commerce/entitlements"');
    expect(source).toContain('entitlement.item_type === "room"');
    expect(source).toContain('entitlement.status === "active"');
  });

  it("shows server expiry and explicitly distinguishes entitlement from scene integration", () => {
    expect(source).toContain("lease.expires_at");
    expect(source).toContain("اتصال این اعتبار به بازشدن صحنهٔ سه‌بعدی هنوز تکمیل نشده است");
  });

  it("fails closed in the UI when entitlement status cannot be loaded", () => {
    expect(source).toContain("وضعیت اعتبار قابل بررسی نیست؛ دسترسی فعال فرض نمی‌شود.");
    expect(source).toContain("وضعیت از فهرست اعتبارهای معتبر سرور خوانده شده است.");
  });
});
