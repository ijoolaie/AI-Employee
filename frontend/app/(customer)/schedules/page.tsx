"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarClock, Pause, Play, Plus, Trash2 } from "lucide-react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage, listWorkflows, listWorkflowSchedules, createWorkflowSchedule, updateWorkflowSchedule, deleteWorkflowSchedule } from "@/lib/api";
import type { WorkflowScheduleList } from "@/types";

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleString() : "—";
}

export default function SchedulesPage() {
  const qc = useQueryClient();
  const schedulesQ = useQuery({ queryKey: ["workflow-schedules"], queryFn: listWorkflowSchedules, refetchInterval: 10000 });
  const workflowsQ = useQuery({ queryKey: ["workflows"], queryFn: listWorkflows });
  const [workflowId, setWorkflowId] = useState("");
  const [cron, setCron] = useState("0 * * * *");
  const [timezone, setTimezone] = useState("UTC");
  const [error, setError] = useState<string | null>(null);

  const createM = useMutation({
    mutationFn: () => createWorkflowSchedule(workflowId, { cron_expression: cron, timezone }),
    onSuccess: () => { setError(null); qc.invalidateQueries({ queryKey: ["workflow-schedules"] }); },
    onError: (e) => setError(getErrorMessage(e)),
  });
  const toggleM = useMutation({
    mutationFn: (s: WorkflowScheduleList) => updateWorkflowSchedule(s.id, { is_active: !s.is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["workflow-schedules"] }),
    onError: (e) => setError(getErrorMessage(e)),
  });
  const deleteM = useMutation({
    mutationFn: (id: string) => deleteWorkflowSchedule(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["workflow-schedules"] }),
    onError: (e) => setError(getErrorMessage(e)),
  });

  const workflows = useMemo(() => (workflowsQ.data ?? []).filter(w => w.is_active), [workflowsQ.data]);
  const schedules = schedulesQ.data ?? [];

  return <>
    <Header title="Schedules" description="Manage durable workflow schedules, timezones and execution history." />
    <div className="space-y-6 p-6">
      {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><CalendarClock className="h-5 w-5" />Create schedule</CardTitle></CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <label className="text-sm"><span className="mb-1 block text-gray-500">Workflow</span><select value={workflowId} onChange={e => setWorkflowId(e.target.value)} className="h-10 w-full rounded-lg border border-gray-300 bg-white px-3"><option value="">Select workflow…</option>{workflows.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}</select></label>
            <label className="text-sm"><span className="mb-1 block text-gray-500">Cron</span><input value={cron} onChange={e => setCron(e.target.value)} placeholder="0 * * * *" className="h-10 w-full rounded-lg border border-gray-300 px-3 font-mono" /></label>
            <label className="text-sm"><span className="mb-1 block text-gray-500">Timezone</span><input value={timezone} onChange={e => setTimezone(e.target.value)} placeholder="UTC" className="h-10 w-full rounded-lg border border-gray-300 px-3" /></label>
            <div className="flex items-end"><Button onClick={() => createM.mutate()} disabled={!workflowId || !cron || !timezone || createM.isPending} className="w-full"><Plus className="mr-2 h-4 w-4" />{createM.isPending ? "Creating…" : "Create schedule"}</Button></div>
          </div>
          <p className="mt-3 text-xs text-gray-500">Cron uses five fields: minute hour day-of-month month day-of-week. Examples: <code>*/5 * * * *</code>, <code>0 9 * * 1-5</code>.</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Schedule catalog</CardTitle></CardHeader>
        <CardContent className="p-0">
          {schedulesQ.isLoading ? <div className="p-8"><Spinner /></div> : schedulesQ.error ? <div className="p-6 text-sm text-red-600">{getErrorMessage(schedulesQ.error)}</div> : schedules.length === 0 ? <div className="px-6 py-12 text-center text-sm text-gray-500">No schedules yet.</div> : <div className="overflow-auto"><table className="w-full text-left text-sm"><thead><tr className="border-b bg-gray-50 text-xs uppercase text-gray-500"><th className="px-5 py-3">Workflow</th><th className="px-5 py-3">Cron</th><th className="px-5 py-3">Timezone</th><th className="px-5 py-3">Status</th><th className="px-5 py-3">Next run</th><th className="px-5 py-3">Last run</th><th className="px-5 py-3">Actions</th></tr></thead><tbody>{schedules.map(s => <tr key={s.id} className="border-b hover:bg-gray-50"><td className="px-5 py-3 font-medium">{s.workflow_name}</td><td className="px-5 py-3 font-mono text-xs">{s.cron_expression}</td><td className="px-5 py-3">{s.timezone}</td><td className="px-5 py-3"><span className={`rounded-full px-2 py-1 text-xs ${s.is_active ? "bg-emerald-100 text-emerald-700" : "bg-gray-100 text-gray-600"}`}>{s.is_active ? "Active" : "Paused"}</span></td><td className="px-5 py-3 text-gray-600">{formatDate(s.next_run_at)}</td><td className="px-5 py-3 text-gray-600">{formatDate(s.last_run_at)}</td><td className="px-5 py-3"><div className="flex gap-3"><button className="inline-flex items-center gap-1 text-brand-600 hover:underline disabled:opacity-50" onClick={() => toggleM.mutate(s)} disabled={toggleM.isPending}>{s.is_active ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}{s.is_active ? "Pause" : "Resume"}</button><button className="inline-flex items-center gap-1 text-red-600 hover:underline disabled:opacity-50" onClick={() => { if (window.confirm("Delete this schedule?")) deleteM.mutate(s.id); }} disabled={deleteM.isPending}><Trash2 className="h-3.5 w-3.5" />Delete</button></div></td></tr>)}</tbody></table></div>}
        </CardContent>
      </Card>
    </div>
  </>;
}
