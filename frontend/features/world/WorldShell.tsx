"use client";

import Link from "next/link";
import { Building2, LayoutDashboard, Sparkles } from "lucide-react";
import { MobileInputAdapter } from "./MobileInputAdapter";
import { WorldViewport } from "./WorldViewport";

export function WorldShell() {
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
            <LayoutDashboard className="h-4 w-4" />
            Management Mode
          </Link>
        </header>

        <section className="flex flex-1 flex-col gap-5 py-5">
          <div>
            <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-cyan-500/20 bg-cyan-500/5 px-3 py-1 text-xs text-cyan-200">
              <Sparkles className="h-3.5 w-3.5" />
              F1 · World renderer
            </div>
            <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">Explore your company as a living workspace.</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              This map is a deterministic presentation layer. Business truth remains in the governed backend and is projected here in F2.
            </p>
          </div>

          <div className="relative">
            <WorldViewport />
            <MobileInputAdapter />
          </div>
        </section>
      </div>
    </main>
  );
}
