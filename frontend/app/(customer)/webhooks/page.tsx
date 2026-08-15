"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, Eye, EyeOff, Link2, Plus, RefreshCw, RotateCcw, ToggleLeft, ToggleRight } from "lucide-react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage, listWorkflows, listWorkflowEventTriggers, createWorkflowEventTrigger, updateWorkflowEventTrigger, rotateWorkflowEventTriggerSecret, listWorkflowEventDeliveries, replayWorkflowEventDelivery } from "@/lib/api";
import type { WorkflowEventDelivery, WorkflowEventTrigger } from "@/types";

function formatDate(value: string | null | undefined) { return value ? new Date(value).toLocaleString() : "—"; }

export default function WebhooksPage() {
  const qc = useQueryClient();
  const workflowsQ = useQuery({ queryKey: ["workflows"], queryFn: listWorkflows });
  const workflows = useMemo(() => (workflowsQ.data ?? []).filter(w => w.is_active), [workflowsQ.data]);
  const [workflowId, setWorkflowId] = useState("");
  const [eventType, setEventType] = useState("workflow.completed");
  const [selectedTrigger, setSelectedTrigger] = useState<WorkflowEventTrigger | null>(null);
  const [secret, setSecret] = useState<string | null>(null);
  const [showSecret, setShowSecret] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const triggersQ = useQuery({
    queryKey: ["workflow-event-triggers", workflowId],
    queryFn: () => listWorkflowEventTriggers(workflowId),
    enabled: !!workflowId,
    refetchInterval: 10000,
  });
  const deliveriesQ = useQuery({
    queryKey: ["workflow-event-deliveries", selectedTrigger?.id],
    queryFn: () => listWorkflowEventDeliveries(selectedTrigger?.id),
    enabled: !!selectedTrigger,
    refetchInterval: 5000,
  });

  const createM = useMutation({
    mutationFn: () => createWorkflowEventTrigger(workflowId, eventType.trim()),
    onSuccess: (data) => { setError(null); setSecret(data.webhook_secret ?? null); setSelectedTrigger(data); qc.invalidateQueries({ queryKey: ["workflow-event-triggers", workflowId] }); },
    onError: e => setError(getErrorMessage(e)),
  });
  const toggleM = useMutation({
    mutationFn: (t: WorkflowEventTrigger) => updateWorkflowEventTrigger(t.workflow_id, t.id, { is_active: !t.is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["workflow-event-triggers", workflowId] }),
    onError: e => setError(getErrorMessage(e)),
  });
  const rotateM = useMutation({
    mutationFn: (t: WorkflowEventTrigger) => rotateWorkflowEventTriggerSecret(t.workflow_id, t.id),
    onSuccess: data => { setError(null); setSecret(data.webhook_secret ?? null); setSelectedTrigger(data); qc.invalidateQueries({ queryKey: ["workflow-event-triggers", workflowId] }); },
    onError: e => setError(getErrorMessage(e)),
  });
  const replayM = useMutation({
    mutationFn: (id: string) => replayWorkflowEventDelivery(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["workflow-event-deliveries", selectedTrigger?.id] }),
    onError: e => setError(getErrorMessage(e)),
  });

  const triggers = triggersQ.data ?? [];
  const deliveries: WorkflowEventDelivery[] = deliveriesQ.data ?? [];
  const selected = triggers.find(t => t.id === selectedTrigger?.id) ?? selectedTrigger;

  function copy(value: string) { navigator.clipboard?.writeText(value).catch(() => undefined); }

  return <>
    <Header title="Webhooks" description="Manage workflow event triggers, secrets, delivery history and replay." />
    <div className="space-y-6 p-6">
      {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><Plus className="h-5 w-5" />Create webhook trigger</CardTitle></CardHeader>
        <CardContent><div className="grid gap-4 md:grid-cols-3">
          <label className="text-sm"><span className="mb-1 block text-gray-500">Workflow</span><select value={workflowId} onChange={e => { setWorkflowId(e.target.value); setSelectedTrigger(null); setSecret(null); }} className="h-10 w-full rounded-lg border border-gray-300 bg-white px-3"><option value="">Select workflow…</option>{workflows.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}</select></label>
          <label className="text-sm"><span className="mb-1 block text-gray-500">Event type</span><input value={eventType} onChange={e => setEventType(e.target.value)} className="h-10 w-full rounded-lg border border-gray-300 px-3" placeholder="order.created" /></label>
          <div className="flex items-end"><Button className="w-full" disabled={!workflowId || !eventType.trim() || createM.isPending} onClick={() => createM.mutate()}>{createM.isPending ? "Creating…" : "Create trigger"}</Button></div>
        </div><p className="mt-3 text-xs text-gray-500">The secret is shown only when the trigger is created or rotated. Store it securely.</p></CardContent>
      </Card>

      {secret && selected && <Card><CardHeader><CardTitle>New webhook secret</CardTitle></CardHeader><CardContent className="space-y-3">
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">Copy this secret now. The server stores it encrypted and does not expose it in the trigger catalog.</div>
        <div className="flex gap-2"><input readOnly value={showSecret ? secret : "•".repeat(Math.min(secret.length, 32))} className="h-10 flex-1 rounded-lg border border-gray-300 px-3 font-mono text-sm" /><Button variant="secondary" onClick={() => setShowSecret(v => !v)}>{showSecret ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}</Button><Button variant="secondary" onClick={() => copy(secret)}><Copy className="mr-2 h-4 w-4" />Copy</Button></div>
        <div className="flex gap-2 text-xs text-gray-600"><span>Endpoint:</span><code>{selected.webhook_url ?? `/api/v1/webhooks/workflows/${selected.id}`}</code><Button variant="secondary" onClick={() => copy(selected.webhook_url ?? `/api/v1/webhooks/workflows/${selected.id}`)}><Link2 className="h-3.5 w-3.5" /></Button></div>
      </CardContent></Card>}

      <Card><CardHeader><CardTitle>Trigger catalog</CardTitle></CardHeader><CardContent className="p-0">
        {!workflowId ? <div className="p-8 text-center text-sm text-gray-500">Select a workflow to manage its webhook triggers.</div> : triggersQ.isLoading ? <div className="p-8"><Spinner /></div> : triggers.length === 0 ? <div className="p-8 text-center text-sm text-gray-500">No webhook triggers for this workflow.</div> : <div className="overflow-auto"><table className="w-full text-left text-sm"><thead><tr className="border-b bg-gray-50 text-xs uppercase text-gray-500"><th className="px-5 py-3">Event</th><th className="px-5 py-3">Status</th><th className="px-5 py-3">Created</th><th className="px-5 py-3">Secret rotated</th><th className="px-5 py-3">Actions</th></tr></thead><tbody>{triggers.map(t => <tr key={t.id} className={`border-b hover:bg-gray-50 ${selected?.id === t.id ? "bg-brand-50/40" : ""}`} onClick={() => { setSelectedTrigger(t); setSecret(null); }}><td className="px-5 py-3 font-medium">{t.event_type}</td><td className="px-5 py-3"><span className={`rounded-full px-2 py-1 text-xs ${t.is_active ? "bg-emerald-100 text-emerald-700" : "bg-gray-100 text-gray-600"}`}>{t.is_active ? "Active" : "Paused"}</span></td><td className="px-5 py-3 text-gray-600">{formatDate(t.created_at)}</td><td className="px-5 py-3 text-gray-600">{formatDate(t.secret_rotated_at)}</td><td className="px-5 py-3"><div className="flex flex-wrap gap-3"><button className="inline-flex items-center gap-1 text-brand-600 hover:underline" onClick={e => { e.stopPropagation(); toggleM.mutate(t); }} disabled={toggleM.isPending}>{t.is_active ? <ToggleRight className="h-4 w-4" /> : <ToggleLeft className="h-4 w-4" />}{t.is_active ? "Pause" : "Resume"}</button><button className="inline-flex items-center gap-1 text-amber-700 hover:underline" onClick={e => { e.stopPropagation(); if (window.confirm("Rotate this webhook secret? Existing signatures will stop working.")) rotateM.mutate(t); }} disabled={rotateM.isPending}><RotateCcw className="h-4 w-4" />Rotate secret</button></div></td></tr>)}</tbody></table></div>}
      </CardContent></Card>

      <Card><CardHeader><CardTitle>Delivery history</CardTitle></CardHeader><CardContent className="p-0">
        {!selected ? <div className="p-8 text-center text-sm text-gray-500">Select a trigger to view deliveries.</div> : deliveriesQ.isLoading ? <div className="p-8"><Spinner /></div> : deliveries.length === 0 ? <div className="p-8 text-center text-sm text-gray-500">No deliveries yet.</div> : <div className="overflow-auto"><table className="w-full text-left text-sm"><thead><tr className="border-b bg-gray-50 text-xs uppercase text-gray-500"><th className="px-5 py-3">Event ID</th><th className="px-5 py-3">Status</th><th className="px-5 py-3">Attempts</th><th className="px-5 py-3">Received</th><th className="px-5 py-3">Run</th><th className="px-5 py-3">Actions</th></tr></thead><tbody>{deliveries.map(d => <tr key={d.id} className="border-b"><td className="px-5 py-3 font-mono text-xs">{d.event_id}</td><td className="px-5 py-3">{d.status}</td><td className="px-5 py-3">{d.attempts}</td><td className="px-5 py-3 text-gray-600">{formatDate(d.received_at)}</td><td className="px-5 py-3 font-mono text-xs">{d.workflow_run_id ?? "—"}</td><td className="px-5 py-3"><Button variant="secondary" disabled={replayM.isPending || d.status === "accepted"} onClick={() => { if (window.confirm("Replay this delivery and create a new workflow run?")) replayM.mutate(d.id); }}><RefreshCw className="mr-2 h-3.5 w-3.5" />Replay</Button></td></tr>)}</tbody></table></div>}
      </CardContent></Card>
    </div>
  </>;
}
