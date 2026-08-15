"use client";

import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage, getUsageSummary } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { BarChart3 } from "lucide-react";

export default function UsagePage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["usage-summary"],
    queryFn: () => getUsageSummary(),
  });

  return (
    <>
      <Header title="Usage" description="AI execution usage and recorded provider costs" />
      <div className="space-y-6 p-6">
        {isLoading && <Spinner />}
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {getErrorMessage(error)}
          </div>
        )}
        {!isLoading && !error && data && (
          <>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <Metric title="AI calls" value={data.calls.toLocaleString()} />
              <Metric title="Total tokens" value={data.total_tokens.toLocaleString()} />
              <Metric title="Recorded cost" value={formatCurrency(data.cost_usd)} />
              <Metric title="Avg latency" value={`${data.avg_latency_ms.toFixed(0)} ms`} />
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  Provider / model breakdown
                </CardTitle>
              </CardHeader>
              <CardContent>
                {data.breakdown.length === 0 ? (
                  <p className="text-sm text-gray-500">No AI provider calls have been recorded yet.</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead>
                        <tr className="border-b border-gray-100 text-xs uppercase text-gray-500">
                          <th className="px-3 py-3 font-medium">Provider</th>
                          <th className="px-3 py-3 font-medium">Model</th>
                          <th className="px-3 py-3 font-medium">Calls</th>
                          <th className="px-3 py-3 font-medium">Tokens</th>
                          <th className="px-3 py-3 font-medium">Cost</th>
                          <th className="px-3 py-3 font-medium">Latency</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.breakdown.map((item) => (
                          <tr key={`${item.provider}:${item.model}`} className="border-b border-gray-50">
                            <td className="px-3 py-3 font-medium text-gray-900">{item.provider}</td>
                            <td className="px-3 py-3 font-mono text-xs text-gray-600">{item.model}</td>
                            <td className="px-3 py-3 text-gray-600">{item.calls.toLocaleString()}</td>
                            <td className="px-3 py-3 text-gray-600">{item.total_tokens.toLocaleString()}</td>
                            <td className="px-3 py-3 text-gray-600">{formatCurrency(item.cost_usd)}</td>
                            <td className="px-3 py-3 text-gray-600">{item.avg_latency_ms.toFixed(0)} ms</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>

            <div className="rounded-lg border border-gray-200 bg-white px-4 py-3 text-xs text-gray-500">
              {data.notes.map((note) => <p key={note}>{note}</p>)}
            </div>
          </>
        )}
      </div>
    </>
  );
}

function Metric({ title, value }: { title: string; value: string }) {
  return (
    <Card>
      <CardContent className="pt-6">
        <p className="text-sm text-gray-500">{title}</p>
        <p className="mt-2 text-2xl font-semibold text-gray-900">{value}</p>
      </CardContent>
    </Card>
  );
}
