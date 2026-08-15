"use client";

export function BarChart({ values, labels }: { values: number[]; labels: string[] }) {
  const max = Math.max(...values, 1);
  return <div className="flex h-44 items-end gap-2 border-b border-gray-100 px-2 pb-1 pt-4">
    {values.map((v, i) => <div key={`${labels[i]}-${i}`} className="flex h-full flex-1 flex-col items-center justify-end gap-1">
      <span className="text-[10px] text-gray-400">{v}</span>
      <div className="w-full max-w-10 rounded-t-md bg-brand-500 transition-all" style={{ height: `${Math.max(4, (v / max) * 100)}%` }} />
      <span className="truncate text-[10px] text-gray-400">{labels[i]}</span>
    </div>)}
  </div>;
}

export function ProgressBar({ value, max = 100, label }: { value: number; max?: number; label?: string }) {
  const pct = Math.min(100, Math.max(0, max ? (value / max) * 100 : 0));
  return <div>{label && <div className="mb-1 flex justify-between text-xs text-gray-500"><span>{label}</span><span>{Math.round(pct)}%</span></div>}<div className="h-2 overflow-hidden rounded-full bg-gray-100"><div className="h-full rounded-full bg-brand-500" style={{ width: `${pct}%` }} /></div></div>;
}
