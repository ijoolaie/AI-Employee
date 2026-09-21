"use client";

import { useState } from "react";
import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import {
  decideApproval,
  decideWorkflowApproval,
  getErrorMessage,
  listApprovals,
  listWorkflowApprovals,
} from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { useI18n } from "@/lib/i18n/provider";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

function isPermissionError(error: unknown) {
  const message = getErrorMessage(error).toLowerCase();
  return message.includes("permission") || message.includes("403") || message.includes("forbidden");
}

export default function ApprovalsPage() {
  const { t } = useI18n();
  const m = t.approvals;
  const qc = useQueryClient();
  const [reason, setReason] = useState<Record<string, string>>({});

  const toolQ = useQuery({
    queryKey: ["approvals", "tool", "pending"],
    queryFn: () => listApprovals("pending"),
    refetchInterval: 3000,
  });
  const workflowQ = useQuery({
    queryKey: ["approvals", "workflow", "pending"],
    queryFn: () => listWorkflowApprovals("pending"),
    refetchInterval: 3000,
  });

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["approvals"] });
    qc.invalidateQueries({ queryKey: ["runs"] });
    qc.invalidateQueries({ queryKey: ["workflow-runs"] });
    qc.invalidateQueries({ queryKey: ["workflows"] });
  };

  const toolDecision = useMutation({
    mutationFn: ({ id, decision }: { id: string; decision: "approve" | "reject" }) =>
      decideApproval(id, decision, reason[id] || undefined),
    onSuccess: (_, variables) => {
      setReason((current) => ({ ...current, [variables.id]: "" }));
      invalidate();
    },
  });

  const workflowDecision = useMutation({
    mutationFn: ({ id, decision }: { id: string; decision: "approve" | "reject" }) =>
      decideWorkflowApproval(id, decision, reason[id] || undefined),
    onSuccess: (_, variables) => {
      setReason((current) => ({ ...current, [variables.id]: "" }));
      invalidate();
    },
  });

  const actionError = toolDecision.error ?? workflowDecision.error;
  const busy = toolDecision.isPending || workflowDecision.isPending;

  const retryAll = () => {
    void toolQ.refetch();
    void workflowQ.refetch();
  };

  return (
    <>
      <Header title={m.title} description={m.description} />
      <div className="space-y-6 p-6">
        {actionError && (
          <div role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
            {getErrorMessage(actionError)}
          </div>
        )}

        {toolQ.isError || workflowQ.isError ? (
          <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4">
            <p className="text-sm text-red-700">
              {(isPermissionError(toolQ.error) || isPermissionError(workflowQ.error))
                ? m.permissionDenied
                : m.error}
            </p>
            <Button type="button" variant="outline" className="mt-3" onClick={retryAll}>
              {m.retry}
            </Button>
          </div>
        ) : null}

        <section className="space-y-3">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">{m.workflowTitle}</h2>
            <p className="text-sm text-gray-500">{m.workflowDescription}</p>
          </div>
          {workflowQ.isLoading ? <Spinner /> : !workflowQ.isError && !workflowQ.data?.length ? (
            <EmptyState title={m.workflowEmpty} description={m.workflowEmptyDescription} />
          ) : workflowQ.data?.map((approval) => (
            <Card key={approval.id}>
              <CardHeader>
                <div className="flex items-center justify-between gap-3">
                  <CardTitle>{m.step}: {approval.step_key}</CardTitle>
                  <Badge status={approval.status} />
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-xs text-gray-500">
                  {m.run} {approval.workflow_run_id.slice(0, 8)}… · {m.requested} {formatDate(approval.created_at)}
                  {approval.expires_at ? ` · ${m.expires} ${formatDate(approval.expires_at)}` : ""}
                </div>
                {Object.keys(approval.metadata || {}).length > 0 && (
                  <pre className="max-h-64 overflow-auto rounded-lg bg-gray-50 p-4 text-xs">{JSON.stringify(approval.metadata, null, 2)}</pre>
                )}
                <textarea
                  aria-label={m.reason}
                  value={reason[approval.id] || ""}
                  onChange={(e) => setReason((current) => ({ ...current, [approval.id]: e.target.value }))}
                  placeholder={m.reasonPlaceholder}
                  className="min-h-20 w-full rounded-lg border border-gray-200 p-3 text-sm"
                  maxLength={2000}
                />
                <div className="flex flex-wrap gap-2">
                  <Button disabled={busy} onClick={() => workflowDecision.mutate({ id: approval.id, decision: "approve" })}>{m.approveResume}</Button>
                  <Button variant="outline" disabled={busy} onClick={() => workflowDecision.mutate({ id: approval.id, decision: "reject" })}>{m.rejectWorkflow}</Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </section>

        <section className="space-y-3">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">{m.toolTitle}</h2>
            <p className="text-sm text-gray-500">{m.toolDescription}</p>
          </div>
          {toolQ.isLoading ? <Spinner /> : !toolQ.isError && !toolQ.data?.length ? (
            <EmptyState title={m.toolEmpty} description={m.toolEmptyDescription} />
          ) : toolQ.data?.map((approval) => (
            <Card key={approval.id}>
              <CardHeader>
                <div className="flex items-center justify-between gap-3">
                  <CardTitle>{approval.tool_name}</CardTitle>
                  <Badge status={approval.status} />
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-xs text-gray-500">
                  {m.run} {approval.run_id.slice(0, 8)}… · {m.requested} {formatDate(approval.created_at)}
                </div>
                <pre className="max-h-64 overflow-auto rounded-lg bg-gray-50 p-4 text-xs">{JSON.stringify(approval.arguments, null, 2)}</pre>
                <textarea
                  aria-label={m.reason}
                  value={reason[approval.id] || ""}
                  onChange={(e) => setReason((current) => ({ ...current, [approval.id]: e.target.value }))}
                  placeholder={m.reasonPlaceholder}
                  className="min-h-20 w-full rounded-lg border border-gray-200 p-3 text-sm"
                  maxLength={2000}
                />
                <div className="flex flex-wrap gap-2">
                  <Button disabled={busy} onClick={() => toolDecision.mutate({ id: approval.id, decision: "approve" })}>{m.approveRun}</Button>
                  <Button variant="outline" disabled={busy} onClick={() => toolDecision.mutate({ id: approval.id, decision: "reject" })}>{m.reject}</Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </section>
      </div>
    </>
  );
}
