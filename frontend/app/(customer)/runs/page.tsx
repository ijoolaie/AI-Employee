"use client";

import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage, listRuns } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { useI18n } from "@/lib/i18n/provider";
import { Play } from "lucide-react";
import Link from "next/link";

function isPermissionError(error: unknown) {
  const message = getErrorMessage(error).toLowerCase();
  return message.includes("permission") || message.includes("403") || message.includes("forbidden");
}

export default function RunsPage() {
  const { t: m } = useI18n();
  const query = useQuery({ queryKey: ["runs"], queryFn: () => listRuns() });
  const runs = [...(query.data ?? [])].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );
  const permissionDenied = query.isError && isPermissionError(query.error);

  return (
    <>
      <Header title={m.runs.title} description={m.runs.description} />
      <div className="mx-auto max-w-7xl space-y-6 p-4 sm:p-6" dir="auto">
        {permissionDenied ? (
          <EmptyState icon={Play} title={m.runs.permissionDenied} description={m.runs.permissionDescription} />
        ) : query.isLoading ? (
          <div className="flex items-center gap-2"><Spinner /><span>{m.runs.loading}</span></div>
        ) : query.isError ? (
          <div className="space-y-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            <p>{getErrorMessage(query.error)}</p>
            <Button variant="outline" onClick={() => query.refetch()}>{m.runs.retry}</Button>
          </div>
        ) : runs.length === 0 ? (
          <EmptyState icon={Play} title={m.runs.emptyTitle} description={m.runs.emptyDescription} />
        ) : (
          <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
            <table className="min-w-[820px] w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50/50 text-xs text-gray-500">
                  <th className="px-5 py-3 text-start font-medium">{m.runs.runId}</th>
                  <th className="px-5 py-3 text-start font-medium">{m.runs.employee}</th>
                  <th className="px-5 py-3 text-start font-medium">{m.runs.status}</th>
                  <th className="px-5 py-3 text-start font-medium">{m.runs.tokens}</th>
                  <th className="px-5 py-3 text-start font-medium">{m.runs.cost}</th>
                  <th className="px-5 py-3 text-start font-medium">{m.runs.created}</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr key={run.id} className="border-b border-gray-50 hover:bg-gray-50/50">
                    <td className="px-5 py-3">
                      <Link href={`/runs/${run.id}`} className="font-medium text-brand-600 hover:underline">
                        {run.id.slice(0, 8)}…
                      </Link>
                    </td>
                    <td className="px-5 py-3">
                      <Link href={`/employees/${run.employee_id}`} className="text-gray-600 hover:text-brand-600">
                        {run.employee_name || run.employee_slug || `${run.employee_id.slice(0, 8)}…`}
                      </Link>
                    </td>
                    <td className="px-5 py-3"><Badge status={run.status} /></td>
                    <td className="px-5 py-3 text-gray-600">{run.total_tokens.toLocaleString()}</td>
                    <td className="px-5 py-3 text-gray-600">{formatCurrency(run.total_cost_usd)}</td>
                    <td className="px-5 py-3 text-gray-500">{formatDate(run.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
