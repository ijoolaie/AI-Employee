"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ShoppingCart } from "lucide-react";
import { Header } from "@/components/layout/header";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage } from "@/lib/errors";
import { getOrderSummary, listOrders, updateOrderStatus } from "@/lib/api";
import type { BusinessOrder } from "@/types";
import { useI18n } from "@/lib/i18n/provider";

const STATUSES = ["draft", "confirmed", "processing", "shipped", "delivered", "cancelled"] as const;
function money(v: string | number) { const n = typeof v === "string" ? Number(v) : v; return Number.isFinite(n) ? n.toLocaleString() : String(v); }

export default function OrdersPage() {
  const qc = useQueryClient();
  const { t } = useI18n();
  const m = t.commerce.orders;
  const ordersQ = useQuery({ queryKey: ["orders"], queryFn: () => listOrders() });
  const summaryQ = useQuery({ queryKey: ["orders-summary"], queryFn: getOrderSummary });
  const statusMut = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => updateOrderStatus(id, status),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["orders"] }); qc.invalidateQueries({ queryKey: ["orders-summary"] }); },
  });
  const orders = ordersQ.data ?? [];
  const permissionDenied = [ordersQ.error, summaryQ.error].filter(Boolean).some(err => getErrorMessage(err).toLowerCase().includes("permission"));

  return (
    <>
      <Header title={m.title} description={m.description} />
      <div className="space-y-6 p-6">
        {permissionDenied && <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">{m.permissionDenied}</div>}
        {summaryQ.isLoading ? <div className="flex justify-center py-8"><Spinner /></div> :
          summaryQ.isError ? null : summaryQ.data ? <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Metric title={m.total} value={String(summaryQ.data.total_orders)} />
            {Object.entries(summaryQ.data.counts_by_status || {}).map(([k, v]) => <Metric key={k} title={k} value={String(v)} />)}
          </div> : null}
        {ordersQ.isLoading ? <div className="flex justify-center py-16"><Spinner /></div> :
          ordersQ.isError ? <p className="text-sm text-red-600">{permissionDenied ? m.permissionDenied : m.error}</p> :
          orders.length === 0 ? <EmptyState icon={ShoppingCart} title={m.emptyTitle} description={m.emptyDescription} /> :
          <Card><CardContent className="overflow-x-auto p-0">
            <table className="w-full text-left text-sm"><thead><tr className="border-b border-gray-100 text-xs uppercase text-gray-500">
              <th className="px-4 py-3 font-medium">{m.number}</th><th className="px-4 py-3 font-medium">{m.customer}</th><th className="px-4 py-3 font-medium">{m.status}</th><th className="px-4 py-3 font-medium">{m.totalAmount}</th><th className="px-4 py-3 font-medium">{m.date}</th><th className="px-4 py-3 font-medium">{m.actions}</th>
            </tr></thead><tbody>{orders.map((o: BusinessOrder) => <tr key={o.id} className="border-b border-gray-50">
              <td className="px-4 py-3 font-mono text-xs text-gray-900">{o.number}</td><td className="px-4 py-3 text-gray-800">{o.customer_name}</td>
              <td className="px-4 py-3"><span className="rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">{m.statuses[o.status as keyof typeof m.statuses]}</span></td>
              <td className="px-4 py-3 text-gray-800">{money(o.total)} {o.currency}</td><td className="px-4 py-3 text-gray-500">{o.order_date}</td>
              <td className="px-4 py-3"><select className="rounded border border-gray-200 bg-white px-2 py-1 text-xs" value={o.status} disabled={statusMut.isPending} onChange={e => statusMut.mutate({ id: o.id, status: e.target.value })} aria-label={m.status}>
                {STATUSES.map(s => <option key={s} value={s}>{m.statuses[s]}</option>)}
              </select></td>
            </tr>)}</tbody></table>
          </CardContent></Card>}
        {statusMut.isError && <p className="text-sm text-red-600">{getErrorMessage(statusMut.error).toLowerCase().includes("permission") ? m.permissionDenied : m.updateError}</p>}
      </div>
    </>
  );
}
function Metric({ title, value }: { title: string; value: string }) { return <Card><CardContent className="pt-6"><p className="text-sm text-gray-500">{title}</p><p className="mt-2 text-2xl font-semibold text-gray-900">{value}</p></CardContent></Card>; }
