"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { ShoppingCart, RefreshCw, ArrowLeft } from "lucide-react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { Button } from "@/components/ui/button";
import { getErrorMessage } from "@/lib/errors";
import { formatDate } from "@/lib/utils";
import { getOrder, getOrderSummary, listOrders, updateOrderStatus } from "@/lib/api";
import type { BusinessOrder } from "@/types";
import { useI18n } from "@/lib/i18n/provider";

const STATUSES = ["draft", "confirmed", "processing", "shipped", "delivered", "cancelled"] as const;
function money(v: string | number) {
  const n = typeof v === "string" ? Number(v) : v;
  return Number.isFinite(n) ? n.toLocaleString() : String(v);
}

export default function OrdersPage() {
  const qc = useQueryClient();
  const router = useRouter();
  const searchParams = useSearchParams();
  const orderId = searchParams.get("order");
  const { t } = useI18n();
  const m = t.commerce.orders;

  const ordersQ = useQuery({ queryKey: ["orders"], queryFn: () => listOrders() });
  const summaryQ = useQuery({ queryKey: ["orders-summary"], queryFn: getOrderSummary });
  const orderQ = useQuery({
    queryKey: ["order", orderId],
    queryFn: () => getOrder(orderId as string),
    enabled: Boolean(orderId),
  });

  const statusMut = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => updateOrderStatus(id, status),
    onSuccess: (updated) => {
      qc.setQueryData(["order", updated.id], updated);
      qc.invalidateQueries({ queryKey: ["orders"] });
      qc.invalidateQueries({ queryKey: ["orders-summary"] });
    },
  });

  const orders = ordersQ.data ?? [];
  const permissionDenied = [ordersQ.error, summaryQ.error].filter(Boolean).some((err) =>
    getErrorMessage(err).toLowerCase().includes("permission")
  );

  if (orderId) {
    return (
      <>
        <Header title={m.detailTitle} description={orderQ.data?.number ?? m.description} />
        <div className="space-y-6 p-6">
          <OrderDetail
            orderQ={orderQ}
            m={m}
            qc={qc}
            onBack={() => router.push("/orders")}
          />
        </div>
      </>
    );
  }

  const retry = () => {
    void ordersQ.refetch();
    void summaryQ.refetch();
  };

  return (
    <>
      <Header title={m.title} description={m.description} />
      <div className="space-y-6 p-6">
        {permissionDenied && (
          <div role="alert" className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
            {m.permissionDenied}
          </div>
        )}
        {summaryQ.isLoading ? (
          <div className="flex justify-center py-8"><Spinner /></div>
        ) : summaryQ.isError ? (
          <div className="flex items-center justify-between rounded-lg border p-4 text-sm">
            <span className="text-red-600">{permissionDenied ? m.permissionDenied : m.summaryError}</span>
            {!permissionDenied && (
              <Button variant="outline" size="sm" onClick={() => void summaryQ.refetch()}>
                <RefreshCw className="h-4 w-4" />{m.retry}
              </Button>
            )}
          </div>
        ) : summaryQ.data ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Metric title={m.total} value={String(summaryQ.data.total_orders)} />
            {Object.entries(summaryQ.data.counts_by_status || {}).map(([k, v]) => (
              <Metric key={k} title={m.statuses[k as keyof typeof m.statuses] ?? k} value={String(v)} />
            ))}
          </div>
        ) : null}

        {ordersQ.isLoading ? (
          <div className="flex justify-center py-16"><Spinner /></div>
        ) : ordersQ.isError ? (
          <div className="flex flex-col items-center gap-3 p-12 text-center">
            <p role="alert" className="text-sm text-red-600">{permissionDenied ? m.permissionDenied : m.error}</p>
            {!permissionDenied && (
              <Button variant="outline" onClick={retry} disabled={ordersQ.isFetching}>
                <RefreshCw className="h-4 w-4" />{m.retry}
              </Button>
            )}
          </div>
        ) : orders.length === 0 ? (
          <EmptyState icon={ShoppingCart} title={m.emptyTitle} description={m.emptyDescription} />
        ) : (
          <Card>
            <CardContent className="overflow-x-auto p-0">
              <table className="w-full text-start text-sm">
                <thead><tr className="border-b border-gray-100 text-xs uppercase text-gray-500">
                  <th className="px-4 py-3 font-medium">{m.number}</th>
                  <th className="px-4 py-3 font-medium">{m.customer}</th>
                  <th className="px-4 py-3 font-medium">{m.status}</th>
                  <th className="px-4 py-3 font-medium">{m.totalAmount}</th>
                  <th className="px-4 py-3 font-medium">{m.date}</th>
                  <th className="px-4 py-3 font-medium">{m.actions}</th>
                </tr></thead>
                <tbody>{orders.map((o: BusinessOrder) => (
                  <tr key={o.id} className="border-b border-gray-50">
                    <td className="px-4 py-3 font-mono text-xs">
                      <button type="button" className="text-brand-700 hover:underline" onClick={() => router.push("/orders?order=" + encodeURIComponent(o.id))}>{o.number}</button>
                    </td>
                    <td className="px-4 py-3 text-gray-800">{o.customer_name}</td>
                    <td className="px-4 py-3"><span className="rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">{m.statuses[o.status as keyof typeof m.statuses] ?? o.status}</span></td>
                    <td className="px-4 py-3 text-gray-800">{money(o.total)} {o.currency}</td>
                    <td className="px-4 py-3 text-gray-500">{o.order_date}</td>
                    <td className="px-4 py-3">
                      <select className="rounded border border-gray-200 bg-white px-2 py-1 text-xs" value={o.status} disabled={statusMut.isPending} onChange={e => statusMut.mutate({ id: o.id, status: e.target.value })} aria-label={m.status}>
                        {STATUSES.map(s => <option key={s} value={s}>{m.statuses[s]}</option>)}
                      </select>
                    </td>
                  </tr>
                ))}</tbody>
              </table>
            </CardContent>
          </Card>
        )}
        {statusMut.isError && (
          <p role="alert" className="text-sm text-red-600">
            {getErrorMessage(statusMut.error).toLowerCase().includes("permission") ? m.permissionDenied : m.updateError}
          </p>
        )}
      </div>
    </>
  );
}

