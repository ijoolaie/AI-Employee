"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Building2, LayoutDashboard, Palette, Sparkles } from "lucide-react";
import { getCustomerOffice, getErrorMessage, getROIAnalytics } from "@/lib/api";
import { MobileInputAdapter } from "./MobileInputAdapter";
import { WorldEmployeePanel } from "./WorldEmployeePanel";
import { WorldOutcomePanel } from "./WorldOutcomePanel";
import { WorldProgressionPanel } from "./WorldProgressionPanel";
import { projectWorldReadModel } from "./WorldState";
import { WorldViewport } from "./WorldViewport";
import { WorldCustomizationPanel } from "./WorldCustomizationPanel";
import { WorldStatusBar } from "./WorldStatusBar";
import { WorldMiniMap } from "./WorldMiniMap";

export function WorldShell() {
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<string | null>(null);
  const [showMiniMap, setShowMiniMap] = useState(false);
  const [showCustomization, setShowCustomization] = useState(false);
  const [nearLockedRoom, setNearLockedRoom] = useState(false);
  const [showRoomOffer, setShowRoomOffer] = useState(false);
  const officeQuery = useQuery({ queryKey: ["customer-world-read-model"], queryFn: getCustomerOffice, refetchInterval: 5000, staleTime: 2000 });
  const roiQuery = useQuery({ queryKey: ["world-roi"], queryFn: getROIAnalytics, refetchInterval: 15000, staleTime: 5000 });
  const world = useMemo(() => (officeQuery.data ? projectWorldReadModel(officeQuery.data) : null), [officeQuery.data]);
  const onEmployeeSelect = useCallback((id: string | null) => setSelectedEmployeeId(id), []);
  const onMapToggle = useCallback(() => setShowMiniMap((value) => !value), []);
  const onRoomProximity = useCallback((near: boolean) => setNearLockedRoom(near), []);
  const onRoomInteract = useCallback(() => setShowRoomOffer(true), []);
  const selectedEmployee = world?.employees.find((employee) => employee.id === selectedEmployeeId) ?? null;

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setSelectedEmployeeId(null);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

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
            <LayoutDashboard className="h-4 w-4" /> Management Mode
          </Link>
        </header>

        <section className="flex flex-1 flex-col gap-5 py-5">
          <div>
            <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-cyan-500/20 bg-cyan-500/5 px-3 py-1 text-xs text-cyan-200">
              <Sparkles className="h-3.5 w-3.5" /> AI Company World
            </div>
            <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">Your real workforce, inside the HQ.</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              World Mode is a read-only presentation layer over governed business data. It never creates employees, revenue, tasks, approvals, or AI execution state.
            </p>
          </div>

          {officeQuery.isLoading && <LoadingState />}
          {officeQuery.error && <ErrorState message={getErrorMessage(officeQuery.error)} onRetry={() => void officeQuery.refetch()} />}

          {world && (
            <>
              <div className="relative">
                <WorldViewport employees={world.employees} selectedEmployeeId={selectedEmployeeId} onEmployeeSelect={onEmployeeSelect} onMapToggle={onMapToggle} onRoomProximity={onRoomProximity} onRoomInteract={onRoomInteract} />
                <MobileInputAdapter />
                {showMiniMap && <WorldMiniMap employeeCount={world.employees.length} />}
                {nearLockedRoom && !showRoomOffer && !showCustomization && <button type="button" onClick={() => setShowRoomOffer(true)} className="absolute bottom-20 left-1/2 z-20 -translate-x-1/2 rounded-xl border border-amber-300/40 bg-slate-950/90 px-4 py-3 text-sm text-amber-100 shadow-xl backdrop-blur">Locked room nearby · Press E or inspect</button>}
                {showRoomOffer && <section role="dialog" aria-modal="true" aria-labelledby="world-room-offer-title" className="absolute bottom-4 left-4 right-4 z-30 mx-auto max-w-lg rounded-2xl border border-amber-300/30 bg-slate-950/95 p-5 text-slate-100 shadow-2xl backdrop-blur-xl"><div className="flex items-start justify-between gap-3"><div><p className="text-xs uppercase tracking-[0.2em] text-amber-200">Expansion opportunity</p><h3 id="world-room-offer-title" className="mt-1 text-lg font-semibold">Your next office room</h3></div><button type="button" onClick={() => setShowRoomOffer(false)} className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm">Close</button></div><p className="mt-3 text-sm leading-6 text-slate-300">You can rent this room for 1 month with 1 employee. Starter desk, chair and computer are planned for the room.</p><p className="mt-3 rounded-lg border border-slate-800 bg-slate-900 p-3 text-sm text-amber-100">Price and payment options will appear when the server catalogue and verified order flow are connected.</p><div className="mt-4 flex flex-wrap items-center justify-between gap-3"><span className="text-xs text-slate-500">Preview only · no payment or room activation occurs</span><button type="button" onClick={() => setShowRoomOffer(false)} className="rounded-lg bg-amber-200 px-4 py-2 text-sm font-semibold text-slate-950">Got it</button></div></section>}
                {selectedEmployee && <WorldEmployeePanel employee={selectedEmployee} onClose={() => setSelectedEmployeeId(null)} />}
              </div>

              <WorldStatusBar world={world} />
              <WorldProgressionPanel progression={world.progression} />
              <WorldOutcomePanel data={roiQuery.data} />
            </>
          )}
        </section>
      </div>
    </main>
  );
}

function LoadingState() {
  return <div role="status" className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 text-sm text-slate-400">Loading the authoritative HQ state…</div>;
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div role="alert" className="rounded-2xl border border-red-500/30 bg-red-950/30 p-5 text-sm text-red-200">
      <p>{message}</p>
      <button type="button" onClick={onRetry} className="mt-3 rounded-lg border border-red-400/30 px-3 py-2 text-xs hover:bg-red-900/30">Retry</button>
    </div>
  );
}
