"use client";

import { useParams } from "next/navigation";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import {
  activateWorkflowVersion,
  cancelWorkflowRun,
  createWorkflowRun,
  getErrorMessage,
  getWorkflow,
  getWorkflowObservability,
  getWorkflowRun,
  listWorkflowRuns,
  listWorkflowVersions,
  replayWorkflowRun,
} from "@/lib/api";
import type { WorkflowRun, WorkflowVersion } from "@/types";

export default function WorkflowDetailPage() {
  const params = useParams<{ id: string }>();
  const qc = useQueryClient();
  const [runId, setRunId] = useState<string | null>(null);
  const workflowQ = useQuery({ queryKey: ["workflow", params.id], queryFn: () => getWorkflow(params.id) });
  const versionsQ = useQuery({ queryKey: ["workflow-versions", params.id], queryFn: () => listWorkflowVersions(params.id) });
  const runsQ = useQuery({ queryKey: ["workflow-runs", params.id], queryFn: () => listWorkflowRuns(params.id), refetchInterval: 5000 });
  const runQ = useQuery({ queryKey: ["workflow-run", params.id, runId], queryFn: () => getWorkflowRun(params.id, runId!), enabled: !!runId, refetchInterval: runId ? 3000 : false });
  const obsQ = useQuery({ queryKey: ["workflow-observability", params.id, runId], queryFn: () => getWorkflowObservability(params.id, runId!), enabled: !!runId, refetchInterval: runId ? 5000 : false });
  const runM = useMutation({ mutationFn: () => createWorkflowRun(params.id, { input_data: {} }), onSuccess: r => { setRunId(r.id); qc.invalidateQueries({ queryKey: ["workflow-runs", params.id] }); } });
  const cancelM = useMutation({ mutationFn: () => cancelWorkflowRun(params.id, runId!, "Cancelled from Workflow UI"), onSuccess: () => qc.invalidateQueries({ queryKey: ["workflow-runs", params.id] }) });
  const replayM = useMutation({ mutationFn: (id: string) => replayWorkflowRun(params.id, id), onSuccess: r => { setRunId(r.id); qc.invalidateQueries({ queryKey: ["workflow-runs", params.id] }); } });
  const activateM = useMutation({ mutationFn: (id: string) => activateWorkflowVersion(params.id, id), onSuccess: () => { qc.invalidateQueries({ queryKey: ["workflow", params.id] }); qc.invalidateQueries({ queryKey: ["workflow-versions", params.id] }); } });

  if (workflowQ.isLoading) return <><Header title="Workflow" /><div className="p-6"><Spinner /></div></>;
  if (workflowQ.error || !workflowQ.data) return <><Header title="Workflow" /><div className="p-6 text-sm text-red-600">{getErrorMessage(workflowQ.error ?? new Error("Workflow not found"))}</div></>;
  const workflow = workflowQ.data;
  const selectedRun = runQ.data;

  return <><Header title={workflow.name} description={`/${workflow.slug} · versioned workflow management`} />
    <div className="space-y-6 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-sm text-gray-500">Current version: <span className="font-medium text-gray-900">{versionsQ.data?.find(v => v.is_current)?.version_number ?? "—"}</span></div>
        <div className="flex gap-2"><Link href={`/workflows/${params.id}/builder`} className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">Visual Builder</Link><Button onClick={() => runM.mutate()} disabled={runM.isPending}>{runM.isPending ? "Starting…" : "Run workflow"}</Button></div>
      </div>

      {(runM.error || replayM.error || activateM.error || cancelM.error) && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{getErrorMessage(runM.error || replayM.error || activateM.error || cancelM.error)}</div>}

      <div className="grid grid-cols-12 gap-6">
        <Card className="col-span-12 lg:col-span-7"><CardHeader><CardTitle>Run history</CardTitle></CardHeader><CardContent className="p-0">
          {!runsQ.data?.length ? <div className="px-5 py-10 text-center text-sm text-gray-500">No workflow runs yet.</div> : <div className="overflow-auto"><table className="w-full text-left text-sm"><thead><tr className="border-b bg-gray-50 text-xs uppercase text-gray-500"><th className="px-5 py-3">Run</th><th className="px-5 py-3">Version</th><th className="px-5 py-3">Status</th><th className="px-5 py-3">Created</th><th className="px-5 py-3">Actions</th></tr></thead><tbody>{runsQ.data.map((r: WorkflowRun) => <tr key={r.id} className={`border-b hover:bg-gray-50 ${runId === r.id ? "bg-brand-50" : ""}`}><td className="px-5 py-3"><button className="font-mono text-xs text-brand-700 hover:underline" onClick={() => setRunId(r.id)}>{r.id.slice(0, 10)}…</button></td><td className="px-5 py-3 text-gray-600">{versionsQ.data?.find(v => v.id === r.workflow_version_id)?.version_number ?? r.workflow_version_id.slice(0, 8)}</td><td className="px-5 py-3"><Badge status={r.status} /></td><td className="px-5 py-3 text-gray-500">{new Date(r.created_at).toLocaleString()}</td><td className="px-5 py-3"><button onClick={() => replayM.mutate(r.id)} disabled={replayM.isPending} className="text-brand-600 hover:underline disabled:opacity-50">Replay</button></td></tr>)}</tbody></table></div>}
        </CardContent></Card>

        <Card className="col-span-12 lg:col-span-5"><CardHeader><CardTitle>Workflow versions</CardTitle></CardHeader><CardContent className="space-y-2">
          {versionsQ.data?.map((v: WorkflowVersion) => <div key={v.id} className="rounded-lg border border-gray-200 p-3"><div className="flex items-center justify-between gap-2"><div><span className="font-medium">v{v.version_number}</span>{v.is_current && <span className="ml-2 rounded-full bg-emerald-100 px-2 py-1 text-xs text-emerald-700">Current</span>}</div>{!v.is_current && <Button variant="secondary" className="h-8 px-3 text-xs" onClick={() => activateM.mutate(v.id)} disabled={activateM.isPending}>Activate</Button>}</div><div className="mt-2 text-xs text-gray-500">{v.trigger_type} · {v.content_hash?.slice(0, 16) ?? "no hash"}</div><div className="mt-1 text-xs text-gray-400">{new Date(v.created_at).toLocaleString()}</div></div>)}
        </CardContent></Card>
      </div>

      {selectedRun && <div className="grid grid-cols-12 gap-6"><Card className="col-span-12 lg:col-span-5"><CardHeader><CardTitle>Selected run</CardTitle></CardHeader><CardContent className="space-y-2 text-sm"><p><b>ID:</b> {selectedRun.id}</p><p><b>Version:</b> {versionsQ.data?.find(v => v.id === selectedRun.workflow_version_id)?.version_number ?? selectedRun.workflow_version_id}</p><p><b>Status:</b> <Badge status={selectedRun.status} /></p>{selectedRun.deadline_at && <p><b>Deadline:</b> {new Date(selectedRun.deadline_at).toLocaleString()}</p>}<div className="flex flex-wrap gap-2 pt-2"><Button variant="secondary" onClick={() => replayM.mutate(selectedRun.id)} disabled={replayM.isPending}>Replay this run</Button><Button variant="secondary" onClick={() => cancelM.mutate()} disabled={cancelM.isPending || ["success","failed","cancelled","timed_out"].includes(selectedRun.status)}>Cancel</Button></div></CardContent></Card><Card className="col-span-12 lg:col-span-7"><CardHeader><CardTitle>Observability</CardTitle></CardHeader><CardContent><pre className="max-h-96 overflow-auto rounded-lg bg-slate-950 p-4 text-xs text-slate-100">{JSON.stringify(obsQ.data ?? {}, null, 2)}</pre></CardContent></Card></div>}
    </div></>;
}
