"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarClock, Pause, Play, Plus } from "lucide-react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { EmptyState } from "@/components/ui/empty-state";
import { getErrorMessage, listWorkflows, listWorkflowSchedules, createWorkflowSchedule, updateWorkflowSchedule } from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";
import type { WorkflowScheduleList } from "@/types";

function formatDate(value: string | null, locale: string) {
  return value ? new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "—";
}

function isPermissionError(error: unknown) {
  const message = getErrorMessage(error).toLowerCase();
  return message.includes("permission") || message.includes("403") || message.includes("forbidden");
}

export default function SchedulesPage() {
  const { t, locale } = useI18n();
  const m = t.schedules;
  const qc = useQueryClient();
  const schedulesQ = useQuery({ queryKey: ["workflow-schedules"], queryFn: listWorkflowSchedules, refetchInterval: 10000 });
  const workflowsQ = useQuery({ queryKey: ["workflows"], queryFn: listWorkflows });
  const [workflowId, setWorkflowId] = useState("");
  const [cron, setCron] = useState("0 * * * *");
  const [timezone, setTimezone] = useState("UTC");

  const createM = useMutation({
    mutationFn: () => createWorkflowSchedule(workflowId, { cron_expression: cron.trim(), timezone: timezone.trim() }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["workflow-schedules"] });
      setWorkflowId("");
    },
  });
  const toggleM = useMutation({
    mutationFn: (s: WorkflowScheduleList) => updateWorkflowSchedule(s.id, { is_active: !s.is_active }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["workflow-schedules"] }),
  });
  const workflows = useMemo(() => (workflowsQ.data ?? []).filter((w) => w.is_active), [workflowsQ.data]);
  const schedules = schedulesQ.data ?? [];
  const actionError = createM.error ?? toggleM.error;
  const busy = createM.isPending || toggleM.isPending;

  const retrySchedules = () => { void schedulesQ.refetch(); };
  const retryWorkflows = () => { void workflowsQ.refetch(); };

  return (
    <>
      <Header title={m.title} description={m.description} />
      <div className="space-y-6 p-6">
        {actionError && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{isPermissionError(actionError) ? m.permissionDenied : getErrorMessage(actionError)}</div>}

        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><CalendarClock className="h-5 w-5" />{m.createTitle}</CardTitle></CardHeader>
          <CardContent>
            {workflowsQ.isLoading ? <Spinner /> : workflowsQ.isError ? (
              <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm">
                <p className="text-red-700">{isPermissionError(workflowsQ.error) ? m.permissionDenied : m.workflowError}</p>
                <Button type="button" variant="outline" className="mt-3" onClick={retryWorkflows}>{m.retry}</Button>
              </div>
            ) : workflows.length === 0 ? (
              <EmptyState title={m.noWorkflows} description={m.noWorkflowsDescription} />
            ) : (
              <div className="grid gap-4 md:grid-cols-4">
                <label className="text-sm"><span className="mb-1 block text-gray-500">{m.workflow}</span><select aria-label={m.workflow} value={workflowId} onChange={(e) => setWorkflowId(e.target.value)} className="h-10 w-full rounded-lg border border-gray-300 bg-white px-3"><option value="">{m.selectWorkflow}</option>{workflows.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}</select></label>
                <label className="text-sm"><span className="mb-1 block text-gray-500">{m.cron}</span><input aria-label={m.cron} value={cron} onChange={(e) => setCron(e.target.value)} placeholder="0 * * * *" className="h-10 w-full rounded-lg border border-gray-300 px-3 font-mono" /></label>
                <label className="text-sm"><span className="mb-1 block text-gray-500">{m.timezone}</span><input aria-label={m.timezone} value={timezone} onChange={(e) => setTimezone(e.target.value)} placeholder="UTC" className="h-10 w-full rounded-lg border border-gray-300 px-3" /></label>
                <div className="flex items-end"><Button onClick={() => createM.mutate()} disabled={!workflowId || !cron.trim() || !timezone.trim() || busy} className="w-full"><Plus className="me-2 h-4 w-4" />{createM.isPending ? m.creating : m.create}</Button></div>
              </div>
            )}
            <p className="mt-3 text-xs text-gray-500">{m.cronHelp} <code>*/5 * * * *</code>, <code>0 9 * * 1-5</code>.</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>{m.catalog}</CardTitle></CardHeader>
          <CardContent className="p-0">
            {schedulesQ.isLoading ? <div className="p-8"><Spinner /></div> : schedulesQ.isError ? (
              <div role="alert" className="p-6 text-sm">
                <p className={isPermissionError(schedulesQ.error) ? "text-amber-700" : "text-red-600"}>{isPermissionError(schedulesQ.error) ? m.permissionDenied : m.error}</p>
                <Button type="button" variant="outline" className="mt-3" onClick={retrySchedules}>{m.retry}</Button>
              </div>
            ) : schedules.length === 0 ? (
              <EmptyState title={m.emptyTitle} description={m.emptyDescription} />
            ) : (
              <div className="overflow-auto">
                <table className="w-full text-start text-sm">
                  <thead><tr className="border-b bg-gray-50 text-xs uppercase text-gray-500"><th className="px-5 py-3 text-start">{m.workflow}</th><th className="px-5 py-3 text-start">{m.cron}</th><th className="px-5 py-3 text-start">{m.timezone}</th><th className="px-5 py-3 text-start">{m.status}</th><th className="px-5 py-3 text-start">{m.nextRun}</th><th className="px-5 py-3 text-start">{m.lastRun}</th><th className="px-5 py-3 text-start">{m.actions}</th></tr></thead>
                  <tbody>{schedules.map((s) => <tr key={s.id} className="border-b hover:bg-gray-50">
                    <td className="px-5 py-3 font-medium">{s.workflow_name}</td><td className="px-5 py-3 font-mono text-xs">{s.cron_expression}</td><td className="px-5 py-3">{s.timezone}</td>
                    <td className="px-5 py-3"><span className={`rounded-full px-2 py-1 text-xs ${s.is_active ? "bg-emerald-100 text-emerald-700" : "bg-gray-100 text-gray-600"}`}>{s.is_active ? m.active : m.paused}</span></td>
                    <td className="px-5 py-3 text-gray-600">{formatDate(s.next_run_at, locale)}</td><td className="px-5 py-3 text-gray-600">{formatDate(s.last_run_at, locale)}</td>
                    <td className="px-5 py-3"><div className="flex flex-wrap gap-3">
                      <button type="button" className="inline-flex items-center gap-1 text-brand-600 hover:underline disabled:opacity-50" onClick={() => toggleM.mutate(s)} disabled={busy}><span aria-hidden="true">{s.is_active ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}</span>{s.is_active ? m.pause : m.resume}</button>
                    </div></td>
                  </tr>)}</tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
