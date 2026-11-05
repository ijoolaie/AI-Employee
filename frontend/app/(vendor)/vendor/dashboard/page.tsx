"use client";

import { useAuthStore } from "@/lib/auth-store";
import { Header } from "@/components/layout/header";
import Link from "next/link";
import { Building2, ShieldCheck, Users } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export default function VendorDashboardPage() {
  const tenant = useAuthStore((state) => state.tenant);
  return <>
    <Header title="Vendor portal" description={"Manage the direct reseller and Customer network for " + (tenant?.name ?? "your Vendor workspace") + "."} />
    <main className="mx-auto grid max-w-5xl gap-6 p-6 md:grid-cols-3 md:p-10">
      <Link href="/vendor/resellers"><Card className="h-full transition hover:shadow-md"><CardContent className="p-6"><Building2 className="h-7 w-7 text-brand-700" /><h2 className="mt-4 font-semibold text-slate-900">Resellers</h2><p className="mt-2 text-sm text-slate-600">Create and manage Resellers directly owned by this Vendor.</p></CardContent></Card></Link>
      <Link href="/vendor/customers"><Card className="h-full transition hover:shadow-md"><CardContent className="p-6"><Users className="h-7 w-7 text-brand-700" /><h2 className="mt-4 font-semibold text-slate-900">Direct Customers</h2><p className="mt-2 text-sm text-slate-600">Manage Customer tenants provisioned directly under this Vendor.</p></CardContent></Card></Link>
      <Link href="/vendor/licenses"><Card className="h-full transition hover:shadow-md"><CardContent className="p-6"><ShieldCheck className="h-7 w-7 text-brand-700" /><h2 className="mt-4 font-semibold text-slate-900">Commercial licenses</h2><p className="mt-2 text-sm text-slate-600">Issue commercial licenses to tenants in this Vendor hierarchy.</p></CardContent></Card></Link>
    </main>
  </>;
}
