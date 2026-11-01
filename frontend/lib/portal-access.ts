export type PortalKind = "customer" | "reseller" | "vendor";
export type AccountKind = "customer" | "reseller" | "vendor" | "platform-admin" | string;

/** UI destination policy only. Backend permissions and tenant scoping remain authoritative. */
export function canEnterPortal(accountKind: AccountKind, portal: PortalKind): boolean {
  if (accountKind === "platform-admin") return false;
  return accountKind === portal;
}

export function defaultPortalForAccount(accountKind: AccountKind): PortalKind | "admin" {
  if (accountKind === "platform-admin") return "admin";
  if (accountKind === "vendor") return "vendor";
  if (accountKind === "reseller") return "reseller";
  return "customer";
}

export function portalPath(portal: PortalKind): string {
  switch (portal) {
    case "vendor": return "/vendor/dashboard";
    case "reseller": return "/reseller/dashboard";
    default: return "/dashboard";
  }
}
