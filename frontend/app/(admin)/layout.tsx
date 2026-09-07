"use client";

import { useAuthStore } from "@/lib/auth-store";
import { useRouter } from "next/navigation";
import { useEffect, useSyncExternalStore } from "react";
import { Spinner } from "@/components/ui/spinner";
import { AdminSidebar } from "@/components/layout/admin-sidebar";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const hydrated = useSyncExternalStore(
    (onChange) => useAuthStore.persist.onFinishHydration(() => onChange()),
    () => useAuthStore.persist.hasHydrated(),
    () => false,
  );

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated()) router.replace("/login");
    else if (!user?.is_platform_admin) router.replace("/dashboard");
  }, [hydrated, isAuthenticated, router, user]);

  if (!hydrated || !isAuthenticated() || !user?.is_platform_admin) return <Spinner className="min-h-screen" />;

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <AdminSidebar />
      <main className="flex flex-1 flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto">{children}</div>
      </main>
    </div>
  );
}
