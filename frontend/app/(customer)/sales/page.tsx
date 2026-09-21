"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { TrendingUp } from "lucide-react";
import { Header } from "@/components/layout/header";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage } from "@/lib/errors";
import { getSalesForecast, getSalesPipeline, listDeals, updateDealStage } from "@/lib/api";
import type { BusinessDeal } from "@/types";
import { useI18n } from "@/lib/i18n/provider";

const STAGES = ["lead", "qualified", "proposal", "negotiation", "won", "lost"] as const;
function money(v: string | number) { const n = typeof v === "string" ? Number(v) : v; return Number.isFinite(n) ? n.toLocaleString() : String(v); }

export default function SalesPage() {
  const qc = useQueryClient();
  const { t } = useI18n();
  const m = t.commerce.sales;
  const dealsQ = useQuery({ queryKey: ["deals"], queryFn: () => listDeals() });
  const pipeQ = useQuery({ queryKey: ["sales-pipeline"], queryFn: getSalesPipeline });
  const forecastQ = useQuery({ queryKey: ["sales-forecast"], queryFn: () => getSalesForecast(30) });
  const stageMut = useMutation({
    mutationFn: ({ id, stage }: { id: string; stage: string }) => updateDealStage(id, stage),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["deals"] }); qc.invalidateQueries({ queryKey: ["sales-pipeline"] }); qc.invalidateQueries({ queryKey: ["sales-forecast"] }); },
  });
  const deals = dealsQ.data ?? [];
  const permissionDenied = [dealsQ.error, pipeQ.error, forecastQ.error].filter(Boolean).some(err => getErrorMessage(err).toLowerCase().includes("permission"));

  return (
    <>
      <Header title={m.title} description={m.description} />
      <div className="space-y-6 p-6">
        {permissionDenied && <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">{m.permissionDenied}</div>}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {pipeQ.isLoading || forecastQ.isLoading ? <div className="col-span-full flex justify-center py-6"><Spinner /></div> :
            pipeQ.isError ? null : pipeQ.data ? <>
              <Metric title={m.openDeals} value={String(pipeQ.data.open_deals)} />
              <Metric title={m.weightedPipeline} value={money(pipeQ.data.weighted_pipeline) + " " + pipeQ.data.currency} />
              <Metric title={m.won} value={money(pipeQ.data.won_amount) + " " + pipeQ.data.currency} />
              <Metric title={m.forecast} value={forecastQ.data ? money(forecastQ.data.expected_revenue) + " " + forecastQ.data.currency : "—"} />
            </> : null}
        </div>
        {dealsQ.isLoading ? <div className="flex justify-center py-16"><Spinner /></div> :
          dealsQ.isError ? <p className="text-sm text-red-600">{permissionDenied ? m.permissionDenied : m.error}</p> :
          deals.length === 0 ? <EmptyState icon={TrendingUp} title={m.emptyTitle} description={m.emptyDescription} /> :
          <Card><CardContent className="overflow-x-auto p-0">
            <table className="w-full text-left text-sm"><thead><tr className="border-b border-gray-100 text-xs uppercase text-gray-500">
              <th className="px-4 py-3 font-medium">{m.titleColumn}</th><th className="px-4 py-3 font-medium">{m.customer}</th><th className="px-4 py-3 font-medium">{m.stage}</th><th className="px-4 py-3 font-medium">{m.amount}</th><th className="px-4 py-3 font-medium">{m.probability}</th><th className="px-4 py-3 font-medium">{m.actions}</th>
            </tr></thead><tbody>{deals.map((d: BusinessDeal) => <tr key={d.id} className="border-b border-gray-50">
              <td className="px-4 py-3 font-medium"><Link className="text-brand-700 hover:underline" href={"/sales/deals/" + d.id}>{d.title}</Link></td>
              <td className="px-4 py-3 text-gray-700">{d.customer_name}</td><td className="px-4 py-3"><span className="rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700">{d.stage}</span></td>
              <td className="px-4 py-3 text-gray-800">{money(d.amount)} {d.currency}</td><td className="px-4 py-3 text-gray-600">{d.probability}%</td>
              <td className="px-4 py-3"><select className="rounded border border-gray-200 bg-white px-2 py-1 text-xs" value={d.stage} disabled={stageMut.isPending} onChange={e => stageMut.mutate({ id: d.id, stage: e.target.value })} aria-label={m.stage}>
                {STAGES.map(s => <option key={s} value={s}>{s}</option>)}
              </select></td>
            </tr>)}</tbody></table>
          </CardContent></Card>}
        {stageMut.isError && <p className="text-sm text-red-600">{getErrorMessage(stageMut.error).toLowerCase().includes("permission") ? m.permissionDenied : m.updateError}</p>}
      </div>
    </>
  );
}
function Metric({ title, value }: { title: string; value: string }) { return <Card><CardContent className="pt-6"><p className="text-sm text-gray-500">{title}</p><p className="mt-2 text-xl font-semibold text-gray-900">{value}</p></CardContent></Card>; }
