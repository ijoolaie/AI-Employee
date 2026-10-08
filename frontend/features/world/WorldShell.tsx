"use client";

import Link from "next/link";
import { useCallback, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Building2, LayoutDashboard, Sparkles } from "lucide-react";
import { getCustomerOffice, getErrorMessage, getROIAnalytics } from "@/lib/api";
import { projectWorldReadModel } from "./WorldState";
import { MobileInputAdapter } from "./MobileInputAdapter";
import { WorldViewport } from "./WorldViewport";

export function WorldShell() {
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<string | null>(null);
  const roiQuery = useQuery({\n    queryKey: ["world-roi"],\n    queryFn: getROIAnalytics,\n    refetchInterval: 15000,\n    staleTime: 5000,\n  });\n  const query = useQuery({
    queryKey: ["customer-world-read-model"],
    queryFn: getCustomerOffice,
    refetchInterval: 5000,
    staleTime: 2000,
  });
  const world = useMemo(() => (query.data ? projectWorldReadModel(query.data) : null), [query.data]);
  const onEmployeeSelect = useCallback((id: string | null) => setSelectedEmployeeId(id), []);
  const selectedEmployee = world?.employees.find((employee) => employee.id === selectedEmployeeId) ?? null;

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto flex min-h-screen w-full max-w-[1600px] flex-col px-4 py-4 sm:px-6 lg:px-8">
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-cyan-500/30 bg-cyan-500/10">
              <Building2 className="h-5 w-5 text-cyan-300" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-cyan-300">AI Company HQ</p>
              <h1 className="text-lg font-semibold">World Mode</h1>
            </div>
          </div>
          <Link href="/dashboard" className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200 hover:bg-slate-800">
            <LayoutDashboard className="h-4 w-4" />
            Management Mode
          </Link>
        </header>

        <section className="flex flex-1 flex-col gap-5 py-5">
          <div>
            <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-cyan-500/20 bg-cyan-500/5 px-3 py-1 text-xs text-cyan-200">
              <Sparkles className="h-3.5 w-3.5" />
              F2 · Authoritative HQ projection
            </div>
            <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">Your real workforce, inside the HQ.</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              Employees and runtime states are projected from the existing tenant-scoped office read model. The World layer does not create or mutate business state.
            </p>
          </div>

          {query.isLoading && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 text-sm text-slate-400">Loading the authoritative HQ state…</div>
          )}
          {query.error && (
            <div role="alert" className="rounded-2xl border border-red-500/30 bg-red-950/30 p-5 text-sm text-red-200">
              <p>{getErrorMessage(query.error)}</p>
              <button type="button" onClick={() => void query.refetch()} className="mt-3 rounded-lg border border-red-400/30 px-3 py-2 text-xs hover:bg-red-900/30">Retry</button>
            </div>
          )}

          {world && (
            <>
              <div className="relative">
                <WorldViewport employees={world.employees} selectedEmployeeId={selectedEmployeeId} onEmployeeSelect={onEmployeeSelect} />
                <MobileInputAdapter />
                {selectedEmployee && (
                  <aside className="absolute bottom-4 right-4 w-[min(360px,calc(100%-2rem))] rounded-2xl border border-cyan-400/20 bg-slate-950/95 p-4 shadow-2xl backdrop-blur" aria-label="Selected employee">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-white">{selectedEmployee.name}</p>
                        <p className="mt-1 text-xs text-slate-400">{selectedEmployee.kind} · {selectedEmployee.state.replaceAll("_", " ")}</p>
                      </div>
                      <button type="button" onClick={() => setSelectedEmployeeId(null)} className="rounded-lg px-2 py-1 text-xs text-slate-400 hover:bg-white/10 hover:text-white" aria-label="Close employee panel">Esc</button>
                    </div>
                    {selectedEmployee.currentWorkItem && (
                      <div className="mt-3 rounded-xl border border-white/10 bg-white/[0.03] p-3">
                        <p className="text-[10px] uppercase tracking-wide text-slate-500">Current work</p>
                        <p className="mt-1 text-sm text-slate-200">{selectedEmployee.currentWorkItem.title}</p>
                        <p className="mt-1 text-xs text-slate-500">{selectedEmployee.currentWorkItem.status}</p>
                      </div>
                    )}
                    <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                      <div className="rounded-lg border border-white/10 p-2"><span className="text-slate-500">Latest run</span><p className="mt-1 text-slate-200">{selectedEmployee.latestRunStatus ?? "None"}</p></div>
                      <div className="rounded-lg border border-white/10 p-2"><span className="text-slate-500">Employee ID</span><p className="mt-1 truncate text-slate-200">{selectedEmployee.id}</p></div>
                    </div>
                    <Link href={`/employees/${selectedEmployee.id}`} className="mt-3 block rounded-lg bg-white px-3 py-2 text-center text-xs font-semibold text-slate-950 hover:bg-slate-100">
                      Open Employee Management
                    </Link>
                  </aside>
                )}
              </div>

              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                  <p className="text-xs uppercase tracking-wider text-slate-500">Workforce</p>
                  <p className="mt-1 text-lg font-semibold">{world.progression.activeEmployees}/{world.progression.employeeLimit}</p>
                  <p className="mt-1 text-xs text-slate-400">active employees against plan capacity</p>
                </div>
                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                  <p className="text-xs uppercase tracking-wider text-slate-500">Workflow capacity</p>
                  <p className="mt-1 text-lg font-semibold">{world.progression.activeWorkflows}/{world.progression.workflowLimit}</p>
                  <p className="mt-1 text-xs text-slate-400">authoritative active workflows</p>
                </div>
                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                  <p className="text-xs uppercase tracking-wider text-slate-500">HQ tier</p>
                  <p className="mt-1 text-lg font-semibold">{world.progression.tier}</p>
                  <p className="mt-1 text-xs text-slate-400">{world.progression.completionPercent}% capacity utilization index</p>
                </div>
              </div>
            </>
          )}
        </section>
      </div>
    </main>
  );
}
\n\nfunction Outcome({ label, value }: { label: string; value: number }) {\n  return <div className="rounded-xl border border-white/10 bg-slate-950/40 p-3"><p className="text-[10px] uppercase tracking-wide text-slate-500">{label}</p><p className="mt-1 text-lg font-semibold text-white">{typeof value === "number" ? value.toLocaleString() : "—"}</p></div>;\n}\n