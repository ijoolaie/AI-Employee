"use client";

import { ResellerSidebar } from "@/components/layout/reseller-sidebar";
import { useAuthStore } from "@/lib/auth-store";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Spinner } from "@/components/ui/spinner";

export default function ResellerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const check = () => {
      const state = useAuthStore.getState();

      if (!state.isAuthenticated()) {
        router.replace("/login");
        return;
      }

      if (state.user?.is_platform_admin) {
        router.replace("/admin");
        return;
      }

      const tenantKind = (
        state.tenant as
          | (typeof state.tenant & { tenant_kind?: string })
          | null
      )?.tenant_kind;

      if (tenantKind !== "reseller") {
        router.replace("/dashboard");
        return;
      }

      setReady(true);
    };

    const unsubscribe = useAuthStore.persist.onFinishHydration(check);

    if (useAuthStore.persist.hasHydrated()) {
      check();
    }

    return unsubscribe;
  }, [router]);

  if (!ready) {
    return <Spinner className="min-h-screen" />;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <ResellerSidebar />
      <main className="flex flex-1 flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto">{children}</div>
      </main>
    </div>
  );
}
