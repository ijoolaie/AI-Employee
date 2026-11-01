"use client";

import { useAuthStore } from "@/lib/auth-store";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Spinner } from "@/components/ui/spinner";
import { defaultPortalForAccount, portalPath } from "@/lib/portal-access";

export default function HomePage() {
  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);
  const tenant = useAuthStore((s) => s.tenant);

  useEffect(() => {
    if (!isAuthenticated()) { router.replace("/login"); return; }
    const tenantKind = (tenant as (typeof tenant & { tenant_kind?: string }) | null)?.tenant_kind;
    const portal = defaultPortalForAccount(user?.is_platform_admin ? "platform-admin" : tenantKind ?? "customer");
    router.replace(portal === "admin" ? "/admin" : portalPath(portal));
  }, [isAuthenticated, router, tenant, user]);

  return <Spinner className="min-h-screen" />;
}
