"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { getCustomerDashboard, getUsageSummary, listRuns } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { BarChart3 } from "lucide-react";

export default function ReportsPage() {
  const dash = useQuery({ queryKey: ["reports-dashboard"], queryFn: getCustomerDashboard });
  const usage = useQuery({ queryKey: ["reports-usage"], queryFn: () => getUsageSummary() });
  const runs = useQuery({ queryKey: ["reports-runs"], queryFn: () => listRuns() });
  const success = dash.data?.workflow_run_count ? Math.round((dash.data.successful_workflow_run_count / dash.data.workflow_run_count) * 100) : 0;
  return <><Header title="Reports" description="Operational performance, reliability and AI cost summary" /><div className="space-y-6 p-6">
    {(dash.isLoading || usage.isLoading || runs.isLoading) && <Spinner/>}
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Metric label="AI employees" value={dash.data?.active_employee_count ?? 0}/>
      <Metric label="Runs" value={dash.data?.workflow_run_count ?? 0}/>
      <Metric label="Success rate" value={`${success}%`}/>
      <Metric label="AI cost" value={formatCurrency(usage.data?.cost_usd ?? 0)}/>
    </div>
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><BarChart3 className="h-4 w-4"/>Execution report</CardTitle></CardHeader><CardContent><div className="grid gap-3 text-sm"><Row label="Total tokens" value={(usage.data?.total_tokens ?? 0).toLocaleString()}/><Row label="Provider calls" value={(usage.data?.calls ?? 0).toLocaleString()}/><Row label="Average latency" value={`${Math.round(usage.data?.avg_latency_ms ?? 0)} ms`}/><Row label="Failed calls" value={String(dash.data?.usage.failed_calls ?? 0)}/><Row label="Pending approvals" value={String(dash.data?.pending_approval_count ?? 0)}/></div><Link href="/analytics" className="mt-5 inline-block text-sm font-medium text-brand-700 hover:underline">Open detailed analytics →</Link></CardContent></Card>
    <Card><CardHeader><CardTitle>Recent runs</CardTitle></CardHeader><CardContent><div className="space-y-2">{(runs.data ?? []).slice(0,10).map(r=><Link key={r.id} href={`/runs/${r.id}`} className="flex justify-between rounded-lg border p-3 text-sm hover:bg-gray-50"><span>{r.employee_name || r.employee_slug || r.employee_id.slice(0,8)}</span><span className="text-gray-500">{r.status}</span></Link>)}</div></CardContent></Card>
  </div></>;
}
function Metric({label,value}:{label:string;value:string|number}){return <Card><CardContent><p className="text-xs text-gray-500">{label}</p><p className="mt-1 text-2xl font-semibold">{value}</p></CardContent></Card>}
function Row({label,value}:{label:string;value:string}){return <div className="flex justify-between border-b py-2 last:border-0"><span className="text-gray-500">{label}</span><b>{value}</b></div>}
