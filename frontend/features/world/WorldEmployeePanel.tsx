"use client";

import Link from "next/link";
import type { WorldEmployee } from "./WorldState";

export function WorldEmployeePanel({ employee, onClose }: { employee: WorldEmployee; onClose: () => void }) {
  return (
    <aside className="absolute bottom-4 right-4 w-[min(360px,calc(100%-2rem))] rounded-2xl border border-cyan-400/20 bg-slate-950/95 p-4 shadow-2xl backdrop-blur" aria-label="Selected employee">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-white">{employee.name}</p>
          <p className="mt-1 text-xs text-slate-400">{employee.kind} · {employee.state.replaceAll("_", " ")}</p>
        </div>
        <button type="button" onClick={onClose} className="rounded-lg px-2 py-1 text-xs text-slate-400 hover:bg-white/10 hover:text-white" aria-label="Close employee panel">
          Esc
        </button>
      </div>
      {employee.currentWorkItem && (
        <div className="mt-3 rounded-xl border border-white/10 bg-white/[0.03] p-3">
          <p className="text-[10px] uppercase tracking-wide text-slate-500">Current work</p>
          <p className="mt-1 text-sm text-slate-200">{employee.currentWorkItem.title}</p>
          <p className="mt-1 text-xs text-slate-500">{employee.currentWorkItem.status}</p>
        </div>
      )}
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
        <div className="rounded-lg border border-white/10 p-2"><span className="text-slate-500">Latest run</span><p className="mt-1 text-slate-200">{employee.latestRunStatus ?? "None"}</p></div>
        <div className="rounded-lg border border-white/10 p-2"><span className="text-slate-500">Employee ID</span><p className="mt-1 truncate text-slate-200">{employee.id}</p></div>
      </div>
      <Link href={`/employees/${employee.id}`} className="mt-3 block rounded-lg bg-white px-3 py-2 text-center text-xs font-semibold text-slate-950 hover:bg-slate-100">
        Open Employee Management
      </Link>
    </aside>
  );
}
