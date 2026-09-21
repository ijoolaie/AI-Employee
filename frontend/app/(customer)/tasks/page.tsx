"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { Button } from "@/components/ui/button";
import { getErrorMessage } from "@/lib/api";
import { listWorkItems } from "@/lib/work-items-api";
import { formatDate } from "@/lib/utils";
import { useI18n } from "@/lib/i18n/provider";
import { CheckSquare } from "lucide-react";

const active = ["ready", "assigned", "running", "waiting_approval"];

function isPermissionError(error: unknown) {
  const message = getErrorMessage(error).toLowerCase();
  return message.includes("permission") || message.includes("403");
}

export default function TasksPage() {
  const { t } = useI18n();
  const m = t.tasks;
  const q = useQuery({ queryKey: ["work-items"], queryFn: () => listWorkItems() });
  const tasks = [...(q.data ?? [])].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

  return <>
    <Header title={m.title} description={m.description} />
    <div className="space-y-4 p-6">
      {q.isLoading && <div className="flex justify-center py-12"><Spinner /></div>}
      {q.error && (
        <div className="space-y-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <p>{isPermissionError(q.error) ? m.permissionDenied : m.error}</p>
          <Button variant="secondary" onClick={() => q.refetch()}>{m.retry}</Button>
        </div>
      )}
      {!q.isLoading && !q.error && !tasks.length && (
        <EmptyState icon={CheckSquare} title={m.noTasks} description={m.noTasksDescription} />
      )}
      {!q.isLoading && !q.error && tasks.map((task) => (
        <Link href={`/tasks/${task.id}`} key={task.id} className="block rounded-xl border bg-white p-4 shadow-sm transition hover:border-brand-300 hover:shadow">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <span className="font-medium text-brand-700">{task.title}</span>
              <p className="mt-1 text-xs text-gray-500">{formatDate(task.created_at)} · {task.id.slice(0, 12)}…</p>
            </div>
            <Badge status={task.status} />
          </div>
          <p className="mt-3 line-clamp-2 text-sm text-gray-600">{String(task.input_data?.message ?? task.description ?? "Work item")}</p>
          <div className="mt-3 flex flex-wrap gap-4 text-xs text-gray-500">
            <span>{m.priority} {task.priority}</span>
            <span>{active.includes(task.status) ? m.inProgress : m.completedLifecycle}</span>
          </div>
        </Link>
      ))}
    </div>
  </>;
}
