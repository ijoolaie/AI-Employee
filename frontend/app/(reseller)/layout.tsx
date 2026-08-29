"use client";

import { ResellerSidebar } from "@/components/layout/reseller-sidebar";
import { useAuthStore } from "@/lib/auth-store";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Spinner } from "@/components/ui/spinner";

export default function ResellerLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);
  const tenant = useAuthStore((s) => s.tenant);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const check = () => {
      if (!isAuthenticated()) { router.replace("/login"); return; }
      if (user?.is_platform_admin) { router.replace("/admin"); return; }
      const tenantKind = (tenant as (typeof tenant & { tenant_kind?: string }) | null)?.tenant_kind;
      if (tenantKind !== "reseller") { router.replace("/dashboard"); return; }
      setReady(true);
    };
    const unsub = useAuthStore.persist.onFinishHydration(check);
    if (useAuthStore.persist.hasHydrated()) check();
    return unsub;
  }, [isAuthenticated, router, tenant, user]);

  if (!ready) return <Spinner className="min-h-screen" />;

  return <div className="flex h-screen overflow-hidden bg-slate-50"><ResellerSidebar /><main className="flex flex-1 flex-col overflow-hidden"><div className="flex-1 overflow-y-auto">{children}</div></main></div>;
}
