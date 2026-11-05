"use client";

import { Sidebar } from "@/components/layout/sidebar";
import { ModeSwitch } from "@/components/layout/mode-switch";
import { VendorSidebar } from "@/components/layout/vendor-sidebar";
import { useAuthStore } from "@/lib/auth-store";
import { useRouter, usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Spinner } from "@/components/ui/spinner";

export default function CustomerLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const isWorld = pathname === "/world" || pathname.startsWith("/world/");
  const tenant = useAuthStore((state) => state.tenant);
  const tenantKind = (tenant as (typeof tenant & { tenant_kind?: string }) | null)?.tenant_kind;
  const isVendorManagementRoute = tenantKind === "vendor" && pathname.startsWith("/vendor/");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let active = true;
    const check = () => {
      const { accessToken, user, tenant: currentTenant } = useAuthStore.getState();
      if (!accessToken) { router.replace("/login/customer"); return; }
      if (user?.is_platform_admin) { router.replace("/admin"); return; }
      const kind = (currentTenant as (typeof currentTenant & { tenant_kind?: string }) | null)?.tenant_kind;
      if (pathname.startsWith("/vendor/") && kind !== "vendor") {
        router.replace(kind === "reseller" ? "/reseller/dashboard" : kind === "platform-admin" ? "/admin" : "/dashboard");
        return;
      }
      const vendorManagementRoute = kind === "vendor" && pathname.startsWith("/vendor/");
      if (kind !== "customer" && !vendorManagementRoute) {
        router.replace(kind === "vendor" ? "/vendor/dashboard" : kind === "reseller" ? "/reseller/dashboard" : "/login/customer");
        return;
      }
      setReady(true);
    };
    const runCheck = () => { if (active) check(); };
    const unsub = useAuthStore.persist.onFinishHydration(runCheck);
    if (useAuthStore.persist.hasHydrated()) runCheck();
    else void Promise.resolve(useAuthStore.persist.rehydrate()).then(runCheck);
    return () => { active = false; unsub(); };
  }, [router, pathname]);

  if (!ready) return <Spinner className="min-h-screen" />;
  if (isWorld) return <div className="min-h-screen">{children}</div>;

  if (isVendorManagementRoute) {
    return <div className="flex h-screen overflow-hidden bg-slate-50"><VendorSidebar /><main className="flex flex-1 flex-col overflow-hidden"><div className="border-b border-slate-200 bg-white px-5 py-2 text-sm font-semibold text-slate-700">Vendor portal</div><div className="flex-1 overflow-y-auto">{children}</div></main></div>;
  }

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
