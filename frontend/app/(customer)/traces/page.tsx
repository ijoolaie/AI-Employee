"use client";

import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage, getRunTrace, listRuns } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { Brain, CheckCircle2, Clock3, Database, Hammer, MessageSquare, Search, Zap } from "lucide-react";

export default function TracesPage() {
  const params = useSearchParams();
  const runs = useQuery({ queryKey: ["runs", "trace-explorer"], queryFn: () => listRuns(), refetchInterval: 10000 });
  const [selected, setSelected] = useState(params.get("run") || "");
  useEffect(() => { if (!selected && runs.data?.[0]) setSelected(runs.data[0].id); }, [runs.data, selected]);
  const trace = useQuery({ queryKey: ["trace", selected], queryFn: () => getRunTrace(selected), enabled: !!selected, refetchInterval: 5000 });
  const currentRun = useMemo(() => runs.data?.find(r => r.id === selected), [runs.data, selected]);
  return <>
    <Header title="Trace Explorer" description="Inspect planner, memory, tool and LLM execution events" />
    <div className="grid gap-6 p-6 xl:grid-cols-[330px_minmax(0,1fr)]">
      <Card className="h-fit"><CardHeader><CardTitle>Runs</CardTitle></CardHeader><CardContent className="p-0"><div className="max-h-[720px] overflow-y-auto divide-y">{runs.isLoading ? <div className="p-5"><Spinner/></div> : (runs.data ?? []).map(r => <button key={r.id} onClick={() => setSelected(r.id)} className={`w-full p-4 text-left transition hover:bg-gray-50 ${selected === r.id ? "bg-brand-50" : ""}`}><div className="flex items-center justify-between gap-2"><span className="font-mono text-xs text-gray-700">{r.id.slice(0,14)}…</span><Badge status={r.status}/></div><p className="mt-1 truncate text-sm font-medium text-gray-900">{r.employee_name || r.employee_slug || r.employee_id.slice(0,8)}</p><p className="mt-1 text-xs text-gray-500">{formatDate(r.created_at)} · {r.total_tokens.toLocaleString()} tokens</p></button>)}{!(runs.data ?? []).length && <p className="p-5 text-sm text-gray-500">No runs found.</p>}</div></CardContent></Card>
      <div className="space-y-6">{trace.error && <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{getErrorMessage(trace.error)}</div>}{trace.isLoading && <Spinner/>}{trace.data && <><div className="grid gap-4 sm:grid-cols-4"><K label="Status" value={trace.data.status}/><K label="Events" value={trace.data.events.length}/><K label="Tokens" value={trace.data.total_tokens.toLocaleString()}/><K label="Cost" value={formatCurrency(trace.data.total_cost_usd)}/></div><Card><CardHeader><div><CardTitle>Execution timeline</CardTitle><p className="mt-1 text-xs text-gray-500">Run {trace.data.run_id}</p></div>{currentRun && <Badge status={currentRun.status}/>}</CardHeader><CardContent><div className="space-y-0">{trace.data.events.map((event, i) => <div key={`${event.timestamp}-${i}`} className="relative flex gap-4 pb-7 last:pb-0"><div className="relative flex w-8 shrink-0 justify-center"><div className="z-10 flex h-8 w-8 items-center justify-center rounded-full border bg-white text-brand-600"><EventIcon type={event.type}/></div>{i < trace.data.events.length - 1 && <div className="absolute top-8 h-full w-px bg-gray-200"/>}</div><div className="min-w-0 flex-1 rounded-xl border bg-white p-4 shadow-sm"><div className="flex flex-wrap items-center justify-between gap-2"><div className="flex items-center gap-2"><span className="font-medium text-gray-900">{event.action || event.type}</span>{event.status && <Badge status={event.status}/>}</div><span className="text-xs text-gray-400">{formatDate(event.timestamp)}</span></div><div className="mt-2 grid gap-2 text-xs text-gray-500 sm:grid-cols-4">{event.provider && <span>Provider: <b className="text-gray-700">{event.provider}</b></span>}{event.model && <span>Model: <b className="text-gray-700">{event.model}</b></span>}{event.latency_ms != null && <span>Latency: <b className="text-gray-700">{Math.round(event.latency_ms)} ms</b></span>}{(event.prompt_tokens != null || event.completion_tokens != null) && <span>Tokens: <b className="text-gray-700">{((event.prompt_tokens ?? 0)+(event.completion_tokens ?? 0)).toLocaleString()}</b></span>}</div>{event.error_message && <p className="mt-3 rounded-lg bg-red-50 p-2 text-xs text-red-700">{event.error_message}</p>}{event.metadata && <details className="mt-3"><summary className="cursor-pointer text-xs font-medium text-brand-600">Metadata</summary><pre className="mt-2 overflow-auto rounded-lg bg-gray-50 p-3 text-[11px] text-gray-600">{JSON.stringify(event.metadata,null,2)}</pre></details>}</div></div>)}</div></CardContent></Card></>}</div>
    </div>
  </>;
}
function K({label,value}:{label:string;value:string|number}){return <Card><CardContent><p className="text-xs text-gray-500">{label}</p><p className="mt-1 text-lg font-semibold">{value}</p></CardContent></Card>}
function EventIcon({type}:{type:string}){const t=type.toLowerCase(); if(t.includes("tool")) return <Hammer className="h-4 w-4"/>; if(t.includes("memory")) return <Brain className="h-4 w-4"/>; if(t.includes("llm")||t.includes("provider")) return <Zap className="h-4 w-4"/>; if(t.includes("rag")||t.includes("knowledge")) return <Search className="h-4 w-4"/>; if(t.includes("plan")) return <CheckCircle2 className="h-4 w-4"/>; if(t.includes("db")) return <Database className="h-4 w-4"/>; if(t.includes("prompt")) return <MessageSquare className="h-4 w-4"/>; return <Clock3 className="h-4 w-4"/>;}
