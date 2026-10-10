"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Building2, LayoutDashboard, Palette, Sparkles } from "lucide-react";
import { api, getCustomerOffice, getErrorMessage, getROIAnalytics } from "@/lib/api";
import { MobileInputAdapter } from "./MobileInputAdapter";
import { WorldEmployeePanel } from "./WorldEmployeePanel";
import { WorldOutcomePanel } from "./WorldOutcomePanel";
import { WorldProgressionPanel } from "./WorldProgressionPanel";
import { projectWorldReadModel } from "./WorldState";
import { WorldViewport } from "./WorldViewport";
import { WorldCustomizationPanel } from "./WorldCustomizationPanel";
import { WorldRoomOfferPanel } from "./WorldRoomOfferPanel";
import { WorldStatusBar } from "./WorldStatusBar";
import { WorldMiniMap } from "./WorldMiniMap";
import { WorldRoomAccessPanel } from "./WorldRoomAccessPanel";
import { isRoomSceneAccessUsable } from "./WorldRoomSceneAccess";

type APIResponse<T> = { success: boolean; data?: T };
type WorldCatalogueItem = { code: string; item_type: string; is_free: boolean };
type WorldRoomInventory = { room_instance_id: string; item_code: string; status: string; expires_at: string | null };
type WorldRoomInventoryAccess = { item_code: string; granted: boolean; reason: string; room_instance_id: string | null; expires_at: string | null };


