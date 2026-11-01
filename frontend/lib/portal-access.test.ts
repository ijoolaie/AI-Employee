import { describe, expect, it } from "vitest";
import { canEnterPortal, defaultPortalForAccount, portalPath } from "./portal-access";

describe("commercial portal access matrix (aligned with backend edition guards)", () => {
  it.each([
    ["vendor", "customer", false],
    ["vendor", "reseller", false],
    ["vendor", "vendor", true],
    ["reseller", "customer", false],
    ["reseller", "reseller", true],
    ["reseller", "vendor", false],
    ["customer", "customer", true],
    ["customer", "reseller", false],
    ["customer", "vendor", false],
    ["platform-admin", "customer", false],
    ["platform-admin", "reseller", false],
    ["platform-admin", "vendor", false],
  ] as const)("account %s portal %s => %s", (account, portal, allowed) => {
    expect(canEnterPortal(account, portal)).toBe(allowed);
  });

  it("routes account kinds to their default portals without elevating platform admins", () => {
    expect(defaultPortalForAccount("vendor")).toBe("vendor");
    expect(defaultPortalForAccount("reseller")).toBe("reseller");
    expect(defaultPortalForAccount("customer")).toBe("customer");
    expect(defaultPortalForAccount("platform-admin")).toBe("admin");
    expect(portalPath("vendor")).toBe("/vendor/dashboard");
    expect(portalPath("reseller")).toBe("/reseller/dashboard");
    expect(portalPath("customer")).toBe("/dashboard");
  });
});
