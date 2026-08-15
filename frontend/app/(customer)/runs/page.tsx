"use client";

import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage, listRuns } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { Play } from "lucide-react";
import Link from "next/link";

export default function RunsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["runs"],
    queryFn: () => listRuns(),
  });

  const runs = [...(data ?? [])].sort(
    (a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  return (
    <>
      <Header
        title="Runs"
        description="Execution history across all employees"
      />
      <div className="p-6">
        {isLoading && <Spinner />}
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {getErrorMessage(error)}
          </div>
        )}
        {!isLoading && !error && runs.length === 0 && (
          <EmptyState
            icon={Play}
            title="No runs yet"
            description="Start a run from an employee page."
          />
        )}
        {!isLoading && runs.length > 0 && (
          <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50/50 text-xs uppercase text-gray-500">
                  <th className="px-5 py-3 font-medium">Run ID</th>
                  <th className="px-5 py-3 font-medium">Employee</th>
                  <th className="px-5 py-3 font-medium">Status</th>
                  <th className="px-5 py-3 font-medium">Tokens</th>
                  <th className="px-5 py-3 font-medium">Cost</th>
                  <th className="px-5 py-3 font-medium">Created</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr
                    key={run.id}
                    className="border-b border-gray-50 hover:bg-gray-50/50"
                  >
                    <td className="px-5 py-3">
                      <Link
                        href={`/runs/${run.id}`}
                        className="font-medium text-brand-600 hover:underline"
                      >
                        {run.id.slice(0, 8)}…
                      </Link>
                    </td>
                    <td className="px-5 py-3">
                      <Link
                        href={`/employees/${run.employee_id}`}
                        className="text-gray-600 hover:text-brand-600"
                      >
                        {run.employee_name || run.employee_slug || `${run.employee_id.slice(0, 8)}…`}
                      </Link>
                    </td>
                    <td className="px-5 py-3">
                      <Badge status={run.status} />
                    </td>
                    <td className="px-5 py-3 text-gray-600">
                      {run.total_tokens.toLocaleString()}
                    </td>
                    <td className="px-5 py-3 text-gray-600">
                      {formatCurrency(run.total_cost_usd)}
                    </td>
                    <td className="px-5 py-3 text-gray-500">
                      {formatDate(run.created_at)}
                    </td>
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
