"use client";

import { useState } from "react";
import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import {
  decideApproval,
  decideWorkflowApproval,
  getErrorMessage,
  listApprovals,
  listWorkflowApprovals,
} from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export default function ApprovalsPage() {
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

  const error = toolDecision.error ?? workflowDecision.error;
  const busy = toolDecision.isPending || workflowDecision.isPending;
  const loading = toolQ.isLoading || workflowQ.isLoading;
  const toolApprovals = toolQ.data ?? [];
  const workflowApprovals = workflowQ.data ?? [];

  return (
    <>
      <Header title="Approvals" description="Review tool and workflow actions that require explicit human authorization." />
      <div className="space-y-6 p-6">
        {error && <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{getErrorMessage(error)}</div>}

        <section className="space-y-3">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Workflow approvals</h2>
            <p className="text-sm text-gray-500">Approve or reject a paused workflow step. Approval resumes the durable workflow.</p>
          </div>
          {loading ? <Spinner /> : !workflowApprovals.length ? (
            <Card><CardContent className="py-8 text-center text-sm text-gray-500">No pending workflow approvals.</CardContent></Card>
          ) : workflowApprovals.map((approval) => (
            <Card key={approval.id}>
              <CardHeader>
                <div className="flex items-center justify-between gap-3">
                  <CardTitle>Step: {approval.step_key}</CardTitle>
                  <Badge status={approval.status} />
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-xs text-gray-500">
                  Run {approval.workflow_run_id.slice(0, 8)}… · requested {formatDate(approval.created_at)}
                  {approval.expires_at ? ` · expires ${formatDate(approval.expires_at)}` : ""}
                </div>
                {Object.keys(approval.metadata || {}).length > 0 && (
                  <pre className="max-h-64 overflow-auto rounded-lg bg-gray-50 p-4 text-xs">{JSON.stringify(approval.metadata, null, 2)}</pre>
                )}
                <textarea
                  value={reason[approval.id] || ""}
                  onChange={(e) => setReason((current) => ({ ...current, [approval.id]: e.target.value }))}
                  placeholder="Optional decision reason"
                  className="min-h-20 w-full rounded-lg border border-gray-200 p-3 text-sm"
                  maxLength={2000}
                />
                <div className="flex gap-2">
                  <button disabled={busy} onClick={() => workflowDecision.mutate({ id: approval.id, decision: "approve" })} className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">Approve & Resume</button>
                  <button disabled={busy} onClick={() => workflowDecision.mutate({ id: approval.id, decision: "reject" })} className="rounded-lg border border-red-200 px-4 py-2 text-sm font-medium text-red-700 disabled:opacity-50">Reject Workflow</button>
                </div>
              </CardContent>
            </Card>
          ))}
        </section>

        <section className="space-y-3">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Tool approvals</h2>
            <p className="text-sm text-gray-500">Review individual tool calls that are waiting for authorization.</p>
          </div>
          {toolQ.isLoading ? <Spinner /> : !toolApprovals.length ? (
            <Card><CardContent className="py-8 text-center text-sm text-gray-500">No pending tool approvals.</CardContent></Card>
          ) : toolApprovals.map((approval) => (
            <Card key={approval.id}>
              <CardHeader>
                <div className="flex items-center justify-between gap-3">
                  <CardTitle>{approval.tool_name}</CardTitle>
                  <Badge status={approval.status} />
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-xs text-gray-500">Run {approval.run_id.slice(0, 8)}… · requested {formatDate(approval.created_at)}</div>
                <pre className="max-h-64 overflow-auto rounded-lg bg-gray-50 p-4 text-xs">{JSON.stringify(approval.arguments, null, 2)}</pre>
                <textarea
                  value={reason[approval.id] || ""}
                  onChange={(e) => setReason((current) => ({ ...current, [approval.id]: e.target.value }))}
                  placeholder="Optional decision reason"
                  className="min-h-20 w-full rounded-lg border border-gray-200 p-3 text-sm"
                  maxLength={2000}
                />
                <div className="flex gap-2">
                  <button disabled={busy} onClick={() => toolDecision.mutate({ id: approval.id, decision: "approve" })} className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">Approve & Run</button>
                  <button disabled={busy} onClick={() => toolDecision.mutate({ id: approval.id, decision: "reject" })} className="rounded-lg border border-red-200 px-4 py-2 text-sm font-medium text-red-700 disabled:opacity-50">Reject</button>
                </div>
              </CardContent>
            </Card>
          ))}
        </section>
      </div>
    </>
  );
}
