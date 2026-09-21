"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, Mail, Save } from "lucide-react";
import Link from "next/link";

import { Header } from "@/components/layout/header";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage } from "@/lib/errors";
import { getDeal, getSalesForecast, getSalesPipeline, listDeals, updateDealStage } from "@/lib/api";
import type { BusinessDeal } from "@/types";
import { useI18n } from "@/lib/i18n/provider";

const STAGES = ["lead", "qualified", "proposal", "negotiation", "won", "lost"] as const;
function money(v: string | number) { const n = typeof v === "string" ? Number(v) : v; return Number.isFinite(n) ? n.toLocaleString() : String(v); }

export default function SalesPage() {
  const qc = useQueryClient();
  const searchParams = useSearchParams();
  const router = useRouter();
  const dealId = searchParams.get("deal");
  const { t } = useI18n();
  const m = t.commerce.sales;
  const dealQ = useQuery({ queryKey: ["deal", dealId], queryFn: () => getDeal(dealId as string), enabled: Boolean(dealId) });
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
      <Header title={dealId ? m.detailTitle : m.title} description={dealId ? (dealQ.data?.title ?? m.description) : m.description} />
      <div className="space-y-6 p-6">
        {dealId ? <DealDetail dealQ={dealQ} m={m} qc={qc} onBack={() => router.push("/sales")} /> : <>
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
              <td className="px-4 py-3 font-medium"><Link className="text-brand-700 hover:underline" href={"/sales?deal=" + encodeURIComponent(d.id)}>{d.title}</Link></td>
              <td className="px-4 py-3 text-gray-700">{d.customer_name}</td><td className="px-4 py-3"><span className="rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700">{m.stages[d.stage as keyof typeof m.stages]}</span></td>
              <td className="px-4 py-3 text-gray-800">{money(d.amount)} {d.currency}</td><td className="px-4 py-3 text-gray-600">{d.probability}%</td>
              <td className="px-4 py-3"><select className="rounded border border-gray-200 bg-white px-2 py-1 text-xs" value={d.stage} disabled={stageMut.isPending} onChange={e => stageMut.mutate({ id: d.id, stage: e.target.value })} aria-label={m.stage}>
                {STAGES.map(s => <option key={s} value={s}>{m.stages[s]}</option>)}
              </select></td>
            </tr>)}</tbody></table>
          </CardContent></Card>}
        {stageMut.isError && <p className="text-sm text-red-600">{getErrorMessage(stageMut.error).toLowerCase().includes("permission") ? m.permissionDenied : m.updateError}</p>}
        </>}
      </div>
    </>
  );
}
function Metric({ title, value }: { title: string; value: string }) { return <Card><CardContent className="pt-6"><p className="text-sm text-gray-500">{title}</p><p className="mt-2 text-xl font-semibold text-gray-900">{value}</p></CardContent></Card>; }

function DealDetail({ dealQ, m, qc, onBack }: { dealQ: ReturnType<typeof useQuery<BusinessDeal>>; m: any; qc: ReturnType<typeof useQueryClient>; onBack: () => void }) {
  const deal = dealQ.data;
  const [stage, setStage] = useState<string | null>(null);
  const mutation = useMutation({
    mutationFn: (next: string) => updateDealStage(deal!.id, next),
    onSuccess: (updated) => { setStage(updated.stage); qc.setQueryData(["deal", deal!.id], updated); qc.invalidateQueries({ queryKey: ["deals"] }); qc.invalidateQueries({ queryKey: ["sales-pipeline"] }); qc.invalidateQueries({ queryKey: ["sales-forecast"] }); },
  });
  const permissionDenied = getErrorMessage(dealQ.error || mutation.error).toLowerCase().includes("permission");
  if (dealQ.isLoading) return <div className="flex justify-center py-16"><Spinner /></div>;
  if (dealQ.isError || !deal) return <Card><CardContent className="space-y-2 p-6"><p className="text-sm font-medium text-red-600">{permissionDenied ? m.permissionDenied : m.error}</p><p className="text-sm text-slate-500">{m.notFound}</p><button type="button" onClick={onBack} className="text-sm text-brand-700 hover:underline">{m.back}</button></CardContent></Card>;
  const selected = stage ?? deal.stage;
  return <div className="space-y-5"><button type="button" onClick={onBack} className="inline-flex items-center gap-2 text-sm text-brand-700 hover:underline"><ArrowLeft className="h-4 w-4"/>{m.back}</button><div className="grid gap-5 lg:grid-cols-3"><Card className="lg:col-span-2"><CardHeader><CardTitle>{deal.title}</CardTitle></CardHeader><CardContent className="grid gap-5 sm:grid-cols-2"><Field label={m.customer} value={deal.customer_name}/><Field label={m.email} value={deal.customer_email ?? m.noValue}/><Field label={m.detailAmount} value={money(deal.amount) + " " + deal.currency}/><Field label={m.detailProbability} value={deal.probability + "%"}/><Field label={m.expectedClose} value={deal.expected_close_date ? formatDate(deal.expected_close_date) : m.noValue}/><Field label={m.owner} value={deal.owner_name ?? m.noValue}/><Field label={m.source} value={deal.source ?? m.noValue}/><Field label={m.order} value={deal.order_id ?? m.noValue}/><Field label={m.createdAt} value={formatDate(deal.created_at)}/><Field label={m.updatedAt} value={formatDate(deal.updated_at)}/><div className="sm:col-span-2"><p className="text-xs font-medium text-slate-500">{m.notes}</p><p className="mt-1 whitespace-pre-wrap text-sm text-slate-800">{deal.notes ?? m.noValue}</p></div></CardContent></Card><Card><CardHeader><CardTitle>{m.detailStage}</CardTitle></CardHeader><CardContent className="space-y-4"><select className="w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm" value={selected} disabled={mutation.isPending} onChange={e => setStage(e.target.value)} aria-label={m.detailStage}>{STAGES.map(s => <option key={s} value={s}>{m.stages[s]}</option>)}</select><button type="button" className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50" disabled={mutation.isPending || selected === deal.stage} onClick={() => mutation.mutate(selected)}><Save className="h-4 w-4"/>{mutation.isPending ? m.saving : m.save}</button>{mutation.isError && <p className="text-sm text-red-600">{permissionDenied ? m.permissionDenied : m.updateError}</p>}{deal.customer_email && <a href={`mailto:${deal.customer_email}`} className="inline-flex items-center gap-2 text-sm text-brand-700 hover:underline"><Mail className="h-4 w-4"/>{deal.customer_email}</a>}</CardContent></Card></div></div>;
}
function Field({ label, value }: { label: string; value: string }) { return <div><p className="text-xs font-medium text-slate-500">{label}</p><p className="mt-1 break-words text-sm text-slate-900">{value}</p></div>; }
