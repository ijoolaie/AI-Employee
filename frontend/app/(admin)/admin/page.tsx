"use client";

import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { getAdminDashboard, getErrorMessage } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { Activity, Bot, Coins, Database, GitBranch, Layers, ListChecks, Users } from "lucide-react";

export default function AdminDashboardPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["admin-dashboard"], queryFn: getAdminDashboard, refetchInterval: 15000 });

  return (
    <>
      <Header title="Admin Dashboard" description="Platform-wide tenants, usage, cost and operational health" />
      <div className="space-y-6 p-6">
        {isLoading && <Spinner />}
        {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{getErrorMessage(error)}</div>}
        {data && <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Stat icon={Users} label="Tenants" value={`${data.active_tenants}/${data.tenants}`} hint="Active / total" />
            <Stat icon={Layers} label="Users" value={data.users.toLocaleString()} hint="Across all tenants" />
            <Stat icon={GitBranch} label="Workflows" value={data.workflows.toLocaleString()} hint={`${data.workflow_runs.toLocaleString()} runs`} />
            <Stat icon={Coins} label="AI cost" value={formatCurrency(data.total_cost_usd)} hint={`${data.total_tokens.toLocaleString()} tokens`} />
          </div>

          <div className="grid gap-4 lg:grid-cols-4">
            <HealthCard label="PostgreSQL" status={data.health.database} icon={Database} />
            <HealthCard label="Redis" status={data.health.redis} icon={Activity} />
            <HealthCard label="Celery" status={data.health.celery} icon={ListChecks} />
            <HealthCard label="AI Provider" status={data.health.ai_provider} icon={Bot} />
          </div>

          <div className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
            <Card>
              <CardHeader><CardTitle>Tenants</CardTitle></CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm"><thead><tr className="border-b border-gray-100 text-xs uppercase text-gray-500">
                    <th className="px-5 py-3 font-medium">Tenant</th><th className="px-5 py-3 font-medium">Status</th><th className="px-5 py-3 font-medium">Users</th><th className="px-5 py-3 font-medium">Runs</th><th className="px-5 py-3 font-medium">Cost</th>
                  </tr></thead><tbody>
                    {data.tenants_breakdown.map((tenant) => <tr key={tenant.id} className="border-b border-gray-50">
                      <td className="px-5 py-3"><p className="font-medium text-gray-900">{tenant.name}</p><p className="text-xs text-gray-500">{tenant.slug}</p></td>
                      <td className="px-5 py-3"><Badge status={tenant.status} /></td>
                      <td className="px-5 py-3 text-gray-600">{tenant.users}</td><td className="px-5 py-3 text-gray-600">{tenant.runs}</td><td className="px-5 py-3 text-gray-600">{formatCurrency(tenant.cost_usd)}</td>
                    </tr>)}
                  </tbody></table>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle>Provider usage</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {data.providers.length === 0 ? <p className="text-sm text-gray-500">No provider calls recorded yet.</p> : data.providers.map((provider) => <div key={provider.provider} className="rounded-lg border border-gray-100 p-3">
                  <div className="flex items-center justify-between"><span className="font-medium text-gray-900">{provider.provider}</span><span className="text-sm text-gray-500">{formatCurrency(provider.cost_usd)}</span></div>
                  <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-gray-500"><span>{provider.calls} calls</span><span>{provider.total_tokens.toLocaleString()} tokens</span><span>{provider.avg_latency_ms.toFixed(0)} ms avg</span></div>
                </div>)}
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 md:grid-cols-4">
            <Mini title="AI calls" value={data.ai_calls.toLocaleString()} />
            <Mini title="Failed workflow runs" value={data.failed_runs.toLocaleString()} />
            <Mini title="Pending outbox" value={data.pending_outbox.toLocaleString()} />
            <Mini title="Dead-letter outbox" value={data.dead_outbox.toLocaleString()} />
          </div>
          <p className="text-xs text-gray-400">Dashboard data refreshes every 15 seconds. Tenant costs are aggregated from recorded AI provider calls.</p>
        </>}
      </div>
    </>
  );
}

function Stat({ icon: Icon, label, value, hint }: { icon: React.ComponentType<{ className?: string }>; label: string; value: string; hint: string }) {
  return <Card><CardContent className="flex items-start gap-4"><div className="rounded-lg bg-brand-50 p-2.5"><Icon className="h-5 w-5 text-brand-600" /></div><div><p className="text-sm text-gray-500">{label}</p><p className="mt-0.5 text-2xl font-semibold text-gray-900">{value}</p><p className="text-xs text-gray-400">{hint}</p></div></CardContent></Card>;
}
function Mini({ title, value }: { title: string; value: string }) { return <Card><CardContent><p className="text-sm text-gray-500">{title}</p><p className="mt-2 text-2xl font-semibold text-gray-900">{value}</p></CardContent></Card>; }
function HealthCard({ label, status, icon: Icon }: { label: string; status: string; icon: React.ComponentType<{ className?: string }> }) {
  const healthy = status === "healthy" || status === "configured";
  return <Card><CardContent className="flex items-center justify-between"><div className="flex items-center gap-3"><Icon className="h-5 w-5 text-gray-500" /><div><p className="text-sm font-medium text-gray-900">{label}</p><p className="text-xs text-gray-500">{status}</p></div></div><span className={`h-2.5 w-2.5 rounded-full ${healthy ? "bg-emerald-500" : "bg-amber-500"}`} /></CardContent></Card>;
}
