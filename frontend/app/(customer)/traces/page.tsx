"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage, getRunTrace, listRuns } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { useI18n } from "@/lib/i18n/provider";
import { Activity, Brain, CheckCircle2, Clock3, Database, Hammer, MessageSquare, Search, Zap } from "lucide-react";

function isPermissionError(error: unknown) {
  const message = getErrorMessage(error).toLowerCase();
  return message.includes("permission") || message.includes("403") || message.includes("forbidden");
}

function EventIcon({ type }: { type: string }) {
  const Icon = type.includes("memory") ? Brain
    : type.includes("tool") ? Hammer
    : type.includes("llm") || type.includes("ai") ? MessageSquare
    : type.includes("db") || type.includes("data") ? Database
    : type.includes("search") ? Search
    : type.includes("complete") || type.includes("success") ? CheckCircle2
    : type.includes("wait") || type.includes("queue") ? Clock3
    : type.includes("http") || type.includes("web") ? Zap
    : Activity;
  return <Icon className="h-4 w-4" />;
}

export default function TracesPage() {
  const { t: m } = useI18n();
  const params = useSearchParams();
  const runs = useQuery({ queryKey: ["runs", "trace-explorer"], queryFn: () => listRuns() });
  const [selected, setSelected] = useState(params.get("run") || "");
  const selectedId = selected || runs.data?.[0]?.id || "";
  const trace = useQuery({
    queryKey: ["trace", selectedId],
    queryFn: () => getRunTrace(selectedId),
    enabled: !!selectedId,
    refetchInterval: 5000,
  });
  const currentRun = useMemo(() => runs.data?.find((r) => r.id === selectedId), [runs.data, selectedId]);
  const permissionDenied = (runs.isError && isPermissionError(runs.error)) || (trace.isError && isPermissionError(trace.error));

  return (
    <>
      <Header title={m.traces.title} description={m.traces.description} />
      <div className="grid gap-6 p-4 sm:p-6 xl:grid-cols-[330px_minmax(0,1fr)]" dir="auto">
        <Card className="h-fit">
          <CardHeader><CardTitle>{m.traces.runs}</CardTitle></CardHeader>
          <CardContent className="p-0">
            {runs.isLoading ? <div className="p-5"><Spinner /></div>
              : runs.isError ? <div className="space-y-3 p-5 text-sm text-red-600"><p>{getErrorMessage(runs.error)}</p><Button variant="outline" onClick={() => runs.refetch()}>{m.traces.retry}</Button></div>
              : !(runs.data ?? []).length ? <EmptyState icon={Activity} title={m.traces.emptyTitle} description={m.traces.emptyDescription} />
              : <div className="max-h-[720px] overflow-y-auto divide-y">
                {(runs.data ?? []).map((run) => (
                  <button key={run.id} onClick={() => setSelected(run.id)} className={`w-full p-4 text-start transition hover:bg-gray-50 ${selectedId === run.id ? "bg-brand-50" : ""}`}>
                    <div className="flex items-center justify-between gap-2"><span className="font-mono text-xs text-gray-700">{run.id.slice(0, 14)}…</span><Badge status={run.status} /></div>
                    <p className="mt-1 truncate text-sm font-medium text-gray-900">{run.employee_name || run.employee_slug || run.employee_id.slice(0, 8)}</p>
                    <p className="mt-1 text-xs text-gray-500">{formatDate(run.created_at)} · {run.total_tokens.toLocaleString()} {m.traces.tokens}</p>
                  </button>
                ))}
              </div>}
          </CardContent>
        </Card>

        <div className="space-y-6">
          {permissionDenied ? <EmptyState icon={Activity} title={m.traces.permissionDenied} description={m.traces.permissionDescription} />
            : trace.isLoading ? <Spinner />
            : trace.isError ? <div className="space-y-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700"><p>{getErrorMessage(trace.error)}</p><Button variant="outline" onClick={() => trace.refetch()}>{m.traces.retry}</Button></div>
            : !trace.data ? <EmptyState icon={Activity} title={m.traces.selectRun} description={m.traces.selectRunDescription} />
            : <>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <Meta label={m.traces.status} value={<Badge status={trace.data.status} />} />
                <Meta label={m.traces.events} value={trace.data.events.length.toLocaleString()} />
                <Meta label={m.traces.tokens} value={trace.data.total_tokens.toLocaleString()} />
                <Meta label={m.traces.cost} value={formatCurrency(trace.data.total_cost_usd)} />
              </div>
              <Card>
                <CardHeader><CardTitle>{m.traces.timeline}</CardTitle></CardHeader>
                <CardContent>
                  {trace.data.events.length === 0 ? <EmptyState icon={Activity} title={m.traces.noEvents} description={m.traces.noEventsDescription} />
                    : <div className="space-y-0">
                      {trace.data.events.map((event, i) => (
                        <div key={`${event.timestamp}-${i}`} className="relative flex gap-4 pb-7 last:pb-0">
                          <div className="relative flex w-8 shrink-0 justify-center">
                            <div className="z-10 flex h-8 w-8 items-center justify-center rounded-full border bg-white text-brand-600"><EventIcon type={event.type} /></div>
                            {i < trace.data.events.length - 1 && <div className="absolute top-8 h-full w-px bg-gray-200" />}
                          </div>
                          <div className="min-w-0 flex-1 rounded-xl border bg-white p-4 shadow-sm">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <div className="flex items-center gap-2"><Badge status={event.status || event.type} /><span className="font-medium text-gray-900">{event.action || event.type}</span></div>
                              <span className="text-xs text-gray-400">{formatDate(event.timestamp)}</span>
                            </div>
                            {event.provider && <p className="mt-1 text-xs text-gray-500">{event.provider}{event.model ? ` · ${event.model}` : ""}</p>}
                            {(event.prompt_tokens !== undefined || event.completion_tokens !== undefined) && <p className="mt-1 text-xs text-gray-500">{event.prompt_tokens ?? 0} + {event.completion_tokens ?? 0} {m.traces.tokens}{event.latency_ms !== undefined ? ` · ${event.latency_ms} ms` : ""}{event.cost_usd !== undefined ? ` · ${formatCurrency(event.cost_usd)}` : ""}</p>}
                            {event.error_message && <p className="mt-2 text-xs text-red-700">{event.error_message}</p>}
                          </div>
                        </div>
                      ))}
                    </div>}
                </CardContent>
              </Card>
              {currentRun && <p className="text-sm text-gray-500">{m.traces.run}: {currentRun.id}</p>}
            </>}
        </div>
      </div>
    </>
  );
}

function Meta({ label, value }: { label: string; value: React.ReactNode }) {
  return <Card><CardContent><p className="text-xs font-medium uppercase tracking-wide text-gray-400">{label}</p><div className="mt-1 text-sm font-medium text-gray-900">{value}</div></CardContent></Card>;
}