export function WorldShell() {
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<string | null>(null);
  const [showMiniMap, setShowMiniMap] = useState(false);
  const [showCustomization, setShowCustomization] = useState(false);
  const [nearLockedRoom, setNearLockedRoom] = useState(false);
  const [showRoomOffer, setShowRoomOffer] = useState(false);
  const [showRoomAccess, setShowRoomAccess] = useState(false);
  const officeQuery = useQuery({ queryKey: ["customer-world-read-model"], queryFn: getCustomerOffice, refetchInterval: 5000, staleTime: 2000 });
  const roiQuery = useQuery({ queryKey: ["world-roi"], queryFn: getROIAnalytics, refetchInterval: 15000, staleTime: 5000 });
  const roomCatalogueQuery = useQuery({
    queryKey: ["world-room-access-catalogue"],
    queryFn: async () => {
      const response = await api.get<APIResponse<WorldCatalogueItem[]>>("/world-commerce/catalogue");
      if (!response.data.success || !Array.isArray(response.data.data)) throw new Error("کاتالوگ اتاق معتبر نیست.");
      return response.data.data.find((item) => item.item_type === "room" && !item.is_free)?.code ?? null;
    },
    staleTime: 30_000,
    retry: 1,
  });
  const roomInventoryQuery = useQuery({
    queryKey: ["world-room-inventory"],
    queryFn: async () => {
      const response = await api.get<APIResponse<WorldRoomInventory[]>>("/world-commerce/room-inventory");
      if (!response.data.success || !Array.isArray(response.data.data)) throw new Error("موجودی اتاق معتبر نیست.");
      return response.data.data;
    },
    refetchInterval: 15_000,
    staleTime: 5_000,
    retry: 1,
  });
  const roomAccessItemCode = roomInventoryQuery.data?.[0]?.item_code ?? roomCatalogueQuery.data;
  const roomAccessQuery = useQuery({
    queryKey: ["world-room-inventory-access", roomAccessItemCode],
    enabled: Boolean(roomAccessItemCode) && !roomInventoryQuery.isLoading && !roomInventoryQuery.error,
    queryFn: async () => {
      const response = await api.get<APIResponse<WorldRoomInventoryAccess>>(`/world-commerce/room-inventory/${encodeURIComponent(roomAccessItemCode!)}/access`);
      if (!response.data.success || !response.data.data) throw new Error("وضعیت دسترسی اتاق معتبر نیست.");
      return response.data.data;
    },
    refetchInterval: 15_000,
    staleTime: 5_000,
    retry: 1,
  });
  const roomAccessUnavailable = Boolean(roomInventoryQuery.error || roomCatalogueQuery.error || roomAccessQuery.error || (!roomCatalogueQuery.isLoading && roomCatalogueQuery.data === null));
  const roomSceneAccess = {
    granted: roomAccessQuery.data?.granted === true,
    roomInstanceId: roomAccessQuery.data?.room_instance_id ?? null,
    expiresAt: roomAccessQuery.data?.expires_at ?? null,
    unavailable: roomAccessUnavailable,
  };
  const roomAccessGranted = isRoomSceneAccessUsable(roomSceneAccess, roomAccessUnavailable);
  const world = useMemo(() => (officeQuery.data ? projectWorldReadModel(officeQuery.data) : null), [officeQuery.data]);
  const onEmployeeSelect = useCallback((id: string | null) => setSelectedEmployeeId(id), []);
  const onMapToggle = useCallback(() => setShowMiniMap((value) => !value), []);
  const onRoomProximity = useCallback((near: boolean) => setNearLockedRoom(near), []);
  const onRoomInteract = useCallback(() => {
    if (roomInventoryQuery.isLoading || roomAccessQuery.isLoading || roomCatalogueQuery.isLoading || roomAccessUnavailable) {
      setShowRoomOffer(false);
      setShowRoomAccess(true);
    } else if (roomAccessGranted) {
      setShowRoomOffer(false);
      setShowRoomAccess(true);
    } else {
      setShowRoomAccess(false);
      setShowRoomOffer(true);
    }
  }, [roomInventoryQuery.isLoading, roomAccessQuery.isLoading, roomCatalogueQuery.isLoading, roomAccessUnavailable, roomAccessGranted]);
  useEffect(() => {
    const expiresAt = roomAccessQuery.data?.expires_at;
    if (roomAccessQuery.data?.granted !== true || !expiresAt) return;

    const delay = Date.parse(expiresAt) - Date.now();
    if (!Number.isFinite(delay) || delay <= 0) {
      void roomAccessQuery.refetch();
      return;
    }
    const timeout = window.setTimeout(() => { void roomAccessQuery.refetch(); }, delay);
    return () => window.clearTimeout(timeout);
  }, [roomAccessQuery.data?.expires_at, roomAccessQuery.data?.granted, roomAccessQuery.refetch]);

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
                <WorldViewport employees={world.employees} selectedEmployeeId={selectedEmployeeId} onEmployeeSelect={onEmployeeSelect} onMapToggle={onMapToggle} onRoomProximity={onRoomProximity} onRoomInteract={onRoomInteract} roomAccess={roomSceneAccess} />
                <MobileInputAdapter />
                {showMiniMap && <WorldMiniMap employeeCount={world.employees.length} />}
                {nearLockedRoom && !showRoomOffer && !showRoomAccess && !showCustomization && <button type="button" onClick={onRoomInteract} className="absolute bottom-20 left-1/2 z-20 -translate-x-1/2 rounded-xl border border-amber-300/40 bg-slate-950/90 px-4 py-3 text-sm text-amber-100 shadow-xl backdrop-blur">{roomAccessGranted ? "Locked room nearby · Access authorized · Press E or inspect" : "Locked room nearby · Press E to inspect access or rent"}</button>}
                {showRoomOffer && <WorldRoomOfferPanel onClose={() => setShowRoomOffer(false)} />}
                {showRoomAccess && <WorldRoomAccessPanel state={roomInventoryQuery.isLoading || roomCatalogueQuery.isLoading || roomAccessQuery.isLoading ? "loading" : roomAccessUnavailable ? "unavailable" : roomAccessGranted ? "granted" : "unavailable"} itemCode={roomAccessQuery.data?.item_code ?? roomAccessItemCode ?? ""} expiresAt={roomAccessQuery.data?.expires_at ?? null} roomInstanceId={roomAccessQuery.data?.room_instance_id ?? null} onRetry={() => { void roomInventoryQuery.refetch(); void roomCatalogueQuery.refetch(); if (roomAccessItemCode) void roomAccessQuery.refetch(); }} onClose={() => setShowRoomAccess(false)} />}
                {selectedEmployee && <WorldEmployeePanel employee={selectedEmployee} onClose={() => setSelectedEmployeeId(null)} />}
              </div>

              <RoomLeaseStatus
                loading={roomInventoryQuery.isLoading || roomCatalogueQuery.isLoading || roomAccessQuery.isLoading}
                unavailable={roomAccessUnavailable}
                access={roomAccessQuery.data ?? null}
                granted={roomAccessGranted}
              />
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

function RoomLeaseStatus({ loading, unavailable, access, granted }: { loading: boolean; unavailable: boolean; access: WorldRoomInventoryAccess | null; granted: boolean }) {
  const expiry = access?.expires_at ? new Intl.DateTimeFormat("fa-IR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(access.expires_at)) : null;
  return (
    <section aria-label="World room lease status" className="rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-3">
      <p className="text-xs font-semibold text-slate-300">وضعیت موجودی و دسترسی اتاق</p>
      {loading && <p role="status" className="mt-1 text-sm text-slate-400">در حال بررسی موجودی و مجوز اتاق از سرور…</p>}
      {unavailable && <p role="alert" className="mt-1 text-sm text-amber-200">وضعیت موجودی یا مجوز قابل بررسی نیست؛ دسترسی مسدود می‌ماند.</p>}
      {!loading && !unavailable && granted && access?.room_instance_id && (
        <p className="mt-1 text-sm text-emerald-200">اتاق «{access.item_code}» از سرور تأیید شد{expiry ? ` تا ${expiry}` : ""}. شناسه نمونه: <span className="font-mono">{access.room_instance_id}</span>. صحنه فقط تا پایان اعتبار مجاز نمایش داده می‌شود.</p>
      )}
      {!loading && !unavailable && !granted && <p className="mt-1 text-sm text-slate-400">نمونه اتاق دارای مجوز معتبر برای این مستأجر پیدا نشد.</p>}
    </section>
  );
}