function OrderDetail({ orderQ, m, qc, onBack }: {
  orderQ: { data?: BusinessOrder; isLoading: boolean; isError: boolean; error: unknown };
  m: any;
  qc: any;
  onBack: () => void;
}) {
  const order = orderQ.data;
  const statusMut = useMutation({
    mutationFn: (status: string) => updateOrderStatus(order!.id, status),
    onSuccess: (updated) => {
      qc.setQueryData(["order", updated.id], updated);
      qc.invalidateQueries({ queryKey: ["orders"] });
      qc.invalidateQueries({ queryKey: ["orders-summary"] });
    },
  });

  const permissionDenied = getErrorMessage((orderQ.error ?? statusMut.error) as Error).toLowerCase().includes("permission");

  if (orderQ.isLoading) return <div className="flex justify-center py-16"><Spinner /></div>;
  if (orderQ.isError || !order) {
    return (
      <Card><CardContent className="space-y-3 p-6">
        <p role="alert" className="text-sm text-red-600">{permissionDenied ? m.permissionDenied : m.error}</p>
        <button type="button" onClick={onBack} className="inline-flex items-center gap-2 text-sm text-brand-700 hover:underline"><ArrowLeft className="h-4 w-4" />{m.back}</button>
      </CardContent></Card>
    );
  }

  return (
    <div className="space-y-5">
      <button type="button" onClick={onBack} className="inline-flex items-center gap-2 text-sm text-brand-700 hover:underline"><ArrowLeft className="h-4 w-4" />{m.back}</button>
      <div className="grid gap-5 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>{order.number}</CardTitle></CardHeader>
          <CardContent className="space-y-5">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label={m.customer} value={order.customer_name} />
              <Field label={m.email} value={order.customer_email ?? m.noValue} />
              <Field label={m.date} value={formatDate(order.order_date)} />
              <Field label={m.deliveryDate} value={order.requested_delivery_date ? formatDate(order.requested_delivery_date) : m.noValue} />
              <Field label={m.subtotal} value={money(order.subtotal) + " " + order.currency} />
              <Field label={m.tax} value={money(order.tax_amount) + " " + order.currency} />
              <Field label={m.totalAmount} value={money(order.total) + " " + order.currency} />
              <Field label={m.taxRate} value={String(order.tax_rate) + "%"} />
              <Field label={m.createdAt} value={formatDate(order.created_at)} />
              <Field label={m.updatedAt} value={formatDate(order.updated_at)} />
            </div>
            <div>
              <p className="text-xs font-medium text-slate-500">{m.lineItems}</p>
              <div className="mt-2 overflow-x-auto rounded border">
                <table className="w-full text-sm">
                  <thead><tr className="border-b text-start text-xs text-slate-500"><th className="px-3 py-2">{m.item}</th><th className="px-3 py-2">{m.quantity}</th><th className="px-3 py-2">{m.unitPrice}</th><th className="px-3 py-2">{m.amount}</th></tr></thead>
                  <tbody>{order.line_items.map((item, index) => <tr key={item.sku ?? index} className="border-b last:border-0"><td className="px-3 py-2">{item.description}</td><td className="px-3 py-2">{item.quantity}</td><td className="px-3 py-2">{money(item.unit_price)}</td><td className="px-3 py-2">{item.amount == null ? "—" : money(item.amount)}</td></tr>)}</tbody>
                </table>
              </div>
            </div>
            <Field label={m.notes} value={order.notes ?? m.noValue} />
            <Field label={m.invoice} value={order.invoice_id ?? m.noValue} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>{m.status}</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <select className="w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm" value={order.status} disabled={statusMut.isPending} onChange={e => statusMut.mutate(e.target.value)} aria-label={m.status}>
              {STATUSES.map(s => <option key={s} value={s}>{m.statuses[s]}</option>)}
            </select>
            {statusMut.isError && <p role="alert" className="text-sm text-red-600">{permissionDenied ? m.permissionDenied : m.updateError}</p>}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Metric({ title, value }: { title: string; value: string }) {
  return <Card><CardContent className="pt-6"><p className="text-sm text-gray-500">{title}</p><p className="mt-2 text-2xl font-semibold text-gray-900">{value}</p></CardContent></Card>;
}
function Field({ label, value }: { label: string; value: string }) {
  return <div><p className="text-xs font-medium text-slate-500">{label}</p><p className="mt-1 break-words text-sm text-slate-900">{value}</p></div>;
}
