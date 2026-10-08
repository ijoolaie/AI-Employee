"use client";

import Link from "next/link";
import { ArrowLeft, Building2, Compass, LayoutDashboard, Map, Sparkles } from "lucide-react";

export function WorldShell() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-950 text-white">
      <div
        className="absolute inset-0 opacity-70"
        style={{
          backgroundImage:
            "linear-gradient(30deg, rgba(148,163,184,.08) 12%, transparent 12.5%, transparent 87%, rgba(148,163,184,.08) 87.5%), linear-gradient(150deg, rgba(148,163,184,.08) 12%, transparent 12.5%, transparent 87%, rgba(148,163,184,.08) 87.5%)",
          backgroundSize: "72px 42px",
        }}
      />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(59,130,246,.18),transparent_55%)]" />

      <header className="relative z-10 flex items-center justify-between border-b border-white/10 bg-slate-950/75 px-4 py-3 backdrop-blur md:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600">
            <Building2 className="h-4 w-4" />
          </div>
          <div>
            <p className="text-sm font-semibold">AI Company HQ</p>
            <p className="text-[11px] text-slate-400">World Mode · F0 Shell</p>
          </div>
        </div>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium hover:bg-white/10"
        >
          <LayoutDashboard className="h-4 w-4" />
          Management
        </Link>
      </header>

      <main className="relative z-10 flex min-h-[calc(100vh-65px)] items-center justify-center p-4 md:p-8">
        <section className="w-full max-w-4xl rounded-3xl border border-white/10 bg-slate-900/70 p-6 shadow-2xl backdrop-blur md:p-10">
          <div className="grid gap-8 md:grid-cols-[1.3fr_.7fr] md:items-center">
            <div>
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-brand-400/20 bg-brand-400/10 px-3 py-1 text-xs text-brand-200">
                <Sparkles className="h-3.5 w-3.5" />
                Explorable company is coming online
              </div>
              <h1 className="text-3xl font-semibold tracking-tight md:text-5xl">
                Your AI Company, in one living HQ.
              </h1>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-300 md:text-base">
                World Mode is being built over the same governed workforce that powers Management Mode.
                This shell intentionally shows no invented employees, revenue, activity or productivity.
              </p>
              <div className="mt-7 flex flex-wrap gap-3">
                <Link
                  href="/office"
                  className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-slate-900 hover:bg-slate-100"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Open current HQ
                </Link>
                <Link
                  href="/dashboard"
                  className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-4 py-2.5 text-sm font-medium hover:bg-white/10"
                >
                  <LayoutDashboard className="h-4 w-4" />
                  Management Mode
                </Link>
              </div>
            </div>

            <div className="rounded-2xl border border-white/10 bg-slate-950/70 p-5">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <Map className="h-4 w-4 text-brand-300" />
                World foundation
              </div>
              <ul className="mt-4 space-y-3 text-xs text-slate-300">
                <li className="flex gap-2"><Compass className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />Management and World share the same customer session.</li>
                <li className="flex gap-2"><Compass className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />Backend remains the source of truth.</li>
                <li className="flex gap-2"><Compass className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />Real employee projection starts in the next vertical slice.</li>
              </ul>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
