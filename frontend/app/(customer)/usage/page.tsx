"use client";

import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { api, getErrorMessage, getUsageSummary } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, BarChart3 } from "lucide-react";

interface UsageOptimization {
  period_start: string;
  plan: string;
  usage: { runs: number; tokens: number; employees: number };
  cost_usd: number;
  successful_work_items: number;
  cost_per_successful_work_item_usd: number;
  budget: {
    state: string;
    run_utilization: number;
    token_utilization: number;
    remaining_runs: number;
    remaining_tokens: number;
  };
  optimization_actions: string[];
}

interface CostForecast {
  as_of: string;
  current_daily_cost_usd: number;
  baseline_daily_cost_usd: number;
  anomaly: boolean;
  anomaly_score: number;
  month_to_date_cost_usd: number;
  projected_month_cost_usd: number;
  baseline_days: number;
  actions: string[];
}

export default function UsagePage() {
  const usage = useQuery({
    queryKey: ["usage-summary"],
    queryFn: () => getUsageSummary(),
  });
  const optimization = useQuery({
    queryKey: ["usage-optimization"],
    queryFn: async () => (await api.get<{ success: boolean; data: UsageOptimization }>("/usage/optimization")).data.data!,
  });
  const forecast = useQuery({
    queryKey: ["usage-cost-forecast"],
    queryFn: async () => (await api.get<{ success: boolean; data: CostForecast }>("/usage/cost-forecast")).data.data!,
  });

  return (
    <>
      <Header title="Usage & Cost" description="AI execution usage, budget controls and recorded provider cost signals" />
      <div className="space-y-6 p-6">
        {usage.isLoading && <Spinner />}
        {usage.error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {getErrorMessage(usage.error)}
          </div>
        )}
        {!usage.isLoading && !usage.error && usage.data && (
          <>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <Metric title="AI calls" value={usage.data.calls.toLocaleString()} />
              <Metric title="Total tokens" value={usage.data.total_tokens.toLocaleString()} />
              <Metric title="Recorded cost" value={formatCurrency(usage.data.cost_usd)} />
              <Metric title="Avg latency" value={`${usage.data.avg_latency_ms.toFixed(0)} ms`} />
            </div>

            {optimization.data && (
              <Card>
                <CardHeader><CardTitle>Plan budget & unit economics</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                    <Metric title="Plan" value={optimization.data.plan} />
                    <Metric title="Run utilization" value={`${(optimization.data.budget.run_utilization * 100).toFixed(1)}%`} />
                    <Metric title="Token utilization" value={`${(optimization.data.budget.token_utilization * 100).toFixed(1)}%`} />
                    <Metric title="Cost / successful work" value={formatCurrency(optimization.data.cost_per_successful_work_item_usd)} />
                  </div>
                  <div className="rounded-lg border border-gray-100 bg-gray-50 p-4 text-sm">
                    <div className="flex flex-wrap gap-x-6 gap-y-2">
                      <span>Budget state: <strong>{optimization.data.budget.state}</strong></span>
                      <span>Remaining runs: <strong>{optimization.data.budget.remaining_runs.toLocaleString()}</strong></span>
                      <span>Remaining tokens: <strong>{optimization.data.budget.remaining_tokens.toLocaleString()}</strong></span>
                    </div>
                  </div>
                  <ul className="list-disc space-y-1 pl-5 text-sm text-gray-600">
                    {optimization.data.optimization_actions.map((action) => <li key={action}>{action}</li>)}
                  </ul>
                </CardContent>
              </Card>
            )}

            {forecast.data && (
              <Card>
                <CardHeader><CardTitle className="flex items-center gap-2"><AlertTriangle className="h-4 w-4" />Cost anomaly & forecast</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                    <Metric title="Today" value={formatCurrency(forecast.data.current_daily_cost_usd)} />
                    <Metric title="7-day baseline" value={formatCurrency(forecast.data.baseline_daily_cost_usd)} />
                    <Metric title="Month to date" value={formatCurrency(forecast.data.month_to_date_cost_usd)} />
                    <Metric title="Projected month" value={formatCurrency(forecast.data.projected_month_cost_usd)} />
                  </div>
                  <div className={`rounded-lg border px-4 py-3 text-sm ${forecast.data.anomaly ? "border-amber-200 bg-amber-50 text-amber-800" : "border-gray-100 bg-gray-50 text-gray-600"}`}>
                    {forecast.data.anomaly ? `Cost anomaly detected (score ${forecast.data.anomaly_score}).` : "No material cost anomaly detected."}
                  </div>
                  <ul className="list-disc space-y-1 pl-5 text-sm text-gray-600">
                    {forecast.data.actions.map((action) => <li key={action}>{action}</li>)}
                  </ul>
                </CardContent>
              </Card>
            )}

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><BarChart3 className="h-4 w-4" />Provider / model breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                {usage.data.breakdown.length === 0 ? (
                  <p className="text-sm text-gray-500">No AI provider calls have been recorded yet.</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead><tr className="border-b border-gray-100 text-xs uppercase text-gray-500"><th className="px-3 py-3 font-medium">Provider</th><th className="px-3 py-3 font-medium">Model</th><th className="px-3 py-3 font-medium">Calls</th><th className="px-3 py-3 font-medium">Tokens</th><th className="px-3 py-3 font-medium">Cost</th><th className="px-3 py-3 font-medium">Latency</th></tr></thead>
                      <tbody>{usage.data.breakdown.map((item) => <tr key={`${item.provider}:${item.model}`} className="border-b border-gray-50"><td className="px-3 py-3 font-medium text-gray-900">{item.provider}</td><td className="px-3 py-3 font-mono text-xs text-gray-600">{item.model}</td><td className="px-3 py-3 text-gray-600">{item.calls.toLocaleString()}</td><td className="px-3 py-3 text-gray-600">{item.total_tokens.toLocaleString()}</td><td className="px-3 py-3 text-gray-600">{formatCurrency(item.cost_usd)}</td><td className="px-3 py-3 text-gray-600">{item.avg_latency_ms.toFixed(0)} ms</td></tr>)}</tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>

            <div className="rounded-lg border border-gray-200 bg-white px-4 py-3 text-xs text-gray-500">
              {usage.data.notes.map((note) => <p key={note}>{note}</p>)}
            </div>
          </>
        )}
      </div>
    </>
  );
}

function Metric({ title, value }: { title: string; value: string }) {
  return <Card><CardContent className="pt-6"><p className="text-sm text-gray-500">{title}</p><p className="mt-2 text-2xl font-semibold text-gray-900">{value}</p></CardContent></Card>;
}
