"use client";

import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { decideApproval, getErrorMessage, getWorkItemHistory, listApprovals, type WorkItemHistoryEvent } from "@/lib/api";
import { cancelWorkItem, dispatchWorkItem, listWorkItems, retryWorkItem } from "@/lib/work-items-api";
import { formatDate } from "@/lib/utils";

export default function WorkItemDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const itemQuery = useQuery({ queryKey: ["work-item", id], queryFn: () => listWorkItems({ limit: 200 }) });
  const historyQuery = useQuery({ queryKey: ["work-item-history", id], queryFn: () => getWorkItemHistory(id), enabled: Boolean(id) });
  const item = itemQuery.data?.find((candidate) => candidate.id === id);
  const runId = typeof item?.output_data?.run_id === "string" ? item.output_data.run_id : null;
  const approvalsQuery = useQuery({ queryKey: ["work-item-approvals", runId], queryFn: () => listApprovals("pending"), enabled: Boolean(runId) });
  const approval = approvalsQuery.data?.find((candidate) => candidate.run_id === runId);
  const refresh = async () => Promise.all([
    queryClient.invalidateQueries({ queryKey: ["work-item", id] }),
    queryClient.invalidateQueries({ queryKey: ["work-item-history", id] }),
    queryClient.invalidateQueries({ queryKey: ["work-item-approvals", runId] }),
    queryClient.invalidateQueries({ queryKey: ["work-items"] }),
  ]);
  const dispatchMutation = useMutation({ mutationFn: () => dispatchWorkItem(id), onSuccess: refresh });
  const cancelMutation = useMutation({ mutationFn: () => cancelWorkItem(id), onSuccess: refresh });
  const retryMutation = useMutation({ mutationFn: () => retryWorkItem(id), onSuccess: refresh });
  const decisionMutation = useMutation({
    mutationFn: ({ approvalId, decision }: { approvalId: string; decision: "approve" | "reject" }) => decideApproval(approvalId, decision),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["work-item", id] }),
        queryClient.invalidateQueries({ queryKey: ["work-item-history", id] }),
        queryClient.invalidateQueries({ queryKey: ["work-item-approvals", runId] }),
      ]);
    },
  });
  const busy = dispatchMutation.isPending || cancelMutation.isPending || retryMutation.isPending;
  const canCancel = Boolean(item && ["assigned", "running", "waiting_approval"].includes(item.status));
  const canRetry = item?.status === "failed";

  return <><Header title="Task" description="Canonical WorkItem execution detail"/><div className="p-6 space-y-4">
    {itemQuery.isLoading && <Spinner/>}
    {itemQuery.error && <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{getErrorMessage(itemQuery.error)}</div>}
    {!itemQuery.isLoading && !itemQuery.error && !item && <div className="rounded-lg border p-4 text-sm text-gray-600">Work item not found.</div>}
    {item && <>
      <div className="rounded-xl border bg-white p-5 shadow-sm space-y-4"><div className="flex items-center justify-between gap-3"><div><h2 className="font-semibold">{item.title}</h2><p className="text-xs text-gray-500">Created {formatDate(item.created_at)}</p></div><div className="flex items-center gap-2"><Badge status={item.status}/>{item.executor_type && !["succeeded", "cancelled"].includes(item.status) && <Button size="sm" onClick={() => dispatchMutation.mutate()} loading={dispatchMutation.isPending} disabled={busy}>Dispatch</Button>}{canCancel && <Button size="sm" variant="danger" onClick={() => cancelMutation.mutate()} loading={cancelMutation.isPending} disabled={busy}>Cancel</Button>}{canRetry && <Button size="sm" onClick={() => retryMutation.mutate()} loading={retryMutation.isPending} disabled={busy}>Retry</Button>}</div></div><p className="text-sm text-gray-700">{item.description ?? String(item.input_data?.message ?? "Work item")}</p><dl className="grid gap-3 text-sm sm:grid-cols-2"><div><dt className="text-gray-500">Priority</dt><dd>{item.priority}</dd></div><div><dt className="text-gray-500">Executor</dt><dd>{item.executor_type ?? "Unassigned"}</dd></div><div><dt className="text-gray-500">Run</dt><dd>{runId ?? "Not started"}</dd></div></dl>{dispatchMutation.error && <p className="text-sm text-red-700">{getErrorMessage(dispatchMutation.error)}</p>}{cancelMutation.error && <p className="text-sm text-red-700">{getErrorMessage(cancelMutation.error)}</p>}{retryMutation.error && <p className="text-sm text-red-700">{getErrorMessage(retryMutation.error)}</p>}</div>
      {runId && <section className="rounded-xl border bg-white p-5 shadow-sm"><div className="mb-4"><h3 className="font-semibold">Approval</h3><p className="text-xs text-gray-500">Approval requests are scoped to the WorkItem&apos;s correlated Run.</p></div>
        {approvalsQuery.isLoading && <Spinner/>}
        {approvalsQuery.error && <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{getErrorMessage(approvalsQuery.error)}</div>}
        {!approvalsQuery.isLoading && !approvalsQuery.error && !approval && <p className="text-sm text-gray-500">No pending approval for this execution.</p>}
        {approval && <div className="space-y-3"><div className="text-sm"><span className="font-medium">{approval.tool_name}</span><span className="ml-2 text-gray-500">{approval.status}</span></div><div className="flex gap-2"><Button size="sm" onClick={() => decisionMutation.mutate({ approvalId: approval.id, decision: "approve" })} loading={decisionMutation.isPending}>Approve</Button><Button size="sm" variant="danger" onClick={() => decisionMutation.mutate({ approvalId: approval.id, decision: "reject" })} loading={decisionMutation.isPending}>Reject</Button></div>{decisionMutation.error && <p className="text-sm text-red-700">{getErrorMessage(decisionMutation.error)}</p>}</div>}
      </section>}
      <section className="rounded-xl border bg-white p-5 shadow-sm"><div className="mb-4"><h3 className="font-semibold">Execution result</h3><p className="text-xs text-gray-500">Current status and output returned by the canonical execution service.</p></div>
        <div className="grid gap-3 text-sm sm:grid-cols-2"><div><dt className="text-gray-500">Status</dt><dd className="font-medium">{item.status}</dd></div><div><dt className="text-gray-500">Executor</dt><dd>{item.executor_type ?? "Unassigned"}</dd></div></div>
        {item.output_data && Object.keys(item.output_data).length > 0 ? <pre className="mt-4 overflow-x-auto rounded-lg bg-gray-50 p-3 text-xs">{JSON.stringify(item.output_data, null, 2)}</pre> : <p className="mt-4 text-sm text-gray-500">No execution output has been recorded yet.</p>}
      </section>
      <section className="rounded-xl border bg-white p-5 shadow-sm"><div className="mb-4"><h3 className="font-semibold">Execution history</h3><p className="text-xs text-gray-500">Canonical audit events for this WorkItem.</p></div>
        {historyQuery.isLoading && <Spinner/>}
        {historyQuery.error && <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{getErrorMessage(historyQuery.error)}</div>}
        {!historyQuery.isLoading && !historyQuery.error && !historyQuery.data?.length && <p className="text-sm text-gray-500">No execution history yet.</p>}
        <div className="space-y-3">{historyQuery.data?.map((event: WorkItemHistoryEvent) => <div key={event.id} className="rounded-lg border p-3"><div className="flex flex-wrap items-center justify-between gap-2"><span className="text-sm font-medium">{event.action}</span><span className="text-xs text-gray-500">{formatDate(event.created_at)}</span></div><p className="mt-1 text-xs text-gray-500">{event.actor_type} · {event.status}{event.request_id ? ` · ${event.request_id}` : ""}</p></div>)}</div>
      </section>
    </>}
  </div></>;
}