"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Badge } from "@/components/ui/badge";
import { getCustomerDashboard, getErrorMessage, getUsageSummary, listRuns, getROIAnalytics } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { Activity, Bot, Coins, Gauge, Play, Timer, TriangleAlert, TrendingUp, Users } from "lucide-react";
import { StatCard } from "@/components/dashboard/stat-card";
import { BarChart, ProgressBar } from "@/components/dashboard/charts";
import Link from "next/link";

export default function AnalyticsPage() {
  const roi = useQuery({ queryKey: ["roi-analytics"], queryFn: getROIAnalytics, refetchInterval: 15000 });
  const dash = useQuery({ queryKey: ["customer-dashboard"], queryFn: getCustomerDashboard, refetchInterval: 15000 });
  const usage = useQuery({ queryKey: ["usage-summary"], queryFn: () => getUsageSummary(), refetchInterval: 15000 });
  const runs = useQuery({ queryKey: ["runs", "analytics"], queryFn: () => listRuns(), refetchInterval: 15000 });
  const recent = useMemo(() => [...(runs.data ?? [])].sort((a,b) => new Date(a.created_at).getTime()-new Date(b.created_at).getTime()).slice(-12), [runs.data]);
  const values = recent.map(r => r.total_tokens || 0);
  const labels = recent.map(r => formatDate(r.created_at).split(",")[0] ?? "Run");
  const successRate = dash.data?.workflow_run_count ? Math.round((dash.data.successful_workflow_run_count / dash.data.workflow_run_count) * 100) : 0;
  return <>
    <Header title="Analytics & Operations" description="Business KPIs, AI usage, reliability and cost attribution" />
    <div className="space-y-6 p-6">
      {(dash.isLoading || usage.isLoading || runs.isLoading || roi.isLoading) && <Spinner />}
      {(dash.error || usage.error || runs.error || roi.error) && <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{getErrorMessage(dash.error || usage.error || runs.error || roi.error)}</div>}
      {dash.data && usage.data && <>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{roi.data && <><StatCard icon={Users} label="Conversations" value={roi.data.conversations} hint={`${roi.data.ai_resolution_rate}% AI resolved`} /><StatCard icon={TrendingUp} label="Influenced revenue" value={formatCurrency(roi.data.influenced_revenue)} hint={`${roi.data.influenced_orders} AI-attributed orders`} /></>} <StatCard icon={Bot} label="AI employees" value={dash.data.active_employee_count} hint={`${dash.data.employee_count} total`} href="/employees" /><StatCard icon={Play} label="Workflow runs" value={dash.data.workflow_run_count} hint={`${dash.data.running_workflow_run_count} active`} href="/runs" /><StatCard icon={Gauge} label="Success rate" value={`${successRate}%`} hint={`${dash.data.failed_workflow_run_count} failed`} /><StatCard icon={Coins} label="AI cost" value={formatCurrency(usage.data.cost_usd)} hint={`${usage.data.total_tokens.toLocaleString()} tokens`} href="/usage" /></div>
        <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]"><Card><CardHeader><div><CardTitle>Token activity</CardTitle><p className="mt-1 text-xs text-gray-500">Last 12 loaded runs</p></div></CardHeader><CardContent><BarChart values={values.length ? values : [0]} labels={labels.length ? labels : ["No data"]} /></CardContent></Card><Card><CardHeader><CardTitle>Reliability</CardTitle></CardHeader><CardContent className="space-y-5"><ProgressBar value={successRate} label="Successful workflow runs" /><div className="grid grid-cols-2 gap-3 text-sm"><div className="rounded-lg bg-gray-50 p-3"><p className="text-xs text-gray-500">Provider calls</p><p className="mt-1 text-xl font-semibold">{usage.data.calls.toLocaleString()}</p></div><div className="rounded-lg bg-gray-50 p-3"><p className="text-xs text-gray-500">Avg latency</p><p className="mt-1 text-xl font-semibold">{Math.round(usage.data.avg_latency_ms)} ms</p></div></div><div className="flex items-center justify-between border-t pt-3 text-sm"><span className="text-gray-500">Pending approvals</span><span className="font-semibold">{dash.data.pending_approval_count}</span></div></CardContent></Card></div>
        <div className="grid gap-6 lg:grid-cols-3"><Card><CardHeader><CardTitle>Operations</CardTitle></CardHeader><CardContent className="space-y-3"><Metric icon={Timer} label="Avg latency" value={`${Math.round(dash.data.usage.avg_latency_ms)} ms`} /><Metric icon={Activity} label="Active schedules" value={dash.data.active_schedule_count} /><Metric icon={Users} label="Active webhooks" value={dash.data.active_webhook_count} /><Metric icon={TriangleAlert} label="Failed AI calls" value={dash.data.usage.failed_calls} /></CardContent></Card><Card className="lg:col-span-2"><CardHeader><CardTitle>Recent execution</CardTitle><Link href="/runs" className="text-xs font-medium text-brand-600">View all →</Link></CardHeader><CardContent className="p-0"><div className="divide-y">{(runs.data ?? []).slice(0,8).map(r => <div key={r.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3"><div><Link href={`/runs/${r.id}`} className="font-mono text-xs text-brand-600">{r.id.slice(0,12)}…</Link><p className="text-xs text-gray-500">{r.employee_name || r.employee_slug || r.employee_id.slice(0,8)} · {formatDate(r.created_at)}</p></div><div className="flex items-center gap-4 text-xs text-gray-500"><Badge status={r.status}/><span>{r.total_tokens.toLocaleString()} tokens</span><span>{formatCurrency(r.total_cost_usd)}</span></div></div>)}{!(runs.data ?? []).length && <p className="p-5 text-sm text-gray-500">No runs yet.</p>}</div></CardContent></Card></div>
      </>}
    </div>
  </>;
}
function Metric({ icon: Icon, label, value }: { icon: typeof Timer; label: string; value: string | number }) { return <div className="flex items-center justify-between border-b border-gray-100 pb-3"><div className="flex items-center gap-2"><Icon className="h-4 w-4 text-brand-600"/><span className="text-sm text-gray-500">{label}</span></div><span className="font-semibold text-gray-900">{value}</span></div>; }
