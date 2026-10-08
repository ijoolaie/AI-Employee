export function WorldMiniMap({ employeeCount }: { employeeCount: number }) {
  return (
    <div className="absolute right-4 top-4 w-44 rounded-xl border border-white/10 bg-slate-950/90 p-3 shadow-xl backdrop-blur" aria-label="HQ mini map">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">HQ Map</span>
        <span className="text-[10px] text-slate-600">{employeeCount} staff</span>
      </div>
      <div className="relative h-24 overflow-hidden rounded-lg border border-white/10 bg-slate-900" aria-hidden="true">
        <div className="absolute left-[18%] top-[18%] h-7 w-9 rounded border border-cyan-400/40 bg-cyan-400/10" />
        <div className="absolute left-[56%] top-[14%] h-7 w-10 rounded border border-cyan-400/40 bg-cyan-400/10" />
        <div className="absolute left-[60%] top-[64%] h-7 w-10 rounded border border-cyan-400/40 bg-cyan-400/10" />
        <div className="absolute left-[18%] top-[64%] h-7 w-10 rounded border border-cyan-400/40 bg-cyan-400/10" />
      </div>
      <p className="mt-2 text-[10px] leading-4 text-slate-500">Layout is presentation-only until authoritative department/location data exists.</p>
    </div>
  );
}
