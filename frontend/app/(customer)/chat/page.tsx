"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { createRun, getErrorMessage, getRun, listEmployees } from "@/lib/api";
import type { Run } from "@/types";
import { Bot, Paperclip, Play, RefreshCw, Square } from "lucide-react";

export default function ChatPage() {
  const employees = useQuery({ queryKey: ["employees"], queryFn: listEmployees });
  const [employeeId, setEmployeeId] = useState("");
  const [message, setMessage] = useState("");
  const [run, setRun] = useState<Run | null>(null);
  const selected = useMemo(() => employees.data?.find((e) => e.id === employeeId), [employees.data, employeeId]);

  const execute = useMutation({
    mutationFn: () => createRun({ employee_id: employeeId, input_data: { message: message.trim() } }),
    onSuccess: (data) => { setRun(data); setMessage(""); },
  });

  useEffect(() => {
    if (!run || !["pending", "queued", "running"].includes(run.status)) return;
    const timer = window.setInterval(async () => {
      try { setRun(await getRun(run.id)); } catch { /* interceptor handles auth */ }
    }, 1500);
    return () => window.clearInterval(timer);
  }, [run]);

  const busy = !!run && ["pending", "queued", "running"].includes(run.status);
  return <>
    <Header title="AI Employee Chat" description="Run an AI employee with memory, planning and approved tools." />
    <div className="grid gap-6 p-6 xl:grid-cols-[280px_minmax(0,1fr)_320px]">
      <Card className="h-fit"><CardHeader><CardTitle>Employee</CardTitle></CardHeader><CardContent className="space-y-4">
        {employees.isLoading ? <Spinner /> : <>
          <select value={employeeId} onChange={(e) => setEmployeeId(e.target.value)} className="h-10 w-full rounded-lg border border-gray-300 bg-white px-3 text-sm">
            <option value="">Select an employee…</option>{(employees.data ?? []).map((e) => <option key={e.id} value={e.id}>{e.name}</option>)}
          </select>
          {selected && <div className="rounded-xl bg-gray-50 p-3"><div className="flex items-center gap-2"><Bot className="h-4 w-4 text-brand-600" /><span className="font-medium">{selected.name}</span></div><p className="mt-1 text-xs text-gray-500">{selected.kind} · {selected.is_active ? "Active" : "Inactive"}</p></div>}
          <p className="text-xs leading-5 text-gray-500">The runtime decides when to retrieve memory, create a plan and request tools. Side-effecting tools remain behind the approval boundary.</p>
        </>}
      </CardContent></Card>

      <Card className="flex min-h-[620px] flex-col"><CardHeader><div><CardTitle>Conversation</CardTitle><p className="mt-1 text-xs text-gray-500">LM Studio is used through the existing AI Gateway.</p></div>{run && <Badge status={run.status} />}</CardHeader>
        <CardContent className="flex flex-1 flex-col">
          <div className="flex-1 rounded-xl border border-dashed border-gray-200 bg-gray-50 p-5">
            {!run && <div className="flex h-full min-h-[360px] flex-col items-center justify-center text-center"><Bot className="h-10 w-10 text-brand-500" /><h2 className="mt-4 font-semibold text-gray-900">What should your employee do?</h2><p className="mt-2 max-w-md text-sm text-gray-500">Ask for a task. The execution result, tool activity and trace become available as the run progresses.</p></div>}
            {run && <div className="space-y-4"><div className="rounded-xl bg-white p-4 shadow-sm"><p className="text-xs font-medium uppercase tracking-wide text-gray-400">Run</p><p className="mt-1 font-mono text-xs text-gray-600">{run.id}</p><div className="mt-3 rounded-lg bg-gray-50 p-3 text-sm">{String(run.input_data?.message ?? "")}</div></div><div className="rounded-xl bg-brand-50 p-4"><p className="text-xs font-medium uppercase tracking-wide text-brand-700">Employee output</p><pre className="mt-2 whitespace-pre-wrap font-sans text-sm text-gray-800">{run.output_data ? JSON.stringify(run.output_data, null, 2) : busy ? "Working… retrieving memory, planning and executing…" : run.error ? JSON.stringify(run.error, null, 2) : "No output returned."}</pre></div></div>}
          </div>
          <div className="mt-4 flex items-end gap-2"><button title="Attach file" className="mb-0.5 rounded-lg p-2 text-gray-400 hover:bg-gray-100"><Paperclip className="h-5 w-5" /></button><textarea value={message} onChange={(e) => setMessage(e.target.value)} disabled={busy} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); if (employeeId && message.trim()) execute.mutate(); } }} placeholder="Describe the task…" rows={3} className="min-h-20 flex-1 resize-none rounded-xl border border-gray-300 p-3 text-sm outline-none focus:border-brand-500" /><Button disabled={!employeeId || !message.trim() || execute.isPending || busy} onClick={() => execute.mutate()}><Play className="h-4 w-4" />{busy ? "Running" : "Run"}</Button></div>
          {execute.error && <p className="mt-2 text-sm text-red-600">{getErrorMessage(execute.error)}</p>}
        </CardContent>
      </Card>

      <Card className="h-fit"><CardHeader><CardTitle>Run controls</CardTitle></CardHeader><CardContent className="space-y-3"><div className="flex items-center justify-between text-sm"><span className="text-gray-500">Status</span>{run ? <Badge status={run.status} /> : <span className="text-gray-400">No run</span>}</div><div className="flex items-center justify-between text-sm"><span className="text-gray-500">Tokens</span><span>{run?.total_tokens?.toLocaleString() ?? "—"}</span></div><div className="flex items-center justify-between text-sm"><span className="text-gray-500">Cost</span><span>${run?.total_cost_usd?.toFixed(4) ?? "0.0000"}</span></div>{run && <><a href={`/runs/${run.id}`} className="block rounded-lg border px-3 py-2 text-center text-sm font-medium hover:bg-gray-50">Open run details</a><a href={`/traces?run=${run.id}`} className="block rounded-lg border px-3 py-2 text-center text-sm font-medium hover:bg-gray-50">Open trace</a></>}<button onClick={() => setRun(null)} disabled={busy} className="flex w-full items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-40"><RefreshCw className="h-4 w-4" />New task</button><p className="text-xs leading-5 text-gray-400"><Square className="mr-1 inline h-3 w-3" />Cancellation is exposed for workflow runs; direct AI runs use the existing run lifecycle.</p></CardContent></Card>
    </div>
  </>;
}
