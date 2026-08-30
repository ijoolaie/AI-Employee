"use client";

import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage, listWorkItems } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { CheckSquare } from "lucide-react";

const active = ["ready", "assigned", "running", "waiting_approval"];

export default function TasksPage() {
  const q = useQuery({ queryKey: ["work-items"], queryFn: () => listWorkItems() });
  const tasks = [...(q.data ?? [])].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
  return <><Header title="Tasks" description="Operational task queue backed by WorkItems" /><div className="p-6 space-y-4">
    {q.isLoading && <Spinner/>}
    {q.error && <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{getErrorMessage(q.error)}</div>}
    {!q.isLoading && !q.error && !tasks.length && <EmptyState icon={CheckSquare} title="No tasks yet" description="Start a task from AI Chat or an employee."/>}
    {tasks.map(t => <div key={t.id} className="rounded-xl border bg-white p-4 shadow-sm"><div className="flex flex-wrap items-center justify-between gap-3"><div><span className="font-medium text-brand-700">{t.title}</span><p className="mt-1 text-xs text-gray-500">{formatDate(t.created_at)} · {t.id.slice(0,12)}…</p></div><Badge status={t.status}/></div><p className="mt-3 line-clamp-2 text-sm text-gray-600">{String(t.input_data?.message ?? t.description ?? "Work item")}</p><div className="mt-3 flex gap-4 text-xs text-gray-500"><span>Priority {t.priority}</span><span>{active.includes(t.status) ? "In progress" : "Completed lifecycle"}</span></div></div>)}
  </div></>;
}
