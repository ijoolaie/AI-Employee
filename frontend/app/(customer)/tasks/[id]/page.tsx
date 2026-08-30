"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage } from "@/lib/api";
import { listWorkItems } from "@/lib/work-items-api";
import { formatDate } from "@/lib/utils";

export default function WorkItemDetailPage() {
  const { id } = useParams<{ id: string }>();
  const q = useQuery({ queryKey: ["work-items", id], queryFn: () => listWorkItems({ limit: 200 }) });
  const item = q.data?.find((candidate) => candidate.id === id);
  return <><Header title="Task" description="Canonical WorkItem execution detail"/><div className="p-6 space-y-4">
    {q.isLoading && <Spinner/>}
    {q.error && <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{getErrorMessage(q.error)}</div>}
    {!q.isLoading && !q.error && !item && <div className="rounded-lg border p-4 text-sm text-gray-600">Work item not found.</div>}
    {item && <div className="rounded-xl border bg-white p-5 shadow-sm space-y-4"><div className="flex items-center justify-between gap-3"><div><h2 className="font-semibold">{item.title}</h2><p className="text-xs text-gray-500">Created {formatDate(item.created_at)}</p></div><Badge status={item.status}/></div><p className="text-sm text-gray-700">{item.description ?? String(item.input_data?.message ?? "Work item")}</p><dl className="grid gap-3 text-sm sm:grid-cols-2"><div><dt className="text-gray-500">Priority</dt><dd>{item.priority}</dd></div><div><dt className="text-gray-500">Executor</dt><dd>{item.executor_type ?? "Unassigned"}</dd></div></dl></div>}
  </div></>;
}
