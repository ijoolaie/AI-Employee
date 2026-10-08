import type { WorldProgression } from "./WorldState";

export function WorldProgressionPanel({ progression }: { progression: WorldProgression }) {
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      <StatCard label="Workforce" value={`${progression.activeEmployees}/${progression.employeeLimit}`} detail="active employees against plan capacity" />
      <StatCard label="Workflow capacity" value={`${progression.activeWorkflows}/${progression.workflowLimit}`} detail="authoritative active workflows" />
      <StatCard label="HQ tier" value={progression.tier} detail={`${progression.completionPercent}% capacity utilization index`} />
    </div>
  );
}

function StatCard({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <p className="text-xs uppercase tracking-wider text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
      <p className="mt-1 text-xs text-slate-400">{detail}</p>
    </div>
  );
}
