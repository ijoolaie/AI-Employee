import Link from "next/link";
import type { ROIAnalytics } from "@/types";

export function WorldOutcomePanel({ data }: { data: ROIAnalytics | undefined }) {
  return (
    <div className="rounded-2xl border border-emerald-400/15 bg-emerald-400/[0.03] p-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wider text-emerald-300">Business outcome loop</p>
          <h3 className="mt-1 text-lg font-semibold">World activity is tied to recorded business evidence.</h3>
        </div>
        <Link href="/analytics" className="text-xs font-medium text-emerald-200 hover:text-white">Open Analytics →</Link>
      </div>
      {data ? (
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Outcome label="Conversations" value={data.conversations} />
          <Outcome label="AI resolved" value={data.ai_resolved} />
          <Outcome label="Orders" value={data.orders} />
          <Outcome label="Influenced revenue" value={data.influenced_revenue} />
        </div>
      ) : (
        <p className="mt-3 text-sm text-slate-400">No outcome data is currently available. The World does not invent revenue or productivity values.</p>
      )}
    </div>
  );
}

function Outcome({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-white/10 bg-slate-950/40 p-3">
      <p className="text-[10px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-white">{value.toLocaleString()}</p>
    </div>
  );
}
