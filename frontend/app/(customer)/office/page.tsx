"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Building2, CheckCircle2, Clock3, DoorOpen, ShieldCheck, UserRound, Users, AlertTriangle } from "lucide-react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Button } from "@/components/ui/button";
import { getCustomerOffice, getErrorMessage } from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";

const stateClass: Record<string, string> = {
  WORKING: "border-emerald-200 bg-emerald-50 text-emerald-700",
  WAITING_APPROVAL: "border-amber-200 bg-amber-50 text-amber-700",
  IDLE: "border-slate-200 bg-slate-50 text-slate-600",
  BLOCKED: "border-red-200 bg-red-50 text-red-700",
  MEETING: "border-blue-200 bg-blue-50 text-blue-700",
  COMPLETED: "border-indigo-200 bg-indigo-50 text-indigo-700",
  ESCALATED: "border-orange-200 bg-orange-50 text-orange-700",
};

export default function OfficePage() {
  const { t } = useI18n();
  const tx = t.office;
  const q = useQuery({
    queryKey: ["customer-office"],
    queryFn: getCustomerOffice,
    refetchInterval: 5000,
  });
  const data = q.data;

  return (
    <>
      <Header title={tx.title} description={tx.description} />
      <div className="space-y-6 p-6">
        {q.isLoading && <Spinner />}
        {q.error && (
          <div role="alert" className="flex items-center justify-between gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            <span>{getErrorMessage(q.error)}</span>
            <Button variant="outline" size="sm" onClick={() => void q.refetch()}>{tx.retry}</Button>
          </div>
        )}

        {data && (
          <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
              <Metric icon={Users} label={tx.employees} value={data.employee_count} />
              <Metric icon={CheckCircle2} label={tx.working} value={data.working_count} />
              <Metric icon={Clock3} label={tx.waiting} value={data.waiting_count} />
              <Metric icon={DoorOpen} label={tx.idle} value={data.idle_count} />
              <Metric icon={AlertTriangle} label={tx.escalated} value={data.escalated_count + data.blocked_count} />
            </div>

            <div className="overflow-hidden rounded-2xl border border-slate-200 bg-slate-950 shadow-xl">
              <div className="border-b border-white/10 bg-slate-900 px-6 py-4 text-white">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Building2 className="h-5 w-5" />
                    <div>
                      <h2 className="font-semibold">{tx.officeFloor}</h2>
                      <p className="text-xs text-slate-400">{data.employee_count} {tx.employees.toLowerCase()}</p>
                    </div>
                  </div>
                  <span className="inline-flex items-center gap-2 rounded-full bg-emerald-400/10 px-3 py-1 text-xs font-medium text-emerald-300">
                    <span className="h-2 w-2 rounded-full bg-emerald-400" />
                    {tx.live}
                  </span>
                </div>
              </div>

              <div className="grid gap-6 p-6 lg:grid-cols-[minmax(0,1fr)_280px]">
                <div className="min-h-[430px] rounded-2xl border border-white/10 bg-gradient-to-br from-slate-800 via-slate-900 to-slate-950 p-6">
                  <div className="mb-6 flex items-center gap-3 rounded-xl border border-amber-300/20 bg-amber-200/5 p-4">
                    <div className="rounded-lg bg-amber-200/10 p-2"><ShieldCheck className="h-5 w-5 text-amber-200" /></div>
                    <div>
                      <p className="text-sm font-semibold text-white">{tx.executiveDesk}</p>
                      <p className="text-xs text-slate-400">{tx.approvalsDescription}</p>
                    </div>
                  </div>

                  {data.employees.length === 0 ? (
                    <div className="flex min-h-[280px] items-center justify-center text-center text-sm text-slate-400">{tx.empty}</div>
                  ) : (
                    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                      {data.employees.map((employee) => (
                        <Link key={employee.id} href={`/employees/${employee.id}`} className="group">
                          <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-4 transition hover:-translate-y-1 hover:border-white/20 hover:bg-white/[0.07]">
                            <div className="flex items-start justify-between gap-3">
                              <Avatar name={employee.name} url={employee.avatar_url} />
                              <span className={`rounded-full border px-2 py-1 text-[10px] font-semibold ${stateClass[employee.presentation_state] ?? stateClass.IDLE}`}>
                                {employee.presentation_state.replaceAll("_", " ")}
                              </span>
                            </div>
                            <p className="mt-4 font-semibold text-white">{employee.name}</p>
                            <p className="mt-1 text-xs text-slate-400">{employee.kind} · {employee.slug}</p>
                            {employee.current_work_item && (
                              <div className="mt-4 rounded-xl border border-white/10 bg-black/10 p-3">
                                <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">{tx.currentTask}</p>
                                <p className="mt-1 line-clamp-2 text-xs font-medium text-slate-200">{employee.current_work_item.title}</p>
                                <p className="mt-1 text-[10px] text-slate-500">{employee.current_work_item.status}</p>
                              </div>
                            )}
                            <div className="mt-3 flex items-center justify-between text-[11px] text-slate-500">
                              <span>{tx.latestRun}</span>
                              <span>{employee.latest_run_id ? `#${employee.latest_run_id.slice(0, 8)}` : tx.noRun}</span>
                            </div>
                          </div>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>

                <Card className="border-white/10 bg-white/[0.04] text-white">
                  <CardHeader><CardTitle className="text-base">{tx.visualOnly}</CardTitle></CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-sm leading-6 text-slate-400">{tx.visualOnlyDescription}</p>
                    <div className="rounded-xl border border-white/10 bg-black/10 p-4">
                      <div className="flex items-center gap-3"><UserRound className="h-5 w-5 text-slate-300" /><div><p className="text-sm font-medium">{tx.state}</p><p className="text-xs text-slate-500">{data.office_state}</p></div></div>
                    </div>
                    <Link href="/approvals" className="block">
                      <Button variant="outline" className="w-full">{tx.approvals}</Button>
                    </Link>
                  </CardContent>
                </Card>
              </div>
            </div>
          </>
        )}
      </div>
    </>
  );
}

function Metric({ icon: Icon, label, value }: { icon: typeof Users; label: string; value: number }) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3">
        <div className="rounded-lg bg-brand-50 p-2.5"><Icon className="h-5 w-5 text-brand-600" /></div>
        <div><p className="text-xs text-slate-500">{label}</p><p className="text-xl font-semibold">{value}</p></div>
      </CardContent>
    </Card>
  );
}

function Avatar({ name, url }: { name: string; url: string | null }) {
  const initials = name.split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase();
  return url ? (
    <div className="h-12 w-12 overflow-hidden rounded-full border border-white/10 bg-slate-800" style={{ backgroundImage: `url("${url}")`, backgroundSize: "cover", backgroundPosition: "center" }} aria-label={name} />
  ) : (
    <div className="flex h-12 w-12 items-center justify-center rounded-full border border-white/10 bg-slate-800 text-sm font-semibold text-slate-200" aria-label={name}>{initials}</div>
  );
}
