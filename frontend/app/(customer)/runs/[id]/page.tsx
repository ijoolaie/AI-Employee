"use client";

import { use, useEffect, useState } from "react";
import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { downloadFile, getErrorMessage, getRun, getRunTrace, submitFeedback } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Download, FileSpreadsheet, FileText, Star } from "lucide-react";
import Link from "next/link";

export default function RunDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  const { data: run, isLoading, error, refetch } = useQuery({
    queryKey: ["runs", id],
    queryFn: () => getRun(id),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "pending" || status === "queued" || status === "running" || status === "waiting" ? 2000 : false;
    },
  });

  const traceQ = useQuery({
    queryKey: ["runs", id, "trace"],
    queryFn: () => getRunTrace(id),
    refetchInterval: run && ["pending", "queued", "running"].includes(run.status) ? 2000 : false,
  });

  useEffect(() => {}, [run?.status]);

  if (isLoading) return <Spinner className="min-h-[50vh]" />;
  if (error || !run) {
    return <div className="p-6 text-sm text-red-600">{getErrorMessage(error) || "Run not found"}</div>;
  }

  const isActive = ["pending", "queued", "running", "waiting"].includes(run.status);
  // Phase 2: Report Employee runs carry a whitelisted `report_artifacts`
  // shape on output_data (see run_service.py) — render download buttons
  // when present, for any Employee that produces it.
  const reportArtifacts = run.output_data?.report_artifacts as
    | { pdf_file_id?: string; excel_file_id?: string; chart_file_ids?: string[] }
    | undefined;
  // Phase 5: Document Employee runs carry a whitelisted `document_artifacts`
  // shape (see run_service.py) — same additive pattern as report_artifacts.
  const documentArtifacts = run.output_data?.document_artifacts as
    | { extracted_text_file_id?: string }
    | undefined;

  return (
    <>
      <Header
        title={`Run ${run.id.slice(0, 8)}…`}
        description={run.employee_name ? `${run.employee_name} (${run.employee_slug || run.employee_id.slice(0, 8)})` : `Employee ${run.employee_id.slice(0, 8)}…`}
        actions={<div className="flex items-center gap-2">{isActive && <button onClick={() => refetch()} className="text-xs text-brand-600 hover:underline">Refresh</button>}<Badge status={run.status} /></div>}
      />
      <div className="space-y-6 p-6">
        {run.status === "waiting" && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            <p className="font-medium">Human approval required</p>
            <p className="mt-1 text-amber-800">This Run is paused because an AI-requested Tool requires explicit human approval. Open Approvals to review it.</p>
          </div>
        )}
        {run.status === "pending" && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            <p className="font-medium">Waiting for the worker</p>
            <p className="mt-1 text-amber-800">The Run is queued. Make sure Redis and the Windows Celery worker are running.</p>
          </div>
        )}
        {run.status === "failed" && run.error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            <p className="font-medium">Run failed</p>
            <p className="mt-1">{typeof run.error === "object" && "message" in run.error ? String((run.error as { message?: string }).message) : JSON.stringify(run.error)}</p>
          </div>
        )}

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Meta label="Status" value={<Badge status={run.status} />} />
          <Meta label="Tokens" value={run.total_tokens.toLocaleString()} />
          <Meta label="Cost" value={formatCurrency(run.total_cost_usd)} />
          <Meta label="Created" value={formatDate(run.created_at)} />
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card><CardHeader><CardTitle>Input</CardTitle></CardHeader><CardContent><pre className="max-h-80 overflow-auto rounded-lg bg-gray-50 p-4 text-xs text-gray-800">{JSON.stringify(run.input_data, null, 2)}</pre></CardContent></Card>
          <Card><CardHeader><CardTitle>{run.error ? "Error" : "Output"}</CardTitle></CardHeader><CardContent>{run.error ? <pre className="max-h-80 overflow-auto rounded-lg bg-red-50 p-4 text-xs text-red-800">{JSON.stringify(run.error, null, 2)}</pre> : run.output_data ? <pre className="max-h-80 overflow-auto rounded-lg bg-gray-50 p-4 text-xs text-gray-800">{JSON.stringify(run.output_data, null, 2)}</pre> : <p className="text-sm text-gray-500">{isActive ? "Run in progress…" : "No output produced."}</p>}</CardContent></Card>
        </div>

        {reportArtifacts && (
          <Card>
            <CardHeader><CardTitle>Report Employee — downloads</CardTitle></CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {reportArtifacts.pdf_file_id && (
                  <Button size="sm" onClick={() => downloadFile(reportArtifacts.pdf_file_id as string, "report.pdf")}>
                    <FileText className="h-4 w-4" />
                    Download PDF
                  </Button>
                )}
                {reportArtifacts.excel_file_id && (
                  <Button size="sm" onClick={() => downloadFile(reportArtifacts.excel_file_id as string, "report.xlsx")}>
                    <FileSpreadsheet className="h-4 w-4" />
                    Download Excel
                  </Button>
                )}
                {Array.isArray(reportArtifacts.chart_file_ids) &&
                  (reportArtifacts.chart_file_ids as string[]).map((chartId, i) => (
                    <Button key={chartId} size="sm" onClick={() => downloadFile(chartId, `chart_${i + 1}.png`)}>
                      <Download className="h-4 w-4" />
                      Chart {i + 1}
                    </Button>
                  ))}
              </div>
            </CardContent>
          </Card>
        )}

        {documentArtifacts?.extracted_text_file_id && (
          <Card>
            <CardHeader><CardTitle>Document Employee — downloads</CardTitle></CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                <Button
                  size="sm"
                  onClick={() =>
                    downloadFile(documentArtifacts.extracted_text_file_id as string, "extracted_text.txt")
                  }
                >
                  <FileText className="h-4 w-4" />
                  Download extracted text
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader><CardTitle>Execution trace</CardTitle></CardHeader>
          <CardContent>
            {traceQ.isLoading ? <Spinner /> : traceQ.error ? <p className="text-sm text-red-600">{getErrorMessage(traceQ.error)}</p> : traceQ.data?.events.length ? (
              <div className="space-y-3">
                {traceQ.data.events.map((event, index) => (
                  <div key={`${event.timestamp}-${index}`} className="rounded-lg border border-gray-100 bg-gray-50 p-3 text-sm">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge status={event.status || event.type} />
                      <span className="font-medium text-gray-900">{event.action || event.provider || event.type}</span>
                      <span className="text-xs text-gray-400">{formatDate(event.timestamp)}</span>
                    </div>
                    {event.type === "ai_provider_call" && <p className="mt-1 text-xs text-gray-500">{event.provider} · {event.model} · {event.prompt_tokens ?? 0} + {event.completion_tokens ?? 0} tokens · {event.latency_ms ?? 0} ms · {formatCurrency(event.cost_usd ?? 0)}</p>}
                  </div>
                ))}
              </div>
            ) : <p className="text-sm text-gray-500">No trace events recorded yet.</p>}
          </CardContent>
        </Card>

        {run.status === "success" && <RunFeedback runId={run.id} employeeId={run.employee_id} />}

        <div className="text-sm text-gray-500"><Link href={`/employees/${run.employee_id}`} className="text-brand-600 hover:underline">← Back to employee</Link><span className="mx-2">·</span>Started: {formatDate(run.started_at)} · Completed: {formatDate(run.completed_at)}</div>
      </div>
    </>
  );
}

