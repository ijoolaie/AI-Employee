"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ShoppingCart } from "lucide-react";
import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage } from "@/lib/errors";
import { getOrderSummary, listOrders, updateOrderStatus } from "@/lib/api";
import type { BusinessOrder } from "@/types";

const STATUSES = ["draft", "confirmed", "processing", "shipped", "delivered", "cancelled"] as const;

function money(v: string | number) {
  const n = typeof v === "string" ? Number(v) : v;
  return Number.isFinite(n) ? n.toLocaleString() : String(v);
}

function StatusBadge({ status }: { status: string }) {
  const tone =
    status === "delivered"
      ? "bg-emerald-50 text-emerald-700"
      : status === "cancelled"
        ? "bg-red-50 text-red-700"
        : status === "draft"
          ? "bg-gray-100 text-gray-700"
          : "bg-blue-50 text-blue-700";
  return <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${tone}`}>{status}</span>;
}

export default function OrdersPage() {
  const qc = useQueryClient();
  const ordersQ = useQuery({ queryKey: ["orders"], queryFn: () => listOrders() });
  const summaryQ = useQuery({ queryKey: ["orders-summary"], queryFn: getOrderSummary });

  const statusMut = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      updateOrderStatus(id, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["orders"] });
      qc.invalidateQueries({ queryKey: ["orders-summary"] });
    },
  });

  const orders = ordersQ.data ?? [];
  const summary = summaryQ.data;

  return (
    <>
      <Header
        title="Orders"
        description="Business orders created by the Order Employee or API."
      />
      <div className="space-y-6 p-6">
        {summaryQ.isLoading ? (
          <div className="flex justify-center py-8">
            <Spinner />
          </div>
        ) : summary ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Metric title="Total orders" value={String(summary.total_orders)} />
            {Object.entries(summary.counts_by_status || {}).map(([k, v]) => (
              <Metric key={k} title={k} value={String(v)} />
            ))}
          </div>
        ) : null}

        {ordersQ.isLoading ? (
          <div className="flex justify-center py-16">
            <Spinner />
          </div>
        ) : ordersQ.isError ? (
          <p className="text-sm text-red-600">{getErrorMessage(ordersQ.error)}</p>
        ) : orders.length === 0 ? (
          <EmptyState
            icon={ShoppingCart}
            title="No orders yet"
            description="Run the Order Employee or create orders via API to see them here."
          />
        ) : (
          <Card>
            <CardContent className="overflow-x-auto p-0">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-gray-100 text-xs uppercase text-gray-500">
                    <th className="px-4 py-3 font-medium">Number</th>
                    <th className="px-4 py-3 font-medium">Customer</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3 font-medium">Total</th>
                    <th className="px-4 py-3 font-medium">Date</th>
                    <th className="px-4 py-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map((o: BusinessOrder) => (
                    <tr key={o.id} className="border-b border-gray-50">
                      <td className="px-4 py-3 font-mono text-xs text-gray-900">{o.number}</td>
                      <td className="px-4 py-3 text-gray-800">{o.customer_name}</td>
                      <td className="px-4 py-3">
                        <StatusBadge status={o.status} />
                      </td>
                      <td className="px-4 py-3 text-gray-800">
                        {money(o.total)} {o.currency}
                      </td>
                      <td className="px-4 py-3 text-gray-500">{o.order_date}</td>
                      <td className="px-4 py-3">
                        <select
                          className="rounded border border-gray-200 bg-white px-2 py-1 text-xs"
                          value={o.status}
                          disabled={statusMut.isPending}
                          onChange={(e) =>
                            statusMut.mutate({ id: o.id, status: e.target.value })
                          }
                        >
                          {STATUSES.map((s) => (
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
        {statusMut.isError && (
          <p className="text-sm text-red-600">{getErrorMessage(statusMut.error)}</p>
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
