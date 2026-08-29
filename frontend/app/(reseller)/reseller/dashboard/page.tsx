"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Building2, Bot, LifeBuoy, Users, ArrowRight, Activity } from "lucide-react";
import { api } from "@/lib/api";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ClientSummary { id: string; name: string; slug: string; status: string; tenant_kind: string; created_at: string }

async function listClients() {
  const response = await api.get<{ success: boolean; data: ClientSummary[] }>("/reseller-admin/clients");
  if (!response.data.success) throw new Error("Unable to load clients");
  return response.data.data;
}

export default function ResellerDashboardPage() {
  const clients = useQuery({ queryKey: ["reseller-clients"], queryFn: listClients });
  const items = clients.data ?? [];
  const active = items.filter(c => c.status === "active").length;

  return <>
    <Header title="Reseller Overview" description="Manage your client portfolio, service team, and AI workforce." />
    <div className="space-y-6 p-6">
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric icon={Building2} label="Clients" value={items.length} href="/reseller/clients" />
        <Metric icon={Activity} label="Active clients" value={active} href="/reseller/clients" />
        <Metric icon={Users} label="Service team" value="Manage" href="/reseller/team" />
        <Metric icon={Bot} label="AI workforce" value="Manage" href="/reseller/ai-employees" />
      </section>
      <section className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between"><CardTitle>Client portfolio</CardTitle><Link href="/reseller/clients" className="text-sm font-medium text-brand-600">View all</Link></CardHeader>
          <CardContent>
            {clients.isLoading ? <p className="text-sm text-gray-500">Loading clients…</p> : clients.isError ? <p className="text-sm text-red-600">Could not load the client portfolio.</p> : items.length === 0 ? <EmptyState title="No clients yet" text="Client tenants created under this reseller will appear here." href="/reseller/clients" /> : <div className="divide-y">{items.slice(0, 6).map(client => <Link key={client.id} href="/reseller/clients" className="flex items-center justify-between py-3 hover:bg-gray-50"><div><p className="font-medium text-gray-900">{client.name}</p><p className="text-xs text-gray-500">{client.slug}</p></div><span className={client.status === "active" ? "rounded-full bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700" : "rounded-full bg-gray-100 px-2 py-1 text-xs font-medium text-gray-600"}>{client.status}</span></Link>)}</div>}
          </CardContent>
        </Card>
        <Card><CardHeader><CardTitle>Reseller command center</CardTitle></CardHeader><CardContent className="space-y-3"><QuickLink href="/reseller/support" icon={LifeBuoy} title="Client support" text="Handle escalations and operational issues." /><QuickLink href="/reseller/team" icon={Users} title="Service team" text="Manage human operators and roles." /><QuickLink href="/reseller/ai-employees" icon={Bot} title="AI workforce" text="Maintain AI employees used across your operation." /></CardContent></Card>
      </section>
    </div>
  </>;
}

function Metric({ icon: Icon, label, value, href }: { icon: typeof Building2; label: string; value: string | number; href: string }) { return <Link href={href}><Card className="transition hover:-translate-y-0.5 hover:shadow-md"><CardContent className="flex items-center gap-3 p-5"><div className="rounded-lg bg-slate-100 p-2"><Icon className="h-5 w-5 text-slate-700" /></div><div><p className="text-xs text-gray-500">{label}</p><p className="text-xl font-semibold text-gray-900">{value}</p></div></CardContent></Card></Link>; }
function QuickLink({ href, icon: Icon, title, text }: { href: string; icon: typeof LifeBuoy; title: string; text: string }) { return <Link href={href} className="flex gap-3 rounded-lg border border-gray-100 p-3 hover:bg-gray-50"><Icon className="mt-0.5 h-5 w-5 text-brand-600" /><div><p className="text-sm font-medium text-gray-900">{title}</p><p className="text-xs text-gray-500">{text}</p></div><ArrowRight className="ml-auto mt-1 h-4 w-4 text-gray-400" /></Link>; }
function EmptyState({ title, text, href }: { title: string; text: string; href: string }) { return <div className="rounded-lg border border-dashed border-gray-200 p-8 text-center"><p className="font-medium text-gray-900">{title}</p><p className="mt-1 text-sm text-gray-500">{text}</p><Link href={href} className="mt-4 inline-flex rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white">Open clients</Link></div>; }
