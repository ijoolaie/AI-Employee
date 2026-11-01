"use client";

import { Sidebar } from "@/components/layout/sidebar";
import { ModeSwitch } from "@/components/layout/mode-switch";
import { useAuthStore } from "@/lib/auth-store";
import { useRouter, usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Spinner } from "@/components/ui/spinner";

export default function CustomerLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const isWorld = pathname === "/world" || pathname.startsWith("/world/");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let active = true;
    const check = () => {
      // Read the hydrated snapshot, not render-time selector values captured
      // before persist.rehydrate() resolves.
      const { accessToken, user, tenant } = useAuthStore.getState();
      if (!accessToken) { router.replace("/login/customer"); return; }
      if (user?.is_platform_admin) { router.replace("/admin"); return; }
      const tenantKind = (tenant as (typeof tenant & { tenant_kind?: string }) | null)?.tenant_kind;
      if (tenantKind !== "customer") {
        router.replace(tenantKind === "vendor" ? "/vendor/dashboard" : tenantKind === "reseller" ? "/reseller/dashboard" : "/login/customer");
        return;
      }
      setReady(true);
    };
    const runCheck = () => { if (active) check(); };
    const unsub = useAuthStore.persist.onFinishHydration(runCheck);
    if (useAuthStore.persist.hasHydrated()) runCheck();
    else void Promise.resolve(useAuthStore.persist.rehydrate()).then(runCheck);
    return () => { active = false; unsub(); };
  }, [router]);

  if (!ready) return <Spinner className="min-h-screen" />;
  if (isWorld) return <div className="min-h-screen">{children}</div>;

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />
      <main className="flex flex-1 flex-col overflow-hidden">
        <div className="border-b border-gray-200 bg-white px-4 py-2 md:px-6"><ModeSwitch /></div>
        <div className="flex-1 overflow-y-auto">{children}</div>
      </main>
    </div>
  );
}
