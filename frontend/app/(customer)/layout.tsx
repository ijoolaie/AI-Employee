"use client";

import { Sidebar } from "@/components/layout/sidebar";
import { useAuthStore } from "@/lib/auth-store";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Spinner } from "@/components/ui/spinner";

export default function CustomerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // Wait for zustand persist rehydration
    const unsub = useAuthStore.persist.onFinishHydration(() => {
      if (!isAuthenticated()) {
        router.replace("/login");
      } else {
        setReady(true);
      }
    });
    // If already hydrated
    if (useAuthStore.persist.hasHydrated()) {
      if (!isAuthenticated()) {
        router.replace("/login");
      } else {
        setReady(true);
      }
    }
    return unsub;
  }, [isAuthenticated, router]);

  if (!ready) {
    return <Spinner className="min-h-screen" />;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />
      <main className="flex flex-1 flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto">{children}</div>
      </main>
    </div>
  );
}
