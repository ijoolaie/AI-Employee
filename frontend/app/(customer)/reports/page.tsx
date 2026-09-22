"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { getCustomerDashboard, getUsageSummary, listRuns } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { BarChart3 } from "lucide-react";
import { useI18n } from "@/lib/i18n/provider";

export default function ReportsPage() {
  const { t } = useI18n();
  const m = t.reports;
  const dash = useQuery({ queryKey: ["reports-dashboard"], queryFn: getCustomerDashboard });
  const usage = useQuery({ queryKey: ["reports-usage"], queryFn: () => getUsageSummary() });
  const runs = useQuery({ queryKey: ["reports-runs"], queryFn: () => listRuns() });
  const success = dash.data?.workflow_run_count ? Math.round((dash.data.successful_workflow_run_count / dash.data.workflow_run_count) * 100) : 0;
  return <><Header title={m.title} description={m.description} /><div className="space-y-6 p-6">
    {(dash.isLoading || usage.isLoading || runs.isLoading) && <Spinner/>}{(dash.error || usage.error || runs.error) && <div role="alert" className="flex items-center gap-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"><span>{m.loadError}</span><Button variant="outline" onClick={() => { void dash.refetch(); void usage.refetch(); void runs.refetch(); }}>{m.retry}</Button></div>}
    {!dash.isLoading && !usage.isLoading && !runs.isLoading && !dash.error && !usage.error && !runs.error && !(runs.data ?? []).length && <EmptyState title={m.noRuns} description={m.noRuns} />}
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Metric label={m.aiEmployees} value={dash.data?.active_employee_count ?? 0}/>
      <Metric label={m.runs} value={dash.data?.workflow_run_count ?? 0}/>
      <Metric label={m.successRate} value={`${success}%`}/>
      <Metric label={m.aiCost} value={formatCurrency(usage.data?.cost_usd ?? 0)}/>
    </div>
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><BarChart3 className="h-4 w-4"/>{m.executionReport}</CardTitle></CardHeader><CardContent><div className="grid gap-3 text-sm"><Row label={m.totalTokens} value={(usage.data?.total_tokens ?? 0).toLocaleString()}/><Row label={m.providerCalls} value={(usage.data?.calls ?? 0).toLocaleString()}/><Row label={m.averageLatency} value={`${Math.round(usage.data?.avg_latency_ms ?? 0)} ms`}/><Row label={m.failedCalls} value={String(dash.data?.usage.failed_calls ?? 0)}/><Row label={m.pendingApprovals} value={String(dash.data?.pending_approval_count ?? 0)}/></div><Link href="/analytics" className="mt-5 inline-block text-sm font-medium text-brand-700 hover:underline">{m.openAnalytics}</Link></CardContent></Card>
    <Card><CardHeader><CardTitle>{m.recentRuns}</CardTitle></CardHeader><CardContent><div className="space-y-2">{(runs.data ?? []).slice(0,10).map(r=><Link key={r.id} href={`/runs/${r.id}`} className="flex justify-between rounded-lg border p-3 text-sm hover:bg-gray-50"><span>{r.employee_name || r.employee_slug || r.employee_id.slice(0,8)}</span><span className="text-gray-500">{r.status}</span></Link>)}</div></CardContent></Card>
  </div></>;
}
function Metric({label,value}:{label:string;value:string|number}){return <Card><CardContent><p className="text-xs text-gray-500">{label}</p><p className="mt-1 text-2xl font-semibold">{value}</p></CardContent></Card>}
function Row({label,value}:{label:string;value:string}){return <div className="flex justify-between border-b py-2 last:border-0"><span className="text-gray-500">{label}</span><b>{value}</b></div>}
