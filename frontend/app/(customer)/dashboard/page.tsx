"use client";

import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { getCustomerDashboard, getErrorMessage } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { useAuthStore } from "@/lib/auth-store";
import { useQuery } from "@tanstack/react-query";
import { Bot, Play, Coins, Activity, GitBranch, ShieldCheck, CalendarClock, Webhook, AlertTriangle, Zap } from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const tenant = useAuthStore((s) => s.tenant);
  const q = useQuery({ queryKey: ["customer-dashboard"], queryFn: getCustomerDashboard, refetchInterval: 15000 });
  const data = q.data;

  return <>
    <Header title={`Welcome${user?.full_name ? `, ${user.full_name}` : ""}`} description={`${tenant?.name ?? "Your organization"} — operations overview`} />
    <div className="space-y-6 p-6">
      {q.isLoading && <Spinner />}
      {q.error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{getErrorMessage(q.error)}</div>}
      {data && <>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Stat icon={Bot} label="Employees" value={`${data.active_employee_count}/${data.employee_count}`} hint="Active / total" />
          <Stat icon={GitBranch} label="Workflows" value={`${data.active_workflow_count}/${data.workflow_count}`} hint="Active / total" />
          <Stat icon={Play} label="Workflow runs" value={data.workflow_run_count.toLocaleString()} hint={`${data.running_workflow_run_count} running`} />
          <Stat icon={Coins} label="AI cost" value={formatCurrency(data.usage.cost_usd)} hint={`${data.usage.total_tokens.toLocaleString()} tokens`} />
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Mini icon={Activity} label="Success rate" value={data.workflow_run_count ? `${Math.round(data.successful_workflow_run_count / data.workflow_run_count * 100)}%` : "—"} />
          <Mini icon={AlertTriangle} label="Failed runs" value={String(data.failed_workflow_run_count)} />
          <Mini icon={ShieldCheck} label="Pending approvals" value={String(data.pending_approval_count)} href="/approvals" />
          <Mini icon={CalendarClock} label="Active schedules" value={String(data.active_schedule_count)} href="/schedules" />
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader><CardTitle>Recent workflow runs</CardTitle><Link href="/runs" className="text-sm font-medium text-brand-600 hover:underline">View all</Link></CardHeader>
            <CardContent className="p-0">
              {data.recent_runs.length === 0 ? <p className="px-5 py-8 text-center text-sm text-gray-500">No workflow runs yet.</p> : <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr className="border-b border-gray-100 text-xs uppercase text-gray-500"><th className="px-5 py-3">Run</th><th className="px-5 py-3">Status</th><th className="px-5 py-3">Cost</th><th className="px-5 py-3">Created</th></tr></thead><tbody>{data.recent_runs.map(r => <tr key={r.id} className="border-b border-gray-50"><td className="px-5 py-3 font-mono text-xs">{r.id.slice(0,8)}…</td><td className="px-5 py-3"><Badge status={r.status} /></td><td className="px-5 py-3 text-gray-600">{formatCurrency(r.total_cost_usd)}</td><td className="px-5 py-3 text-gray-500">{formatDate(r.created_at)}</td></tr>)}</tbody></table></div>}
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>AI health</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <Health label="Provider calls" value={data.usage.calls.toLocaleString()} />
              <Health label="Provider success" value={data.usage.calls ? `${Math.round(data.usage.successful_calls / data.usage.calls * 100)}%` : "—"} />
              <Health label="Average latency" value={`${Math.round(data.usage.avg_latency_ms)} ms`} />
              <Health label="Active webhooks" value={String(data.active_webhook_count)} />
              <Link href="/usage" className="block pt-2 text-sm font-medium text-brand-600 hover:underline">Open usage details →</Link>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <Quick href="/approvals" icon={ShieldCheck} title="Approvals" text={`${data.pending_approval_count} items need attention`} />
          <Quick href="/schedules" icon={CalendarClock} title="Schedules" text={`${data.active_schedule_count} active schedules`} />
          <Quick href="/webhooks" icon={Webhook} title="Webhooks" text={`${data.active_webhook_count} active triggers`} />
        </div>
      </>}
    </div>
  </>;
}

function Stat({ icon: Icon, label, value, hint }: any) { return <Card><CardContent className="flex items-start gap-4"><div className="rounded-lg bg-brand-50 p-2.5"><Icon className="h-5 w-5 text-brand-600" /></div><div><p className="text-sm text-gray-500">{label}</p><p className="mt-0.5 text-2xl font-semibold text-gray-900">{value}</p><p className="text-xs text-gray-400">{hint}</p></div></CardContent></Card>; }
function Mini({ icon: Icon, label, value, href }: any) { const body=<CardContent className="flex items-center gap-3"><Icon className="h-5 w-5 text-gray-500" /><div><p className="text-xs text-gray-500">{label}</p><p className="text-xl font-semibold text-gray-900">{value}</p></div></CardContent>; return href ? <Link href={href} className="block hover:-translate-y-0.5">{<Card>{body}</Card>}</Link> : <Card>{body}</Card>; }
function Health({ label, value }: { label: string; value: string }) { return <div className="flex items-center justify-between border-b border-gray-100 pb-3"><span className="text-sm text-gray-500">{label}</span><span className="font-semibold text-gray-900">{value}</span></div>; }
function Quick({ href, icon: Icon, title, text }: any) { return <Link href={href}><Card className="h-full hover:border-brand-200"><CardContent className="flex items-center gap-4"><Icon className="h-5 w-5 text-brand-600" /><div><p className="font-medium text-gray-900">{title}</p><p className="text-sm text-gray-500">{text}</p></div></CardContent></Card></Link>; }
