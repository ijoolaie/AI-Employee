"use client";

import { useAuthStore } from "@/lib/auth-store";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Spinner } from "@/components/ui/spinner";

export default function HomePage() {
  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);
  const tenant = useAuthStore((s) => s.tenant);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }

    if (user?.is_platform_admin) {
      router.replace("/admin");
      return;
    }

    const tenantKind = (tenant as (typeof tenant & { tenant_kind?: string }) | null)?.tenant_kind;
    router.replace(tenantKind === "reseller" ? "/reseller/dashboard" : "/dashboard");
  }, [isAuthenticated, router, tenant, user]);

  return <Spinner className="min-h-screen" />;
}