function Meta({ label, value }: { label: string; value: React.ReactNode }) {
  return <Card><CardContent><p className="text-xs font-medium uppercase tracking-wide text-gray-400">{label}</p><div className="mt-1 text-sm font-medium text-gray-900">{value}</div></CardContent></Card>;
}

// Phase 3 — Validation tooling: lets a real user record feedback on a
// completed Run in-product, feeding app/(admin)/admin/validation.
function RunFeedback({ runId, employeeId }: { runId: string; employeeId: string }) {
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [sent, setSent] = useState(false);

  const mutation = useMutation({
    mutationFn: () => submitFeedback({ rating, comment: comment || undefined, run_id: runId, employee_id: employeeId, category: "run" }),
    onSuccess: () => setSent(true),
  });

  if (sent) {
    return (
      <Card>
        <CardContent>
          <p className="text-sm text-gray-600">Thanks — your feedback was recorded.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader><CardTitle>Was this report useful?</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <div className="flex gap-1">
          {[1, 2, 3, 4, 5].map((n) => (
            <button key={n} type="button" onClick={() => setRating(n)} aria-label={`Rate ${n}`}>
              <Star className={`h-6 w-6 ${n <= rating ? "fill-amber-400 text-amber-400" : "text-gray-300"}`} />
            </button>
          ))}
        </div>
        <textarea
          className="min-h-[70px] w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
          placeholder="Optional comment — what worked, what didn't?"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />
        {mutation.error && (
          <p className="text-sm text-red-600">{getErrorMessage(mutation.error)}</p>
        )}
        <Button size="sm" disabled={rating === 0} loading={mutation.isPending} onClick={() => mutation.mutate()}>
          Send feedback
        </Button>
      </CardContent>
    </Card>
  );
}
