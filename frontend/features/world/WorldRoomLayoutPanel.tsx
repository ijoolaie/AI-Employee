"use client";

import { useState } from "react";
import { api, getErrorMessage } from "@/lib/api";
import type { RoomFurnitureKind, RoomFurniturePlacement, WorldRoomSceneConfig } from "./WorldRoomSceneConfig";

type APIResponse<T> = { success: boolean; data?: T };
type SceneConfigResponse = { room_instance_id: string; item_code: string; scene_config: WorldRoomSceneConfig; updated_at: string };

const KIND_LABELS: Record<RoomFurnitureKind, string> = {
  desk: "Desk",
  chair: "Chair",
  plant: "Plant",
  cabinet: "Cabinet",
  meeting_table: "Meeting table",
};

export function WorldRoomLayoutPanel({
  itemCode,
  roomInstanceId,
  initialConfig,
  onClose,
  onSaved,
}: {
  itemCode: string;
  roomInstanceId: string;
  initialConfig: WorldRoomSceneConfig;
  onClose: () => void;
  onSaved: (config: WorldRoomSceneConfig) => void;
}) {
  const [furniture, setFurniture] = useState<RoomFurniturePlacement[]>(initialConfig.furniture);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const addFurniture = (kind: RoomFurnitureKind) => {
    if (furniture.length >= 40) {
      setError("A room can contain at most 40 built-in items.");
      return;
    }
    setError("");
    setMessage("");
    const placementId = `${kind}-${crypto.randomUUID().replaceAll("-", "").slice(0, 20)}`;
    const offset = ((furniture.length % 5) - 2) * 0.5;
    setFurniture((current) => [
      ...current,
      { placement_id: placementId, kind, x: Math.max(-2.2, Math.min(2.2, offset)), z: Math.max(-2.2, Math.min(2.2, offset)), rotation: 0 },
    ]);
  };

  const updatePlacement = (placementId: string, patch: Partial<Pick<RoomFurniturePlacement, "x" | "z" | "rotation">>) => {
    setFurniture((current) => current.map((item) => item.placement_id === placementId ? { ...item, ...patch } : item));
    setMessage("");
    setError("");
  };

  const save = async () => {
    setSaving(true);
    setMessage("");
    setError("");
    try {
      const response = await api.put<APIResponse<SceneConfigResponse>>(
        `/world-commerce/room-inventory/${encodeURIComponent(itemCode)}/scene-config`,
        { schema_version: 1, layout_preset: "starter", furniture },
      );
      if (!response.data.success || !response.data.data) {
        throw new Error("The server did not confirm that the room layout was saved.");
      }
      onSaved(response.data.data.scene_config);
      setMessage("Room layout saved to the server.");
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setSaving(false);
    }
  };

  return (
    <section role="dialog" aria-modal="true" aria-labelledby="world-room-layout-title" className="absolute inset-3 z-40 overflow-y-auto rounded-2xl border border-cyan-300/30 bg-slate-950/98 p-4 text-slate-100 shadow-2xl backdrop-blur-xl sm:inset-8 sm:p-6">
      <header className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-cyan-300">Persistent room layout</p>
          <h3 id="world-room-layout-title" className="mt-1 text-xl font-semibold">Customize your room</h3>
          <p className="mt-1 text-sm text-slate-400">Room instance: <span className="font-mono">{roomInstanceId}</span></p>
        </div>
        <button type="button" onClick={onClose} className="rounded-lg border border-slate-700 px-3 py-2 text-sm">Close</button>
      </header>

      <p className="mt-4 text-sm leading-6 text-slate-300">Adjust built-in furniture positions within the room footprint, then save; the scene updates after the server confirms your active room lease.</p>

      <div className="mt-4 flex flex-wrap gap-2">
        {(Object.keys(KIND_LABELS) as RoomFurnitureKind[]).map((kind) => (
          <button key={kind} type="button" disabled={saving || furniture.length >= 40} onClick={() => addFurniture(kind)} className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm hover:border-cyan-300/60 disabled:opacity-50">
            + Add {KIND_LABELS[kind].toLowerCase()}
          </button>
        ))}
      </div>

      <div className="mt-4 space-y-3">
        {furniture.length === 0 && <p className="rounded-lg border border-slate-800 bg-slate-900 p-4 text-sm text-slate-400">This room has no furniture placements yet.</p>}
        {furniture.map((item) => (
          <div key={item.placement_id} className="grid gap-3 rounded-xl border border-slate-800 bg-slate-900 p-3 sm:grid-cols-[minmax(0,1fr)_100px_100px_100px_auto] sm:items-end">
            <div>
              <p className="text-sm font-medium">{KIND_LABELS[item.kind]}</p>
              <p className="mt-1 break-all font-mono text-xs text-slate-500">{item.placement_id}</p>
            </div>
            <label className="text-xs text-slate-400">X (-2.2 to 2.2)
              <input aria-label={`${item.placement_id} X`} type="number" min={-2.2} max={2.2} step={0.5} value={item.x} disabled={saving} onChange={(event) => updatePlacement(item.placement_id, { x: Math.max(-2.2, Math.min(2.2, Number(event.target.value))) })} className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-950 px-2 py-2 text-sm text-slate-100" />
            </label>
            <label className="text-xs text-slate-400">Z (-2.2 to 2.2)
              <input aria-label={`${item.placement_id} Z`} type="number" min={-2.2} max={2.2} step={0.5} value={item.z} disabled={saving} onChange={(event) => updatePlacement(item.placement_id, { z: Math.max(-2.2, Math.min(2.2, Number(event.target.value))) })} className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-950 px-2 py-2 text-sm text-slate-100" />
            </label>
            <label className="text-xs text-slate-400">Rotation
              <input aria-label={`${item.placement_id} rotation`} type="number" min={0} max={359} step={15} value={item.rotation} disabled={saving} onChange={(event) => updatePlacement(item.placement_id, { rotation: Math.max(0, Math.min(359, Math.trunc(Number(event.target.value)))) })} className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-950 px-2 py-2 text-sm text-slate-100" />
            </label>
            <button type="button" disabled={saving} onClick={() => setFurniture((current) => current.filter((candidate) => candidate.placement_id !== item.placement_id))} className="rounded-lg border border-red-400/30 px-3 py-2 text-sm text-red-200 disabled:opacity-50">Remove</button>
          </div>
        ))}
      </div>

      {message && <p role="status" className="mt-4 rounded-lg border border-emerald-400/30 bg-emerald-950/30 p-3 text-sm text-emerald-200">{message}</p>}
      {error && <p role="alert" className="mt-4 rounded-lg border border-red-400/30 bg-red-950/30 p-3 text-sm text-red-200">{error}</p>}

      <footer className="mt-5 flex flex-wrap justify-end gap-2 border-t border-slate-800 pt-4">
        <button type="button" disabled={saving} onClick={onClose} className="rounded-lg border border-slate-700 px-4 py-2 text-sm disabled:opacity-50">Cancel</button>
        <button type="button" disabled={saving} onClick={() => void save()} className="rounded-lg bg-cyan-300 px-4 py-2 text-sm font-semibold text-slate-950 disabled:opacity-50">{saving ? "Saving…" : "Save layout"}</button>
      </footer>
    </section>
  );
}
