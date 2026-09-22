"use client";

import { useParams } from "next/navigation";
import React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage, getWorkflow, listWorkflowVersions, listWorkflowRuns, getWorkflowRun, getWorkflowObservability, createWorkflowRun, cancelWorkflowRun, replayWorkflowRun, activateWorkflowVersion } from "@/lib/api";
import type { WorkflowRun, WorkflowVersion } from "@/types";
import { useI18n } from "@/lib/i18n/provider";

const permissionError = (e: unknown) => getErrorMessage(e).toLowerCase().includes("permission") || getErrorMessage(e).includes("403");
const terminal = ["success", "failed", "cancelled", "timed_out"];

export default function WorkflowDetailPage() {
  const params = useParams<{ id: string }>();
  const qc = useQueryClient();
  const { t } = useI18n();
  const m = t.workflowDetail;
  const [runId, setRunId] = React.useState<string | null>(null);

  const workflowQ = useQuery({ queryKey: ["workflow", params.id], queryFn: () => getWorkflow(params.id) });
  const versionsQ = useQuery({ queryKey: ["workflow-versions", params.id], queryFn: () => listWorkflowVersions(params.id), enabled: !!workflowQ.data });
  const runsQ = useQuery({ queryKey: ["workflow-runs", params.id], queryFn: () => listWorkflowRuns(params.id), enabled: !!workflowQ.data, refetchInterval: 5000 });
  const runQ = useQuery({ queryKey: ["workflow-run", params.id, runId], queryFn: () => getWorkflowRun(params.id, runId!), enabled: !!runId, refetchInterval: runId ? 3000 : false });
  const obsQ = useQuery({ queryKey: ["workflow-observability", params.id, runId], queryFn: () => getWorkflowObservability(params.id, runId!), enabled: !!runId, refetchInterval: runId ? 5000 : false });

  const refresh = () => { qc.invalidateQueries({ queryKey: ["workflow", params.id] }); qc.invalidateQueries({ queryKey: ["workflow-versions", params.id] }); qc.invalidateQueries({ queryKey: ["workflow-runs", params.id] }); };
  const runM = useMutation({ mutationFn: () => createWorkflowRun(params.id, { input_data: {} }), onSuccess: r => { setRunId(r.id); refresh(); } });
  const cancelM = useMutation({ mutationFn: () => cancelWorkflowRun(params.id, runId!, m.cancelledReason), onSuccess: refresh });
  const replayM = useMutation({ mutationFn: (id: string) => replayWorkflowRun(params.id, id), onSuccess: r => { setRunId(r.id); refresh(); } });
  const activateM = useMutation({ mutationFn: (id: string) => activateWorkflowVersion(params.id, id), onSuccess: refresh });

  if (workflowQ.isLoading) return <><Header title={m.title} /><div className="flex justify-center p-8"><Spinner /></div></>;
  if (workflowQ.error || !workflowQ.data) return <><Header title={m.title} /><div className="space-y-3 p-6"><p className="text-sm text-red-600">{permissionError(workflowQ.error) ? m.permissionDenied : m.error}</p><Button variant="secondary" onClick={() => workflowQ.refetch()}>{m.retry}</Button></div></>;

  const workflow = workflowQ.data;
  const selectedRun = runQ.data;
  const actionError = runM.error ?? replayM.error ?? activateM.error ?? cancelM.error;

  return <><Header title={workflow.name} description={`/${workflow.slug} · ${m.title}`} /><div className="space-y-6 p-6">
    {actionError && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{permissionError(actionError) ? m.permissionDenied : getErrorMessage(actionError)}</div>}
    {versionsQ.error || runsQ.error ? <Card><CardContent className="space-y-3 p-6"><p className="text-sm text-red-600">{permissionError(versionsQ.error ?? runsQ.error) ? m.permissionDenied : m.error}</p><Button variant="secondary" onClick={() => { versionsQ.refetch(); runsQ.refetch(); }}>{m.retry}</Button></CardContent></Card> : null}
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div className="text-sm text-gray-500">{m.currentVersion}: <span className="font-medium text-gray-900">{versionsQ.data?.find(v => v.is_current)?.version_number ?? m.noVersion}</span></div>
      <div className="flex gap-2"><Link href={`/workflows/${params.id}/builder`} className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">{m.builder}</Link><Button onClick={() => runM.mutate()} disabled={runM.isPending}>{runM.isPending ? m.starting : m.run}</Button></div>
    </div>

    <div className="grid grid-cols-12 gap-6">
      <Card className="col-span-12 lg:col-span-7"><CardHeader><CardTitle>{m.runHistory}</CardTitle></CardHeader><CardContent className="p-0">
        {!runsQ.isLoading && !runsQ.error && !runsQ.data?.length ? <div className="px-5 py-10 text-center text-sm text-gray-500">{m.noRuns}</div> : runsQ.isLoading ? <div className="flex justify-center p-10"><Spinner /></div> : <div className="overflow-auto"><table className="w-full text-start text-sm"><thead><tr className="border-b bg-gray-50 text-xs uppercase text-gray-500"><th className="px-5 py-3">{m.runColumn}</th><th className="px-5 py-3">{m.version}</th><th className="px-5 py-3">{m.status}</th><th className="px-5 py-3">{m.created}</th><th className="px-5 py-3">{m.actions}</th></tr></thead><tbody>{runsQ.data!.map((r: WorkflowRun) => <tr key={r.id} className={runId === r.id ? "border-b bg-brand-50" : "border-b hover:bg-gray-50"}><td className="px-5 py-3"><button className="font-mono text-xs text-brand-700 hover:underline" onClick={() => setRunId(r.id)}>{r.id.slice(0, 10)}…</button></td><td className="px-5 py-3 text-gray-600">{versionsQ.data?.find(v => v.id === r.workflow_version_id)?.version_number ?? r.workflow_version_id.slice(0, 8)}</td><td className="px-5 py-3"><Badge status={r.status} /></td><td className="px-5 py-3 text-gray-500">{new Date(r.created_at).toLocaleString()}</td><td className="px-5 py-3"><button onClick={() => replayM.mutate(r.id)} disabled={replayM.isPending} className="text-brand-600 hover:underline disabled:opacity-50">{m.replay}</button></td></tr>)}</tbody></table></div>}
      </CardContent></Card>

      <Card className="col-span-12 lg:col-span-5"><CardHeader><CardTitle>{m.versions}</CardTitle></CardHeader><CardContent className="space-y-2">{versionsQ.isLoading ? <Spinner /> : (versionsQ.data ?? []).map((v: WorkflowVersion) => <div key={v.id} className="rounded-lg border border-gray-200 p-3"><div className="flex items-center justify-between gap-2"><div><span className="font-medium">v{v.version_number}</span>{v.is_current && <span className="ms-2 rounded-full bg-emerald-100 px-2 py-1 text-xs text-emerald-700">{m.current}</span>}</div>{!v.is_current && <Button variant="secondary" className="h-8 px-3 text-xs" onClick={() => activateM.mutate(v.id)} disabled={activateM.isPending}>{m.activate}</Button>}</div><div className="mt-2 text-xs text-gray-500">{v.trigger_type} · {v.content_hash?.slice(0, 16) ?? m.noVersion}</div><div className="mt-1 text-xs text-gray-400">{new Date(v.created_at).toLocaleString()}</div></div>)}</CardContent></Card>
    </div>

    {selectedRun && <div className="grid grid-cols-12 gap-6"><Card className="col-span-12 lg:col-span-5"><CardHeader><CardTitle>{m.selectedRun}</CardTitle></CardHeader><CardContent className="space-y-2 text-sm"><p><b>{m.id}:</b> {selectedRun.id}</p><p><b>{m.version}:</b> {versionsQ.data?.find(v => v.id === selectedRun.workflow_version_id)?.version_number ?? selectedRun.workflow_version_id}</p><p><b>{m.status}:</b> <Badge status={selectedRun.status} /></p>{selectedRun.deadline_at && <p><b>{m.deadline}:</b> {new Date(selectedRun.deadline_at).toLocaleString()}</p>}<div className="flex flex-wrap gap-2 pt-2"><Button variant="secondary" onClick={() => replayM.mutate(selectedRun.id)} disabled={replayM.isPending}>{m.replayThis}</Button><Button variant="secondary" onClick={() => cancelM.mutate()} disabled={cancelM.isPending || terminal.includes(selectedRun.status)}>{m.cancel}</Button></div></CardContent></Card><Card className="col-span-12 lg:col-span-7"><CardHeader><CardTitle>{m.observability}</CardTitle></CardHeader><CardContent>{obsQ.isLoading ? <Spinner /> : obsQ.error ? <div className="space-y-3 text-sm text-red-600"><p>{permissionError(obsQ.error) ? m.permissionDenied : getErrorMessage(obsQ.error)}</p><Button variant="secondary" onClick={() => obsQ.refetch()}>{m.retry}</Button></div> : <pre className="max-h-96 overflow-auto rounded-lg bg-slate-950 p-4 text-xs text-slate-100">{JSON.stringify(obsQ.data ?? {}, null, 2)}</pre>}</CardContent></Card></div>}
  </div></>;
}
