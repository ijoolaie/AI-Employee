"use client";

import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { api, getErrorMessage, getUsageSummary } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { useI18n } from "@/lib/i18n/provider";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { AlertTriangle, BarChart3 } from "lucide-react";

interface UsageOptimization {
  period_start: string; plan: string;
  usage: { runs: number; tokens: number; employees: number };
  cost_usd: number; successful_work_items: number;
  cost_per_successful_work_item_usd: number;
  budget: { state: string; run_utilization: number; token_utilization: number; remaining_runs: number; remaining_tokens: number };
  optimization_actions: string[];
}
interface CostForecast {
  as_of: string; current_daily_cost_usd: number; baseline_daily_cost_usd: number;
  anomaly: boolean; anomaly_score: number; month_to_date_cost_usd: number;
  projected_month_cost_usd: number; baseline_days: number; actions: string[];
}
function isPermissionError(error: unknown) {
  const message = getErrorMessage(error).toLowerCase();
  return message.includes("permission") || message.includes("403") || message.includes("forbidden");
}
export default function UsagePage() {
  const { t } = useI18n();
  const m = t.usage;
  const [fromAt, setFromAt] = useState("");
  const [toAt, setToAt] = useState("");
  const [appliedRange, setAppliedRange] = useState<{ from_at?: string; to_at?: string }>({});
  const usage = useQuery({
    queryKey: ["usage-summary", appliedRange],
    queryFn: () => getUsageSummary(appliedRange),
  });
  const optimization = useQuery({
    queryKey: ["usage-optimization"],
    queryFn: async () => (await api.get<{ success: boolean; data: UsageOptimization }>("/usage/optimization")).data.data!,
  });
  const forecast = useQuery({
    queryKey: ["usage-cost-forecast"],
    queryFn: async () => (await api.get<{ success: boolean; data: CostForecast }>("/usage/cost-forecast")).data.data!,
  });
  const retry = () => { void usage.refetch(); void optimization.refetch(); void forecast.refetch(); };
  const permission = [usage.error, optimization.error, forecast.error].some(isPermissionError);
  const allFailed = !!usage.error && !!optimization.error && !!forecast.error;
  return <>
    <Header title={m.title} description={m.description} />
    <div className="space-y-6 p-6">
      <Card>
        <CardContent className="flex flex-col gap-3 pt-6 sm:flex-row sm:items-end sm:flex-wrap">
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-gray-500">{m.dateFrom}</span>
            <input type="date" value={fromAt} onChange={e => setFromAt(e.target.value)} className="rounded-lg border px-3 py-2 text-sm" />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-gray-500">{m.dateTo}</span>
            <input type="date" value={toAt} onChange={e => setToAt(e.target.value)} className="rounded-lg border px-3 py-2 text-sm" />
          </label>
          <Button disabled={!!fromAt && !!toAt && fromAt > toAt} onClick={() => setAppliedRange({
            ...(fromAt ? { from_at: `${fromAt}T00:00:00` } : {}),
            ...(toAt ? { to_at: `${toAt}T23:59:59` } : {}),
          })}>{m.apply}</Button>
          <Button variant="secondary" onClick={() => { setFromAt(""); setToAt(""); setAppliedRange({}); }}>{m.clear}</Button>
        </CardContent>
      </Card>
      {(usage.isLoading || optimization.isLoading || forecast.isLoading) && <div className="flex justify-center py-8" aria-label={m.loading}><Spinner /></div>}
      {allFailed && <div role="alert" className="space-y-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        <p>{permission ? m.permissionDenied : m.loadError}</p><Button variant="secondary" onClick={retry}>{m.retry}</Button>
      </div>}
      {!allFailed && usage.error && <InlineError text={isPermissionError(usage.error) ? m.permissionDenied : m.loadError} onRetry={() => void usage.refetch()} retry={m.retry} />}
      {!usage.isLoading && !usage.error && usage.data && <>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Metric title={m.aiCalls} value={usage.data.calls.toLocaleString()} />
          <Metric title={m.totalTokens} value={usage.data.total_tokens.toLocaleString()} />
          <Metric title={m.recordedCost} value={formatCurrency(usage.data.cost_usd)} />
          <Metric title={m.avgLatency} value={`${usage.data.avg_latency_ms.toFixed(0)} ms`} />
        </div>
        {optimization.error && <InlineError text={isPermissionError(optimization.error) ? m.permissionDenied : m.optimizationError} onRetry={() => void optimization.refetch()} retry={m.retry} />}
        {optimization.data && <Card><CardHeader><CardTitle>{m.budgetTitle}</CardTitle></CardHeader><CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <Metric title={m.plan} value={optimization.data.plan} />
            <Metric title={m.runUtilization} value={`${(optimization.data.budget.run_utilization * 100).toFixed(1)}%`} />
            <Metric title={m.tokenUtilization} value={`${(optimization.data.budget.token_utilization * 100).toFixed(1)}%`} />
            <Metric title={m.costPerSuccess} value={formatCurrency(optimization.data.cost_per_successful_work_item_usd)} />
          </div>
          <div className="rounded-lg border border-gray-100 bg-gray-50 p-4 text-sm"><div className="flex flex-wrap gap-x-6 gap-y-2">
            <span>{m.budgetState}: <strong>{optimization.data.budget.state}</strong></span>
            <span>{m.remainingRuns}: <strong>{optimization.data.budget.remaining_runs.toLocaleString()}</strong></span>
            <span>{m.remainingTokens}: <strong>{optimization.data.budget.remaining_tokens.toLocaleString()}</strong></span>
          </div></div>
          {optimization.data.optimization_actions.length > 0 && <ul className="list-disc space-y-1 ps-5 text-sm text-gray-600">{optimization.data.optimization_actions.map(a => <li key={a}>{a}</li>)}</ul>}
        </CardContent></Card>}
        {forecast.error && <InlineError text={isPermissionError(forecast.error) ? m.permissionDenied : m.forecastError} onRetry={() => void forecast.refetch()} retry={m.retry} />}
        {forecast.data && <Card><CardHeader><CardTitle className="flex items-center gap-2"><AlertTriangle className="h-4 w-4" />{m.forecastTitle}</CardTitle></CardHeader><CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <Metric title={m.today} value={formatCurrency(forecast.data.current_daily_cost_usd)} />
            <Metric title={m.baseline} value={formatCurrency(forecast.data.baseline_daily_cost_usd)} />
            <Metric title={m.monthToDate} value={formatCurrency(forecast.data.month_to_date_cost_usd)} />
            <Metric title={m.projectedMonth} value={formatCurrency(forecast.data.projected_month_cost_usd)} />
          </div>
          <div className={`rounded-lg border px-4 py-3 text-sm ${forecast.data.anomaly ? "border-amber-200 bg-amber-50 text-amber-800" : "border-gray-100 bg-gray-50 text-gray-600"}`}>{forecast.data.anomaly ? `${m.anomalyDetected} (${m.score}: ${forecast.data.anomaly_score})` : m.noAnomaly}</div>
          {forecast.data.actions.length > 0 && <ul className="list-disc space-y-1 ps-5 text-sm text-gray-600">{forecast.data.actions.map(a => <li key={a}>{a}</li>)}</ul>}
        </CardContent></Card>}
        <Card><CardHeader><CardTitle className="flex items-center gap-2"><BarChart3 className="h-4 w-4" />{m.breakdownTitle}</CardTitle></CardHeader><CardContent>
          {usage.data.breakdown.length === 0 ? <EmptyState icon={BarChart3} title={m.emptyTitle} description={m.emptyDescription} /> :
          <div className="overflow-x-auto"><table className="w-full min-w-[720px] text-start text-sm"><thead><tr className="border-b border-gray-100 text-xs uppercase text-gray-500">
            <th className="px-3 py-3 text-start font-medium">{m.provider}</th><th className="px-3 py-3 text-start font-medium">{m.model}</th><th className="px-3 py-3 text-start font-medium">{m.calls}</th><th className="px-3 py-3 text-start font-medium">{m.tokens}</th><th className="px-3 py-3 text-start font-medium">{m.cost}</th><th className="px-3 py-3 text-start font-medium">{m.latency}</th>
          </tr></thead><tbody>{usage.data.breakdown.map(item => <tr key={`${item.provider}:${item.model}`} className="border-b border-gray-50">
            <td className="px-3 py-3 font-medium text-gray-900">{item.provider}</td><td className="px-3 py-3 font-mono text-xs text-gray-600">{item.model}</td><td className="px-3 py-3 text-gray-600">{item.calls.toLocaleString()}</td><td className="px-3 py-3 text-gray-600">{item.total_tokens.toLocaleString()}</td><td className="px-3 py-3 text-gray-600">{formatCurrency(item.cost_usd)}</td><td className="px-3 py-3 text-gray-600">{item.avg_latency_ms.toFixed(0)} ms</td>
          </tr>)}</tbody></table></div>}
        </CardContent></Card>
        {usage.data.notes.length > 0 && <div className="rounded-lg border border-gray-200 bg-white px-4 py-3 text-xs text-gray-500">{usage.data.notes.map(n => <p key={n}>{n}</p>)}</div>}
      </>}
    </div>
  </>;
}
function InlineError({text,onRetry,retry}:{text:string;onRetry:()=>void;retry:string}) {
  return <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"><span>{text}</span><Button variant="secondary" onClick={onRetry}>{retry}</Button></div>;
}
function Metric({title,value}:{title:string;value:string}) {
  return <Card><CardContent className="pt-6"><p className="text-sm text-gray-500">{title}</p><p className="mt-2 text-2xl font-semibold text-gray-900">{value}</p></CardContent></Card>;
}
