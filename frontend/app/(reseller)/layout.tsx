"use client";

import { ResellerSidebar } from "@/components/layout/reseller-sidebar";
import { PortalContextSwitcher } from "@/components/layout/portal-context-switcher";
import { useAuthStore } from "@/lib/auth-store";
import { usePathname, useRouter } from "next/navigation";
import { useI18n } from "@/lib/i18n/provider";
import { resellerMessages } from "@/lib/i18n/reseller";
import { useEffect, useState } from "react";
import { Spinner } from "@/components/ui/spinner";

export default function ResellerLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { locale } = useI18n();
  const m = resellerMessages[locale];
  const mobileLinks = [
    ["/reseller/dashboard", m.overview],
    ["/reseller/clients", m.clients],
    ["/reseller/team", m.humanEmployees],
    ["/reseller/ai-employees", m.aiEmployees],
    ["/reseller/test-center", m.testCenter],
    ["/reseller/support", m.clientSupport],
    ["/reseller/workflows", m.workflows],
    ["/reseller/usage", m.usageCost],
    ["/reseller/integrations", m.integrations],
    ["/reseller/billing", m.billing],
    ["/reseller/reports", m.reports],
    ["/reseller/settings", m.settings],
    ["/reseller/security", m.security],
  ] as const;
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const check = () => {
      const state = useAuthStore.getState();
      if (!state.isAuthenticated()) { router.replace("/login/reseller"); return; }
      if (state.user?.is_platform_admin) { router.replace("/admin"); return; }
      const tenantKind = (state.tenant as (typeof state.tenant & { tenant_kind?: string }) | null)?.tenant_kind;
      if (tenantKind !== "reseller") {
        router.replace(tenantKind === "vendor" ? "/vendor/dashboard" : "/dashboard");
        return;
      }
      setReady(true);
    };
    let active = true;
    const runCheck = () => { if (active) check(); };
    const unsubscribe = useAuthStore.persist.onFinishHydration(runCheck);
    if (useAuthStore.persist.hasHydrated()) runCheck();
    else void Promise.resolve(useAuthStore.persist.rehydrate()).then(runCheck);
    return () => { active = false; unsubscribe(); };
  }, [router]);

  if (!ready) return <Spinner className="min-h-screen" />;
  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <ResellerSidebar />
      <main className="flex flex-1 flex-col overflow-hidden">
        <div className="flex items-center justify-between gap-3 border-b border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 sm:px-5">
          <span className="shrink-0"><span className="hidden sm:inline">Current portal: </span>Reseller</span>
          <div className="flex min-w-0 items-center gap-2">
            <select
              aria-label="Reseller navigation"
              value={mobileLinks.find(([href]) => pathname === href || pathname.startsWith(href + "/"))?.[0] ?? "/reseller/dashboard"}
              onChange={(event) => router.push(event.target.value)}
              className="h-9 max-w-[42vw] rounded-lg border border-slate-200 bg-white px-2 text-xs md:hidden"
            >
              {mobileLinks.map(([href, label]) => <option key={href} value={href}>{label}</option>)}
            </select>
            <PortalContextSwitcher />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">{children}</div>
      </main>
    </div>
  );
}
