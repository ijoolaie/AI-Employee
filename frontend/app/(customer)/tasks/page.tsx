"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage, listRuns } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { CheckSquare } from "lucide-react";

const active = ["pending", "queued", "running", "waiting"];

export default function TasksPage() {
  const q = useQuery({ queryKey: ["tasks"], queryFn: () => listRuns() });
  const tasks = [...(q.data ?? [])].sort((a,b) => new Date(b.created_at).getTime()-new Date(a.created_at).getTime());
  return <><Header title="Tasks" description="Operational task queue backed by AI employee runs" /><div className="p-6 space-y-4">
    {q.isLoading && <Spinner/>}
    {q.error && <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{getErrorMessage(q.error)}</div>}
    {!q.isLoading && !q.error && !tasks.length && <EmptyState icon={CheckSquare} title="No tasks yet" description="Start a task from AI Chat or an employee."/>}
    {tasks.map(t => <div key={t.id} className="rounded-xl border bg-white p-4 shadow-sm"><div className="flex flex-wrap items-center justify-between gap-3"><div><Link href={`/runs/${t.id}`} className="font-medium text-brand-700 hover:underline">{t.employee_name || t.employee_slug || "AI Employee"} task</Link><p className="mt-1 text-xs text-gray-500">{formatDate(t.created_at)} · {t.id.slice(0,12)}…</p></div><Badge status={t.status}/></div><p className="mt-3 line-clamp-2 text-sm text-gray-600">{String(t.input_data?.message ?? "Task execution")}</p><div className="mt-3 flex gap-4 text-xs text-gray-500"><span>{t.total_tokens.toLocaleString()} tokens</span><span>{active.includes(t.status) ? "In progress" : "Completed lifecycle"}</span></div></div>)}
  </div></>;
}
