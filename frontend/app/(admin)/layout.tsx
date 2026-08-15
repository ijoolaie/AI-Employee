"use client";

import { useAuthStore } from "@/lib/auth-store";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Spinner } from "@/components/ui/spinner";
import { AdminSidebar } from "@/components/layout/admin-sidebar";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const unsub = useAuthStore.persist.onFinishHydration(() => {
      if (!isAuthenticated()) router.replace("/login");
      else if (!useAuthStore.getState().user?.is_platform_admin) router.replace("/dashboard");
      else setReady(true);
    });
    if (useAuthStore.persist.hasHydrated()) {
      if (!isAuthenticated()) router.replace("/login");
      else if (!user?.is_platform_admin) router.replace("/dashboard");
      else setReady(true);
    }
    return unsub;
  }, [isAuthenticated, router, user]);

  if (!ready) return <Spinner className="min-h-screen" />;

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <AdminSidebar />
      <main className="flex flex-1 flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto">{children}</div>
      </main>
    </div>
  );
}
