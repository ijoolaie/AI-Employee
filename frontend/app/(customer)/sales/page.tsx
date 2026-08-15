"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { TrendingUp } from "lucide-react";
import { Header } from "@/components/layout/header";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage } from "@/lib/errors";
import {
  getSalesForecast,
  getSalesPipeline,
  listDeals,
  updateDealStage,
} from "@/lib/api";
import type { BusinessDeal } from "@/types";

const STAGES = ["lead", "qualified", "proposal", "negotiation", "won", "lost"] as const;

function money(v: string | number) {
  const n = typeof v === "string" ? Number(v) : v;
  return Number.isFinite(n) ? n.toLocaleString() : String(v);
}

function StageBadge({ stage }: { stage: string }) {
  const tone =
    stage === "won"
      ? "bg-emerald-50 text-emerald-700"
      : stage === "lost"
        ? "bg-red-50 text-red-700"
        : "bg-indigo-50 text-indigo-700";
  return <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${tone}`}>{stage}</span>;
}

export default function SalesPage() {
  const qc = useQueryClient();
  const dealsQ = useQuery({ queryKey: ["deals"], queryFn: () => listDeals() });
  const pipeQ = useQuery({ queryKey: ["sales-pipeline"], queryFn: getSalesPipeline });
  const forecastQ = useQuery({
    queryKey: ["sales-forecast"],
    queryFn: () => getSalesForecast(30),
  });

  const stageMut = useMutation({
    mutationFn: ({ id, stage }: { id: string; stage: string }) => updateDealStage(id, stage),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["deals"] });
      qc.invalidateQueries({ queryKey: ["sales-pipeline"] });
      qc.invalidateQueries({ queryKey: ["sales-forecast"] });
    },
  });

  const deals = dealsQ.data ?? [];
  const pipe = pipeQ.data;
  const forecast = forecastQ.data;

  return (
    <>
      <Header
        title="Sales"
        description="Deals and pipeline managed by the Sales Employee."
      />
      <div className="space-y-6 p-6">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {pipeQ.isLoading ? (
            <div className="col-span-full flex justify-center py-6">
              <Spinner />
            </div>
          ) : pipe ? (
            <>
              <Metric title="Open deals" value={String(pipe.open_deals)} />
              <Metric
                title="Weighted pipeline"
                value={`${money(pipe.weighted_pipeline)} ${pipe.currency}`}
              />
              <Metric title="Won" value={`${money(pipe.won_amount)} ${pipe.currency}`} />
              <Metric
                title="Forecast (30d)"
                value={
                  forecast
                    ? `${money(forecast.expected_revenue)} ${forecast.currency}`
                    : "—"
                }
              />
            </>
          ) : null}
        </div>

        {dealsQ.isLoading ? (
          <div className="flex justify-center py-16">
            <Spinner />
          </div>
        ) : dealsQ.isError ? (
          <p className="text-sm text-red-600">{getErrorMessage(dealsQ.error)}</p>
        ) : deals.length === 0 ? (
          <EmptyState
            icon={TrendingUp}
            title="No deals yet"
            description="Run the Sales Employee to create opportunities, or use the sales API."
          />
        ) : (
          <Card>
            <CardContent className="overflow-x-auto p-0">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-gray-100 text-xs uppercase text-gray-500">
                    <th className="px-4 py-3 font-medium">Title</th>
                    <th className="px-4 py-3 font-medium">Customer</th>
                    <th className="px-4 py-3 font-medium">Stage</th>
                    <th className="px-4 py-3 font-medium">Amount</th>
                    <th className="px-4 py-3 font-medium">Prob.</th>
                    <th className="px-4 py-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {deals.map((d: BusinessDeal) => (
                    <tr key={d.id} className="border-b border-gray-50">
                      <td className="px-4 py-3 font-medium"><Link className="text-brand-700 hover:underline" href={`/sales/deals/${d.id}`}>{d.title}</Link></td>
                      <td className="px-4 py-3 text-gray-700">{d.customer_name}</td>
                      <td className="px-4 py-3">
                        <StageBadge stage={d.stage} />
                      </td>
                      <td className="px-4 py-3 text-gray-800">
                        {money(d.amount)} {d.currency}
                      </td>
                      <td className="px-4 py-3 text-gray-600">{d.probability}%</td>
                      <td className="px-4 py-3">
                        <select
                          className="rounded border border-gray-200 bg-white px-2 py-1 text-xs"
                          value={d.stage}
                          disabled={stageMut.isPending}
                          onChange={(e) =>
                            stageMut.mutate({ id: d.id, stage: e.target.value })
                          }
                        >
                          {STAGES.map((s) => (
                            <option key={s} value={s}>
                              {s}
                            </option>
                          ))}
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        )}
        {stageMut.isError && (
          <p className="text-sm text-red-600">{getErrorMessage(stageMut.error)}</p>
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
        <p className="mt-2 text-xl font-semibold text-gray-900">{value}</p>
      </CardContent>
    </Card>
  );
}
