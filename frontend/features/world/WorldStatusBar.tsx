import type { WorldReadModel } from "./WorldState";

export function WorldStatusBar({ world }: { world: WorldReadModel }) {
  const counts = world.employees.reduce<Record<string, number>>((acc, employee) => {
    acc[employee.state] = (acc[employee.state] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/70 px-3 py-2 text-[11px] text-slate-400">
      <span className="font-medium text-slate-200">Live HQ</span>
      {Object.entries(counts).map(([state, count]) => <span key={state} className="rounded-full border border-white/10 px-2 py-1">{state.replaceAll("_", " ")} {count}</span>)}
      <span className="ml-auto">source updated {new Intl.DateTimeFormat(undefined, { timeStyle: "medium" }).format(new Date(world.generatedAt))}</span>
    </div>
  );
}
