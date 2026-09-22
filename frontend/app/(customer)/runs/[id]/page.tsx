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
import { useI18n } from "@/lib/i18n/provider";

export default function RunDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { t } = useI18n();
  const tx = t.runs;

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
    return <div className="p-6 text-sm text-red-600">{getErrorMessage(error) || tx.notFound}</div>;
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
        title={`${tx.detailTitle} ${run.id.slice(0, 8)}…`}
        description={run.employee_name ? `${run.employee_name} (${run.employee_slug || run.employee_id.slice(0, 8)})` : `${tx.employee} ${run.employee_id.slice(0, 8)}…`}
        actions={<div className="flex items-center gap-2">{isActive && <button onClick={() => refetch()} className="text-xs text-brand-600 hover:underline">{tx.refresh}</button>}<Badge status={run.status} /></div>}
      />
      <div className="space-y-6 p-6">
        {run.status === "waiting" && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            <p className="font-medium">{tx.humanApprovalRequired}</p>
            <p className="mt-1 text-amber-800">{tx.approvalText}</p>
          </div>
        )}
        {run.status === "pending" && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            <p className="font-medium">{tx.waitingWorker}</p>
            <p className="mt-1 text-amber-800">{tx.queuedText}</p>
          </div>
        )}
        {run.status === "failed" && run.error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            <p className="font-medium">{tx.failed}</p>
            <p className="mt-1">{typeof run.error === "object" && "message" in run.error ? String((run.error as { message?: string }).message) : JSON.stringify(run.error)}</p>
          </div>
        )}

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Meta label={tx.status} value={<Badge status={run.status} />} />
          <Meta label={tx.tokens} value={run.total_tokens.toLocaleString()} />
          <Meta label={tx.cost} value={formatCurrency(run.total_cost_usd)} />
          <Meta label={tx.created} value={formatDate(run.created_at)} />
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card><CardHeader><CardTitle>{tx.input}</CardTitle></CardHeader><CardContent><pre className="max-h-80 overflow-auto rounded-lg bg-gray-50 p-4 text-xs text-gray-800">{JSON.stringify(run.input_data, null, 2)}</pre></CardContent></Card>
          <Card><CardHeader><CardTitle>{run.error ? tx.error : tx.output}</CardTitle></CardHeader><CardContent>{run.error ? <pre className="max-h-80 overflow-auto rounded-lg bg-red-50 p-4 text-xs text-red-800">{JSON.stringify(run.error, null, 2)}</pre> : run.output_data ? <pre className="max-h-80 overflow-auto rounded-lg bg-gray-50 p-4 text-xs text-gray-800">{JSON.stringify(run.output_data, null, 2)}</pre> : <p className="text-sm text-gray-500">{isActive ? tx.inProgress : tx.noOutput}</p>}</CardContent></Card>
        </div>

        {reportArtifacts && (
          <Card>
            <CardHeader><CardTitle>{tx.reportDownloads}</CardTitle></CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {reportArtifacts.pdf_file_id && (
                  <Button size="sm" onClick={() => downloadFile(reportArtifacts.pdf_file_id as string, "report.pdf")}>
                    <FileText className="h-4 w-4" />
                    {tx.downloadPdf}
                  </Button>
                )}
                {reportArtifacts.excel_file_id && (
                  <Button size="sm" onClick={() => downloadFile(reportArtifacts.excel_file_id as string, "report.xlsx")}>
                    <FileSpreadsheet className="h-4 w-4" />
                    {tx.downloadExcel}
                  </Button>
                )}
                {Array.isArray(reportArtifacts.chart_file_ids) &&
                  (reportArtifacts.chart_file_ids as string[]).map((chartId, i) => (
                    <Button key={chartId} size="sm" onClick={() => downloadFile(chartId, `chart_${i + 1}.png`)}>
                      <Download className="h-4 w-4" />
                      {tx.chart} {i + 1}
                    </Button>
                  ))}
              </div>
            </CardContent>
          </Card>
        )}

        {documentArtifacts?.extracted_text_file_id && (
          <Card>
            <CardHeader><CardTitle>{tx.documentDownloads}</CardTitle></CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                <Button
                  size="sm"
                  onClick={() =>
                    downloadFile(documentArtifacts.extracted_text_file_id as string, "extracted_text.txt")
                  }
                >
                  <FileText className="h-4 w-4" />
                  {tx.downloadExtractedText}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader><CardTitle>{tx.executionTrace}</CardTitle></CardHeader>
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
                    {event.type === "ai_provider_call" && <p className="mt-1 text-xs text-gray-500">{event.provider} · {event.model} · {event.prompt_tokens ?? 0} + {event.completion_tokens ?? 0} {tx.tokens} · {event.latency_ms ?? 0} ms · {formatCurrency(event.cost_usd ?? 0)}</p>}
                  </div>
                ))}
              </div>
            ) : <p className="text-sm text-gray-500">{tx.noTrace}</p>}
          </CardContent>
        </Card>

        {run.status === "success" && <RunFeedback runId={run.id} employeeId={run.employee_id} />}

        <div className="text-sm text-gray-500"><Link href={`/employees/${run.employee_id}`} className="text-brand-600 hover:underline">{tx.backToEmployee}</Link><span className="mx-2">·</span>{tx.started}: {formatDate(run.started_at)} · {tx.completed}: {formatDate(run.completed_at)}</div>
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
  const { t } = useI18n();
  const tx = t.runs;
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
          <p className="text-sm text-gray-600">{tx.thanks}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader><CardTitle>{tx.feedbackTitle}</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <div className="flex gap-1">
          {[1, 2, 3, 4, 5].map((n) => (
            <button key={n} type="button" onClick={() => setRating(n)} aria-label={`${tx.rate} ${n}`}>
              <Star className={`h-6 w-6 ${n <= rating ? "fill-amber-400 text-amber-400" : "text-gray-300"}`} />
            </button>
          ))}
        </div>
        <textarea
          className="min-h-[70px] w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
          placeholder={tx.optionalComment}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />
        {mutation.error && (
          <p className="text-sm text-red-600">{getErrorMessage(mutation.error)}</p>
        )}
        <Button size="sm" disabled={rating === 0} loading={mutation.isPending} onClick={() => mutation.mutate()}>
          {tx.sendFeedback}
        </Button>
      </CardContent>
    </Card>
  );
}
