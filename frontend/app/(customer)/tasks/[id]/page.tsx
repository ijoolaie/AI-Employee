"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage, getWorkItemHistory, type WorkItemHistoryEvent } from "@/lib/api";
import { listWorkItems } from "@/lib/work-items-api";
import { formatDate } from "@/lib/utils";

export default function WorkItemDetailPage() {
  const { id } = useParams<{ id: string }>();
  const itemQuery = useQuery({ queryKey: ["work-item", id], queryFn: () => listWorkItems({ limit: 200 }) });
  const historyQuery = useQuery({ queryKey: ["work-item-history", id], queryFn: () => getWorkItemHistory(id), enabled: Boolean(id) });
  const item = itemQuery.data?.find((candidate) => candidate.id === id);

  return <><Header title="Task" description="Canonical WorkItem execution detail"/><div className="p-6 space-y-4">
    {itemQuery.isLoading && <Spinner/>}
    {itemQuery.error && <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{getErrorMessage(itemQuery.error)}</div>}
    {!itemQuery.isLoading && !itemQuery.error && !item && <div className="rounded-lg border p-4 text-sm text-gray-600">Work item not found.</div>}
    {item && <>
      <div className="rounded-xl border bg-white p-5 shadow-sm space-y-4"><div className="flex items-center justify-between gap-3"><div><h2 className="font-semibold">{item.title}</h2><p className="text-xs text-gray-500">Created {formatDate(item.created_at)}</p></div><Badge status={item.status}/></div><p className="text-sm text-gray-700">{item.description ?? String(item.input_data?.message ?? "Work item")}</p><dl className="grid gap-3 text-sm sm:grid-cols-2"><div><dt className="text-gray-500">Priority</dt><dd>{item.priority}</dd></div><div><dt className="text-gray-500">Executor</dt><dd>{item.executor_type ?? "Unassigned"}</dd></div></dl></div>
      <section className="rounded-xl border bg-white p-5 shadow-sm"><div className="mb-4"><h3 className="font-semibold">Execution history</h3><p className="text-xs text-gray-500">Canonical audit events for this WorkItem.</p></div>
        {historyQuery.isLoading && <Spinner/>}
        {historyQuery.error && <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{getErrorMessage(historyQuery.error)}</div>}
        {!historyQuery.isLoading && !historyQuery.error && !historyQuery.data?.length && <p className="text-sm text-gray-500">No execution history yet.</p>}
        <div className="space-y-3">{historyQuery.data?.map((event: WorkItemHistoryEvent) => <div key={event.id} className="rounded-lg border p-3"><div className="flex flex-wrap items-center justify-between gap-2"><span className="text-sm font-medium">{event.action}</span><span className="text-xs text-gray-500">{formatDate(event.created_at)}</span></div><p className="mt-1 text-xs text-gray-500">{event.actor_type} · {event.status}{event.request_id ? ` · ${event.request_id}` : ""}</p></div>)}</div>
      </section>
    </>}
  </div></>;
}
