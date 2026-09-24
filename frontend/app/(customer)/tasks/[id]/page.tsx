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
import { useI18n } from "@/lib/i18n/provider";

function isPermissionError(error: unknown) {
  const message = getErrorMessage(error).toLowerCase();
  return message.includes("permission") || message.includes("403");
}

export default function WorkItemDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useI18n();
  const m = t.tasks;
  const statusLabel = (status: string) => m.statusLabels[status as keyof typeof m.statusLabels] ?? status;
  const executorLabel = (executor: string | null) => executor ? (m.executorLabels[executor as keyof typeof m.executorLabels] ?? executor) : m.unassigned;
  const historyActionLabel = (action: string) => m.historyActionLabels[action as keyof typeof m.historyActionLabels] ?? action;
  const queryClient = useQueryClient();

  const itemQuery = useQuery({ queryKey: ["work-item", id], queryFn: () => listWorkItems({ limit: 200 }), enabled: Boolean(id) });
  const historyQuery = useQuery({ queryKey: ["work-item-history", id], queryFn: () => getWorkItemHistory(id), enabled: Boolean(id) });
  const item = itemQuery.data?.find((candidate) => candidate.id === id);
  const runId = typeof item?.output_data?.run_id === "string" ? item.output_data.run_id : null;
  const approvalsQuery = useQuery({ queryKey: ["work-item-approvals", runId], queryFn: () => listApprovals("pending"), enabled: Boolean(runId) });
  const approval = approvalsQuery.data?.find((candidate) => candidate.run_id === runId);

  const refresh = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["work-item", id] }),
      queryClient.invalidateQueries({ queryKey: ["work-item-history", id] }),
      queryClient.invalidateQueries({ queryKey: ["work-item-approvals", runId] }),
      queryClient.invalidateQueries({ queryKey: ["work-items"] }),
    ]);
  };

  const dispatchMutation = useMutation({ mutationFn: () => dispatchWorkItem(id), onSuccess: refresh });
  const cancelMutation = useMutation({ mutationFn: () => cancelWorkItem(id), onSuccess: refresh });
  const retryMutation = useMutation({ mutationFn: () => retryWorkItem(id), onSuccess: refresh });
  const decisionMutation = useMutation({
    mutationFn: ({ approvalId, decision }: { approvalId: string; decision: "approve" | "reject" }) => decideApproval(approvalId, decision),
    onSuccess: refresh,
  });

  const busy = dispatchMutation.isPending || cancelMutation.isPending || retryMutation.isPending;
  const canCancel = Boolean(item && ["assigned", "running", "waiting_approval"].includes(item.status));
  const canRetry = item?.status === "failed";
  const actionError = dispatchMutation.error ?? cancelMutation.error ?? retryMutation.error ?? decisionMutation.error;

  return <>
    <Header title={m.task} description={m.detailDescription} />
    <div className="space-y-4 p-6">
      {itemQuery.isLoading && <div className="flex justify-center py-12"><Spinner /></div>}
      {itemQuery.error && (
        <div className="space-y-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <p>{isPermissionError(itemQuery.error) ? m.permissionDenied : m.error}</p>
          <Button variant="secondary" onClick={() => itemQuery.refetch()}>{m.retry}</Button>
        </div>
      )}
      {!itemQuery.isLoading && !itemQuery.error && !item && (
        <div className="rounded-lg border p-4 text-sm text-gray-600">{m.notFound}</div>
      )}

      {item && <>
        {actionError && (
          <div className="space-y-2 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            <p>{isPermissionError(actionError) ? m.permissionDenied : getErrorMessage(actionError) || m.actionFailed}</p>
          </div>
        )}

        <section className="space-y-4 rounded-xl border bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="font-semibold">{item.title}</h2>
              <p className="text-xs text-gray-500">{m.created} {formatDate(item.created_at)}</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge status={item.status}>{statusLabel(item.status)}</Badge>
              {item.executor_type && !["succeeded", "cancelled"].includes(item.status) && (
                <Button size="sm" onClick={() => dispatchMutation.mutate()} loading={dispatchMutation.isPending} disabled={busy}>{m.dispatch}</Button>
              )}
              {canCancel && <Button size="sm" variant="danger" onClick={() => cancelMutation.mutate()} loading={cancelMutation.isPending} disabled={busy}>{m.cancel}</Button>}
              {canRetry && <Button size="sm" onClick={() => retryMutation.mutate()} loading={retryMutation.isPending} disabled={busy}>{m.retryAction}</Button>}
            </div>
          </div>
          <p className="text-sm text-gray-700">{item.description ?? String(item.input_data?.message ?? m.workItem)}</p>
          <dl className="grid gap-3 text-sm sm:grid-cols-2">
            <div><dt className="text-gray-500">{m.priority}</dt><dd>{item.priority}</dd></div>
            <div><dt className="text-gray-500">{m.executor}</dt><dd>{executorLabel(item.executor_type)}</dd></div>
            <div><dt className="text-gray-500">{m.run}</dt><dd>{runId ?? m.notStarted}</dd></div>
            <div><dt className="text-gray-500">{m.status}</dt><dd>{statusLabel(item.status)}</dd></div>
          </dl>
        </section>

        {runId && <section className="space-y-4 rounded-xl border bg-white p-5 shadow-sm">
          <div>
            <h3 className="font-semibold">{m.approval}</h3>
            <p className="text-xs text-gray-500">{m.approvalDescription}</p>
          </div>
          {approvalsQuery.isLoading && <Spinner />}
          {approvalsQuery.error && (
            <div className="space-y-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              <p>{isPermissionError(approvalsQuery.error) ? m.permissionDenied : getErrorMessage(approvalsQuery.error)}</p>
              <Button variant="secondary" onClick={() => approvalsQuery.refetch()}>{m.retry}</Button>
            </div>
          )}
          {!approvalsQuery.isLoading && !approvalsQuery.error && !approval && <p className="text-sm text-gray-500">{m.noPendingApproval}</p>}
          {approval && <div className="space-y-3">
            <div className="text-sm"><span className="font-medium">{approval.tool_name}</span><span className="ms-2 text-gray-500">{statusLabel(approval.status)}</span></div>
            <div className="flex flex-wrap gap-2">
              <Button size="sm" onClick={() => decisionMutation.mutate({ approvalId: approval.id, decision: "approve" })} loading={decisionMutation.isPending}>{m.approve}</Button>
              <Button size="sm" variant="danger" onClick={() => decisionMutation.mutate({ approvalId: approval.id, decision: "reject" })} loading={decisionMutation.isPending}>{m.reject}</Button>
            </div>
          </div>}
        </section>}

        <section className="space-y-4 rounded-xl border bg-white p-5 shadow-sm">
          <div><h3 className="font-semibold">{m.executionResult}</h3><p className="text-xs text-gray-500">{m.executionResultDescription}</p></div>
          <div className="grid gap-3 text-sm sm:grid-cols-2">
            <div><dt className="text-gray-500">{m.status}</dt><dd className="font-medium">{statusLabel(item.status)}</dd></div>
            <div><dt className="text-gray-500">{m.executor}</dt><dd>{executorLabel(item.executor_type)}</dd></div>
          </div>
          {item.output_data && Object.keys(item.output_data).length > 0 ? <pre className="mt-4 overflow-x-auto rounded-lg bg-gray-50 p-3 text-xs">{JSON.stringify(item.output_data, null, 2)}</pre> : <p className="text-sm text-gray-500">{m.noOutput}</p>}
        </section>

        <section className="space-y-4 rounded-xl border bg-white p-5 shadow-sm">
          <div><h3 className="font-semibold">{m.executionHistory}</h3><p className="text-xs text-gray-500">{m.executionHistoryDescription}</p></div>
          {historyQuery.isLoading && <Spinner />}
          {historyQuery.error && (
            <div className="space-y-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              <p>{isPermissionError(historyQuery.error) ? m.permissionDenied : getErrorMessage(historyQuery.error)}</p>
              <Button variant="secondary" onClick={() => historyQuery.refetch()}>{m.retry}</Button>
            </div>
          )}
          {!historyQuery.isLoading && !historyQuery.error && !historyQuery.data?.length && <p className="text-sm text-gray-500">{m.noHistory}</p>}
          <div className="space-y-3">
            {historyQuery.data?.map((event: WorkItemHistoryEvent) => (
              <div key={event.id} className="rounded-lg border p-3">
                <div className="flex flex-wrap items-center justify-between gap-2"><span className="text-sm font-medium">{event.action}</span><span className="text-xs text-gray-500">{formatDate(event.created_at)}</span></div>
                <p className="mt-1 text-xs text-gray-500">{event.actor_type} · {statusLabel(event.status)}{event.request_id ? ` · ${event.request_id}` : ""}</p>
              </div>
            ))}
          </div>
        </section>
      </>}
    </div>
  </>;
}
