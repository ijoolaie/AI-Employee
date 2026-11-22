"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  Activity, ArrowUpRight, Building2, CircleAlert, ClipboardList, RefreshCw,
  ShieldCheck, Users, WalletCards,
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, getErrorMessage } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";

interface TenantSummary {
  id: string;
  name: string;
  slug: string;
  status: string;
  tenant_kind: string;
}
interface SupportEscalationSummary {
  id: string;
  subject?: string;
  status: string;
  created_at?: string;
  updated_at?: string;
}
interface ApiList<T> { success: boolean; data: T[] }

async function getList<T>(path: string): Promise<T[]> {
  const response = await api.get<ApiList<T>>(path);
  if (!response.data.success) throw new Error("The requested data could not be loaded");
  return response.data.data;
}

function countStatus(items: TenantSummary[], status: string) {
  return items.filter((item) => item.status.toLowerCase() === status).length;
}

export default function VendorDashboardPage() {
  const tenant = useAuthStore((state) => state.tenant);
  const resellers = useQuery({ queryKey: ["vendor-resellers"], queryFn: () => getList<TenantSummary>("/edition/vendor/resellers") });
  const customers = useQuery({ queryKey: ["vendor-customers"], queryFn: () => getList<TenantSummary>("/edition/vendor/customers") });
  const licenseTargets = useQuery({ queryKey: ["vendor-license-targets"], queryFn: () => getList<TenantSummary>("/edition/vendor/tenants") });
  const escalations = useQuery({ queryKey: ["vendor-support-escalations"], queryFn: () => getList<SupportEscalationSummary>("/edition/vendor/support/escalations") });
  const loading = resellers.isLoading || customers.isLoading || licenseTargets.isLoading || escalations.isLoading;
  const hasError = resellers.isError || customers.isError || licenseTargets.isError || escalations.isError;
  const resellerRows = resellers.data ?? [];
  const customerRows = customers.data ?? [];
  const targets = licenseTargets.data ?? [];
  const tickets = escalations.data ?? [];
  const activeResellers = countStatus(resellerRows, "active");
  const activeCustomers = countStatus(customerRows, "active");
  const openTickets = tickets.filter((ticket) => !["resolved", "closed"].includes(ticket.status.toLowerCase()));
  const refresh = () => {
    void resellers.refetch(); void customers.refetch(); void licenseTargets.refetch(); void escalations.refetch();
  };

  const metrics = [
    { label: "Resellers", value: resellers.isError ? "N/A" : resellerRows.length, detail: `${activeResellers} active`, icon: Building2, href: "/vendor/resellers" },
    { label: "Direct customers", value: customers.isError ? "N/A" : customerRows.length, detail: `${activeCustomers} active`, icon: Users, href: "/vendor/customers" },
    { label: "License targets", value: licenseTargets.isError ? "N/A" : targets.length, detail: "In your vendor hierarchy", icon: ShieldCheck, href: "/vendor/licenses" },
    { label: "Open support escalations", value: escalations.isError ? "N/A" : openTickets.length, detail: `${tickets.length} total escalations`, icon: CircleAlert, href: "/vendor/support" },
  ];

  return <>
    <Header
      title={"Vendor management dashboard"}
      description={`Network and operations overview for ${tenant?.name ?? "your Vendor workspace"}.`}
    />
    <main className="mx-auto max-w-7xl space-y-6 p-5 md:p-8">
      <section className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">{"Network overview"}</h2>
          <p className="mt-1 text-sm text-slate-500">{"Reseller, customer, licensing and support status at a glance."}</p>
        </div>
        <button onClick={refresh} disabled={loading} className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />{"Refresh data"}
        </button>
      </section>

      {hasError && <div role="alert" className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        {"Some dashboard data could not be loaded. Other sections remain available."}
        <div className="mt-2 text-xs text-amber-800">{[resellers, customers, licenseTargets, escalations].filter((query) => query.isError).map((query) => getErrorMessage(query.error)).join(" | ")}</div>
      </div>}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => <Link key={metric.label} href={metric.href} className="group">
          <Card className="h-full transition hover:-translate-y-0.5 hover:shadow-md">
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <span className="rounded-xl bg-brand-50 p-3 text-brand-700"><metric.icon className="h-5 w-5" /></span>
                <ArrowUpRight className="h-4 w-4 text-slate-300 transition group-hover:text-brand-700" />
              </div>
              <p className="mt-4 text-sm font-medium text-slate-500">{metric.label}</p>
              <p className="mt-1 text-3xl font-semibold tracking-tight text-slate-900">{loading && metric.value !== "—" ? "..." : metric.value}</p>
              <p className="mt-1 text-xs text-slate-500">{metric.detail}</p>
            </CardContent>
          </Card>
        </Link>)}
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.35fr_1fr]">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <CardTitle>{"Quick operations"}</CardTitle>
            <Activity className="h-5 w-5 text-slate-400" />
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            <Link href="/vendor/resellers" className="flex items-center gap-3 rounded-xl border border-slate-200 p-4 transition hover:border-brand-300 hover:bg-brand-50/40">
              <Building2 className="h-5 w-5 text-brand-700" /><span className="min-w-0 flex-1"><span className="block text-sm font-semibold text-slate-900">{"Manage resellers"}</span><span className="mt-1 block text-xs text-slate-500">{"Create, suspend and resume"}</span></span><ArrowUpRight className="h-4 w-4 text-slate-400" />
            </Link>
            <Link href="/vendor/customers" className="flex items-center gap-3 rounded-xl border border-slate-200 p-4 transition hover:border-brand-300 hover:bg-brand-50/40">
              <Users className="h-5 w-5 text-brand-700" /><span className="min-w-0 flex-1"><span className="block text-sm font-semibold text-slate-900">{"Manage customers"}</span><span className="mt-1 block text-xs text-slate-500">{"Direct Vendor customers"}</span></span><ArrowUpRight className="h-4 w-4 text-slate-400" />
            </Link>
            <Link href="/vendor/licenses" className="flex items-center gap-3 rounded-xl border border-slate-200 p-4 transition hover:border-brand-300 hover:bg-brand-50/40">
              <WalletCards className="h-5 w-5 text-brand-700" /><span className="min-w-0 flex-1"><span className="block text-sm font-semibold text-slate-900">{"Issue commercial licenses"}</span><span className="mt-1 block text-xs text-slate-500">{"For tenants in your network"}</span></span><ArrowUpRight className="h-4 w-4 text-slate-400" />
            </Link>
            <Link href="/vendor/team" className="flex items-center gap-3 rounded-xl border border-slate-200 p-4 transition hover:border-brand-300 hover:bg-brand-50/40">
              <Users className="h-5 w-5 text-brand-700" /><span className="min-w-0 flex-1"><span className="block text-sm font-semibold text-slate-900">{"Manage network team"}</span><span className="mt-1 block text-xs text-slate-500">{"Invite users and manage roles"}</span></span><ArrowUpRight className="h-4 w-4 text-slate-400" />
            </Link>
            <Link href="/vendor/security" className="flex items-center gap-3 rounded-xl border border-slate-200 p-4 transition hover:border-brand-300 hover:bg-brand-50/40">
              <ShieldCheck className="h-5 w-5 text-brand-700" /><span className="min-w-0 flex-1"><span className="block text-sm font-semibold text-slate-900">{"Account security"}</span><span className="mt-1 block text-xs text-slate-500">{"Security and email settings"}</span></span><ArrowUpRight className="h-4 w-4 text-slate-400" />
            </Link>
          </CardContent>
        </Card>

        <Card id="support">
          <CardHeader className="flex flex-row items-center justify-between space-y-0"><CardTitle>{"Support overview"}</CardTitle><ClipboardList className="h-5 w-5 text-slate-400" /></CardHeader>
          <CardContent>
            <div className="flex items-end justify-between gap-3">
              <div><p className="text-3xl font-semibold text-slate-900">{escalations.isLoading ? "..." : openTickets.length}</p><p className="mt-1 text-sm text-slate-500">{"Escalations requiring attention"}</p></div>
              <Badge status={openTickets.length ? "open" : "resolved"}>{openTickets.length ? ("Needs attention") : ("All clear")}</Badge>
            </div>
            <div className="mt-5 space-y-3">
              {escalations.isLoading ? <p className="text-sm text-slate-500">{"Loading support queue..."}</p> : openTickets.length === 0 ? <p className="rounded-lg bg-slate-50 p-4 text-sm text-slate-500">{"There are no open support escalations."}</p> : openTickets.slice(0, 4).map((ticket) => <div key={ticket.id} className="flex items-center justify-between gap-3 border-b border-slate-100 pb-3 last:border-0 last:pb-0"><span className="min-w-0 truncate text-sm font-medium text-slate-800">{ticket.subject || ("Support request")}</span><Badge status={ticket.status}>{ticket.status}</Badge></div>)}
            </div>
            <p className="mt-4 text-xs text-slate-500">{"Support queue data is scoped by the Vendor support API permissions."}</p>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <Card><CardHeader><CardTitle>{"Reseller network health"}</CardTitle></CardHeader><CardContent className="space-y-3">
          <div className="flex justify-between text-sm"><span className="text-slate-600">{"Active"}</span><strong>{activeResellers}</strong></div><div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-emerald-500" style={{ width: `${resellerRows.length ? (activeResellers / resellerRows.length) * 100 : 0}%` }} /></div>
          <div className="flex justify-between text-sm"><span className="text-slate-600">{"Inactive / suspended"}</span><strong>{Math.max(0, resellerRows.length - activeResellers)}</strong></div>
          <Link href="/vendor/resellers" className="inline-flex items-center gap-1 pt-2 text-sm font-medium text-brand-700 hover:underline">{"View resellers"}<ArrowUpRight className="h-4 w-4" /></Link>
        </CardContent></Card>
        <Card><CardHeader><CardTitle>{"Direct customer health"}</CardTitle></CardHeader><CardContent className="space-y-3">
          <div className="flex justify-between text-sm"><span className="text-slate-600">{"Active"}</span><strong>{activeCustomers}</strong></div><div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-emerald-500" style={{ width: `${customerRows.length ? (activeCustomers / customerRows.length) * 100 : 0}%` }} /></div>
          <div className="flex justify-between text-sm"><span className="text-slate-600">{"Inactive / suspended"}</span><strong>{Math.max(0, customerRows.length - activeCustomers)}</strong></div>
          <Link href="/vendor/customers" className="inline-flex items-center gap-1 pt-2 text-sm font-medium text-brand-700 hover:underline">{"View customers"}<ArrowUpRight className="h-4 w-4" /></Link>
        </CardContent></Card>
      </section>
    </main>
  </>;
}
