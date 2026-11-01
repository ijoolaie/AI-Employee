"use client";

import { useAuthStore } from "@/lib/auth-store";

export default function VendorDashboardPage() {
  const tenant = useAuthStore((state) => state.tenant);
  return (
    <main className="mx-auto max-w-5xl p-6 md:p-10">
      <header className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-brand-700">AI Employee · Vendor</p>
        <h1 className="mt-2 text-3xl font-bold text-slate-900">Vendor portal</h1>
        <p className="mt-2 text-slate-600">Signed in to {tenant?.name ?? "your vendor workspace"}.</p>
        <p className="mt-4 text-sm text-slate-500">This is a separate vendor entry point, not the platform-admin console. Vendor operations remain scoped to the authenticated vendor tenant.</p>
      </header>
    </main>
  );
}
