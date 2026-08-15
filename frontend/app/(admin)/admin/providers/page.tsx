"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, CircleAlert, ShieldCheck } from "lucide-react";
import { getPlatformProviders } from "@/lib/api";

type Provider = { name: string; category: string; configured: boolean; secret_configured: boolean };

export default function AdminProvidersPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    getPlatformProviders().then((data) => setProviders(data.providers)).catch((e) => setError(e instanceof Error ? e.message : "Unable to load providers"));
  }, []);

  return <div className="min-h-screen bg-slate-50 p-6">
    <div className="mx-auto max-w-5xl">
      <div className="mb-6 flex items-center gap-3">
        <div className="rounded-xl bg-slate-950 p-3 text-white"><ShieldCheck className="h-5 w-5" /></div>
        <div><h1 className="text-2xl font-semibold text-slate-950">Provider Readiness</h1><p className="text-sm text-slate-500">Configuration health only — secrets are never exposed.</p></div>
      </div>
      {error && <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
      <div className="grid gap-3 md:grid-cols-2">
        {providers.map((p) => <div key={p.name} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div><div className="font-medium">{p.name}</div><div className="text-xs uppercase tracking-wide text-slate-400">{p.category}</div></div>
            {p.configured ? <CheckCircle2 className="h-5 w-5 text-emerald-600" /> : <CircleAlert className="h-5 w-5 text-amber-600" />}
          </div>
          <div className="mt-3 text-xs text-slate-500">Configuration: <b>{p.configured ? "ready" : "missing"}</b> · Secret: <b>{p.secret_configured ? "configured" : "missing"}</b></div>
        </div>)}
      </div>
    </div>
  </div>;
}
