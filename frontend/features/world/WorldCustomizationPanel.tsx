"use client";

import { useState } from "react";

export function WorldCustomizationPanel({ onClose }: { onClose: () => void }) {
  const [tab, setTab] = useState<"office" | "ceo">("office");
  const [layout, setLayout] = useState("starter");
  const [avatar, setAvatar] = useState("classic");
  const [displayName, setDisplayName] = useState("CEO");
  const [style, setStyle] = useState("visionary");
  const [message, setMessage] = useState("");

  return (
    <section role="dialog" aria-modal="true" aria-labelledby="world-customize-title" className="absolute inset-3 z-30 overflow-y-auto rounded-2xl border border-white/15 bg-slate-950/95 p-4 text-slate-100 shadow-2xl backdrop-blur-xl sm:inset-8 sm:p-6">
      <header className="flex items-start justify-between gap-3">
        <div><p className="text-xs uppercase tracking-[0.2em] text-cyan-300">Your world, your style</p><h3 id="world-customize-title" className="mt-1 text-xl font-semibold">Customize your office</h3><p className="mt-1 text-sm text-slate-400">Free presets are selectable. Premium options remain locked until secure checkout is available.</p></div>
        <button type="button" onClick={onClose} className="rounded-lg border border-slate-700 px-3 py-2 text-sm">Close</button>
      </header>
      <div className="mt-5 flex gap-2">
        <button type="button" aria-pressed={tab === "office"} onClick={() => setTab("office")} className="rounded-lg bg-slate-800 px-4 py-2 text-sm">Office layout</button>
        <button type="button" aria-pressed={tab === "ceo"} onClick={() => setTab("ceo")} className="rounded-lg bg-slate-800 px-4 py-2 text-sm">CEO avatar</button>
      </div>
      {tab === "office" ? <div className="mt-4 grid gap-3 sm:grid-cols-3">
        {[
          { id: "starter", name: "Starter Office", description: "Compact warm office · Free", premium: false },
          { id: "modern", name: "Modern Studio", description: "Open-plan · Premium", premium: true },
          { id: "executive", name: "Executive Suite", description: "Large luxury office · Premium", premium: true },
        ].map((item) => <button key={item.id} type="button" aria-pressed={layout === item.id} onClick={() => item.premium ? setMessage("Premium checkout is not enabled. This option was not applied.") : (setLayout(item.id), setMessage("Free layout selected for this prototype session."))} className={`rounded-xl border p-4 text-left ${layout === item.id ? "border-cyan-300 bg-cyan-300/10" : "border-slate-800 bg-slate-900"}`}><span className="mb-4 flex h-20 items-center justify-center rounded-lg bg-gradient-to-br from-amber-200 to-orange-400 text-3xl text-slate-900">▦</span><span className="block font-medium">{item.name}</span><span className="mt-1 block text-xs text-slate-400">{item.description}</span></button>)}
      </div> : <div className="mt-4 space-y-4">
        <label className="block text-sm text-slate-300">CEO display name<input value={displayName} maxLength={32} onChange={(event) => setDisplayName(event.target.value.slice(0, 32))} className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2" /></label>
        <label className="block text-sm text-slate-300">Presentation personality<select value={style} onChange={(event) => setStyle(event.target.value)} className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"><option value="visionary">Visionary founder</option><option value="analytical">Analytical leader</option><option value="creative">Creative builder</option><option value="people-first">People-first manager</option></select></label>
        <div className="grid gap-3 sm:grid-cols-2">
          {[{id:"classic",name:"Classic CEO",premium:false},{id:"creative",name:"Creative style",premium:false},{id:"luxury",name:"Luxury Executive outfit",premium:true},{id:"founder",name:"Founder Edition outfit",premium:true}].map((item) => <button key={item.id} type="button" aria-pressed={avatar === item.id} onClick={() => item.premium ? setMessage("Premium outfit is locked until verified checkout and entitlement are implemented.") : (setAvatar(item.id), setMessage("Free appearance selected for this prototype session."))} className={`rounded-xl border p-4 text-left ${avatar === item.id ? "border-cyan-300 bg-cyan-300/10" : "border-slate-800 bg-slate-900"}`}><span className="block font-medium">{item.name}</span><span className="mt-1 block text-xs text-slate-400">{item.premium ? "Premium · locked" : "Free preset"}</span></button>)}
        </div>
        <p className="text-xs text-slate-500">Appearance and personality here are presentation-only. They do not change real employee permissions or AI execution settings.</p>
      </div>}
      {message && <p role="status" className="mt-4 rounded-lg border border-amber-400/20 bg-amber-400/5 p-3 text-sm text-amber-100">{message}</p>}
      <p className="mt-5 border-t border-slate-800 pt-4 text-xs text-slate-500">Prototype only: choices are not yet persisted to the account or applied to the 3D scene. Paid options cannot be activated from this panel.</p>
    </section>
  );
}
