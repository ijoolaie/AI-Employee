"use client";

import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { getAuditLogs, getErrorMessage, getOperationsMetrics, listDeadLetters, listRuns, replayDeadLetter } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, Bug, Database, Gauge, RotateCcw, ScrollText, Server, Terminal } from "lucide-react";
import Link from "next/link";

export default function DeveloperPage() {
  const queryClient = useQueryClient();
  const metrics = useQuery({ queryKey: ["developer", "metrics"], queryFn: getOperationsMetrics, refetchInterval: 10000 });
  const logs = useQuery({ queryKey: ["developer", "audit"], queryFn: () => getAuditLogs({ limit: 50 }), refetchInterval: 10000 });
  const dead = useQuery({ queryKey: ["developer", "dead"], queryFn: () => listDeadLetters(50), refetchInterval: 10000 });
  const runs = useQuery({ queryKey: ["developer", "runs"], queryFn: () => listRuns(), refetchInterval: 10000 });
  const replay = useMutation({
    mutationFn: replayDeadLetter,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["developer"] }),
  });

  const recentRuns = [...(runs.data ?? [])].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).slice(0, 12);
  const loading = metrics.isLoading || logs.isLoading || dead.isLoading || runs.isLoading;

  return (
    <>
      <Header title="Developer Console" description="Tenant-scoped trace, logs, performance and recovery tools" />
      <div className="space-y-6 p-6">
        {loading && <Spinner />}
        {(metrics.error || logs.error || dead.error || runs.error) && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {getErrorMessage(metrics.error || logs.error || dead.error || runs.error)}
          </div>
        )}

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Metric icon={Activity} label="Workflow runs" value={metrics.data?.workflow_runs_total ?? 0} />
          <Metric icon={Terminal} label="Workflow steps" value={metrics.data?.workflow_steps_total ?? 0} />
          <Metric icon={Database} label="Outbox pending" value={metrics.data?.outbox.pending ?? 0} />
          <Metric icon={Bug} label="Dead letters" value={metrics.data?.outbox.dead ?? 0} />
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader><CardTitle className="flex items-center gap-2"><Gauge className="h-4 w-4" />Performance & runtime</CardTitle></CardHeader>
            <CardContent className="space-y-3 text-sm">
              <Row label="Outbox processing" value={String(metrics.data?.outbox.processing ?? 0)} />
              <Row label="Recent runs loaded" value={String(recentRuns.length)} />
              <Row label="Active runs" value={String(recentRuns.filter((r) => ["pending", "queued", "running", "waiting"].includes(r.status)).length)} />
              <Row label="Failed recent runs" value={String(recentRuns.filter((r) => r.status === "failed").length)} />
              <p className="pt-2 text-xs text-gray-500">Use a run detail page for the full execution trace, provider latency, token usage and cost attribution.</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="flex items-center gap-2"><Server className="h-4 w-4" />Dead-letter recovery</CardTitle></CardHeader>
            <CardContent>
              {(dead.data ?? []).length === 0 ? <p className="text-sm text-gray-500">No dead-letter messages.</p> : (
                <div className="space-y-2">
                  {(dead.data ?? []).slice(0, 8).map((item) => (
                    <div key={item.id} className="rounded-lg border border-gray-100 bg-gray-50 p-3">
                      <div className="flex items-center justify-between gap-3">
                        <div><p className="text-sm font-medium text-gray-900">{item.kind}</p><p className="text-xs text-gray-500">{item.attempts} attempts · {formatDate(item.dead_at)}</p></div>
                        <button disabled={replay.isPending} onClick={() => replay.mutate(item.id)} className="inline-flex items-center gap-1 rounded-md border border-gray-200 bg-white px-2 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"><RotateCcw className="h-3 w-3" />Replay</button>
                      </div>
                      {item.last_error && <p className="mt-2 line-clamp-2 text-xs text-red-700">{item.last_error}</p>}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><ScrollText className="h-4 w-4" />Recent audit logs</CardTitle></CardHeader>
          <CardContent>
            {(logs.data ?? []).length === 0 ? <p className="text-sm text-gray-500">No audit events recorded.</p> : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead><tr className="border-b border-gray-100 text-xs uppercase text-gray-500"><th className="px-3 py-2">Time</th><th className="px-3 py-2">Action</th><th className="px-3 py-2">Status</th><th className="px-3 py-2">Request</th></tr></thead>
                  <tbody>{(logs.data ?? []).map((log) => <tr key={log.id} className="border-b border-gray-50"><td className="px-3 py-2 text-gray-500">{formatDate(log.created_at)}</td><td className="px-3 py-2 font-medium text-gray-900">{log.action}</td><td className="px-3 py-2"><Badge status={log.status} /></td><td className="px-3 py-2 font-mono text-xs text-gray-500">{log.request_id ? `${log.request_id.slice(0, 12)}…` : "—"}</td></tr>)}</tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Activity className="h-4 w-4" />Recent runs</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {recentRuns.map((run) => <div key={run.id} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-gray-100 p-3"><div><Link href={`/runs/${run.id}`} className="font-medium text-brand-600 hover:underline">Run {run.id.slice(0, 8)}…</Link><p className="text-xs text-gray-500">{run.employee_name || run.employee_slug || run.employee_id.slice(0, 8)} · {formatDate(run.created_at)}</p></div><div className="flex items-center gap-4 text-xs text-gray-500"><Badge status={run.status} /><span>{run.total_tokens.toLocaleString()} tokens</span><span>{formatCurrency(run.total_cost_usd)}</span></div></div>)}
              {recentRuns.length === 0 && <p className="text-sm text-gray-500">No runs yet.</p>}
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
}

function Metric({ icon: Icon, label, value }: { icon: typeof Activity; label: string; value: number }) {
  return <Card><CardContent className="flex items-center gap-3"><div className="rounded-lg bg-brand-50 p-2 text-brand-600"><Icon className="h-4 w-4" /></div><div><p className="text-xs uppercase tracking-wide text-gray-400">{label}</p><p className="text-xl font-semibold text-gray-900">{value.toLocaleString()}</p></div></CardContent></Card>;
}

function Row({ label, value }: { label: string; value: string }) {
  return <div className="flex items-center justify-between border-b border-gray-100 pb-2"><span className="text-gray-500">{label}</span><span className="font-medium text-gray-900">{value}</span></div>;
}
