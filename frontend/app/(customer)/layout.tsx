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
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);
  const tenant = useAuthStore((s) => s.tenant);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const check = () => {
      if (!isAuthenticated()) {
        router.replace("/login");
        return;
      }
      if (user?.is_platform_admin) {
        router.replace("/admin");
        return;
      }
      const tenantKind = (tenant as (typeof tenant & { tenant_kind?: string }) | null)?.tenant_kind;
      if (tenantKind === "reseller") {
        router.replace("/reseller/dashboard");
        return;
      }
      setReady(true);
    };

    const unsub = useAuthStore.persist.onFinishHydration(check);
    if (useAuthStore.persist.hasHydrated()) check();
    return unsub;
  }, [isAuthenticated, router, tenant, user]);

  if (!ready) return <Spinner className="min-h-screen" />;

  if (isWorld) {
    return <div className="min-h-screen">{children}</div>;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />
      <main className="flex flex-1 flex-col overflow-hidden">
        <div className="border-b border-gray-200 bg-white px-4 py-2 md:px-6">
          <ModeSwitch />
        </div>
        <div className="flex-1 overflow-y-auto">{children}</div>
      </main>
    </div>
  );
}
