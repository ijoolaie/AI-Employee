"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth-store";
import { Spinner } from "@/components/ui/spinner";

export default function VendorLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const check = () => {
      const state = useAuthStore.getState();
      if (!state.isAuthenticated()) { router.replace("/login/vendor"); return; }
      if (state.user?.is_platform_admin) { router.replace("/admin"); return; }
      const kind = (state.tenant as (typeof state.tenant & { tenant_kind?: string }) | null)?.tenant_kind;
      if (kind !== "vendor") {
        router.replace(kind === "reseller" ? "/reseller/dashboard" : "/dashboard");
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
  return <div className="min-h-screen bg-slate-50">{children}</div>;
}
