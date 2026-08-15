"use client";

import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage, getValidationSummary } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, MessageSquare, Star, Users, XCircle } from "lucide-react";

export default function ValidationDashboardPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-validation"],
    queryFn: getValidationSummary,
    refetchInterval: 30000,
  });

  return (
    <>
      <Header
        title="Phase 3 — Validation"
        description="03_Roadmap_v1.1 §6 exit criteria: ≥3 active customers regularly using the Report Employee, with recorded feedback"
      />
      <div className="space-y-6 p-6">
        {isLoading && <Spinner />}
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {getErrorMessage(error)}
          </div>
        )}
        {data && (
          <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Stat
                icon={Users}
                label="Active tenants (14d)"
                value={`${data.active_tenant_count} / ${data.phase3_customer_target}`}
                hint="Tenants with ≥1 Report Employee Run in the last 14 days"
              />
              <Stat
                icon={data.meets_phase3_customer_criteria ? CheckCircle2 : XCircle}
                label="Phase 3 customer target"
                value={data.meets_phase3_customer_criteria ? "Met" : "Not yet met"}
                hint="Quantitative proxy only — see note below"
              />
              <Stat
                icon={MessageSquare}
                label="Feedback recorded"
                value={data.total_feedback_count.toLocaleString()}
                hint="Across all tenants"
              />
              <Stat
                icon={Star}
                label="Average rating"
                value={data.overall_avg_rating != null ? data.overall_avg_rating.toFixed(1) : "—"}
                hint="1–5 scale"
              />
            </div>

            <Card>
              <CardHeader><CardTitle>Tenant activity</CardTitle></CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-gray-100 text-xs uppercase text-gray-500">
                        <th className="px-5 py-3 font-medium">Tenant</th>
                        <th className="px-5 py-3 font-medium">Runs (14d)</th>
                        <th className="px-5 py-3 font-medium">Runs (total)</th>
                        <th className="px-5 py-3 font-medium">Last run</th>
                        <th className="px-5 py-3 font-medium">Feedback</th>
                        <th className="px-5 py-3 font-medium">Avg rating</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.tenants.map((t) => (
                        <tr key={t.tenant_id} className="border-b border-gray-50">
                          <td className="px-5 py-3 font-medium text-gray-900">{t.tenant_name}</td>
                          <td className="px-5 py-3">
                            {t.report_employee_runs_last_14d > 0 ? (
                              <Badge status="active" />
                            ) : (
                              <span className="text-gray-400">0</span>
                            )}
                            {t.report_employee_runs_last_14d > 0 && (
                              <span className="ml-2 text-gray-600">{t.report_employee_runs_last_14d}</span>
                            )}
                          </td>
                          <td className="px-5 py-3 text-gray-600">{t.report_employee_runs_total}</td>
                          <td className="px-5 py-3 text-gray-600">{t.last_run_at ? formatDate(t.last_run_at) : "—"}</td>
                          <td className="px-5 py-3 text-gray-600">{t.feedback_count}</td>
                          <td className="px-5 py-3 text-gray-600">{t.avg_rating != null ? t.avg_rating.toFixed(1) : "—"}</td>
                        </tr>
                      ))}
                      {data.tenants.length === 0 && (
                        <tr>
                          <td colSpan={6} className="px-5 py-6 text-center text-gray-500">
                            No tenants yet.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle>Recent feedback</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {data.recent_feedback.length === 0 ? (
                  <p className="text-sm text-gray-500">No feedback recorded yet.</p>
                ) : (
                  data.recent_feedback.map((f) => (
                    <div key={f.id} className="rounded-lg border border-gray-100 p-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1">
                          {[1, 2, 3, 4, 5].map((n) => (
                            <Star
                              key={n}
                              className={`h-3.5 w-3.5 ${n <= f.rating ? "fill-amber-400 text-amber-400" : "text-gray-300"}`}
                            />
                          ))}
                        </div>
                        <span className="text-xs text-gray-400">{formatDate(f.created_at)}</span>
                      </div>
                      {f.comment && <p className="mt-2 text-sm text-gray-700">{f.comment}</p>}
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            <p className="text-xs text-gray-400">
              This dashboard tracks the Roadmap&apos;s own Phase 3 Definition of Done
              (03_Roadmap_v1.1.docx §6): it is a quantitative proxy for &quot;active customers
              regularly using the Report Employee&quot;, not a substitute for reading the
              actual feedback text and judging quality. Phase 3 completion is a product
              decision, not an automatic status flip.
            </p>
          </>
        )}
      </div>
    </>
  );
}

function Stat({
  icon: Icon,
  label,
  value,
  hint,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <Card>
      <CardContent className="flex items-start gap-4">
        <div className="rounded-lg bg-brand-50 p-2.5">
          <Icon className="h-5 w-5 text-brand-600" />
        </div>
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="mt-0.5 text-2xl font-semibold text-gray-900">{value}</p>
          <p className="text-xs text-gray-400">{hint}</p>
        </div>
      </CardContent>
    </Card>
  );
}
