"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Download, ShieldCheck, Store } from "lucide-react";

import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage } from "@/lib/api";
import { installMarketplacePublication, listMarketplacePublications, type MarketplacePublication } from "@/lib/marketplace";

function shortId(value: string) { return `${value.slice(0, 8)}…`; }
function formatDate(value: string) { return new Date(value).toLocaleString(); }

export default function MarketplacePage() {
  const queryClient = useQueryClient();
  const [workspace, setWorkspace] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [selected, setSelected] = useState<MarketplacePublication | null>(null);

  const publicationsQuery = useQuery({ queryKey: ["marketplace", "publications"], queryFn: listMarketplacePublications });
  const installMutation = useMutation({
    mutationFn: ({ id, workspaceKey }: { id: string; workspaceKey: string }) => installMarketplacePublication(id, workspaceKey),
    onSuccess: (installation) => {
      setMessage(`Installed ${shortId(installation.id)} locally. No AI Employee instance was provisioned.`);
      queryClient.invalidateQueries({ queryKey: ["marketplace"] });
    },
    onError: (error) => setMessage(getErrorMessage(error)),
  });

  const publications = publicationsQuery.data ?? [];

  return (<>
    <Header title="Marketplace" description="Discover published teams and install tenant-local copies." />
    <div className="space-y-6 p-6">
      <div className="rounded-xl border border-brand-100 bg-brand-50 p-4">
        <div className="flex gap-3"><ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-brand-600" /><div><p className="font-semibold text-gray-900">Authorized installation boundary</p><p className="mt-1 text-sm text-gray-600">Marketplace installation is permission-gated by the API. It creates tenant-local Team and Agent definitions and records publication provenance. Installation does not imply customer acceptance, production deployment, or trust beyond recorded evidence.</p></div></div>
      </div>
      {message && <div className="rounded-lg border border-gray-200 bg-white px-4 py-3 text-sm text-gray-700">{message}</div>}

      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <label className="block text-sm font-medium text-gray-700">Target workspace
          <input value={workspace} onChange={(event) => setWorkspace(event.target.value)} placeholder="default workspace" maxLength={120} className="mt-1 h-10 w-full max-w-md rounded-lg border border-gray-300 px-3 text-sm outline-none focus:border-brand-500" />
        </label>
        <p className="mt-2 text-xs text-gray-500">The workspace key is tenant-local and is passed unchanged to the installation boundary.</p>
      </div>

      <section className="space-y-3">
        <div className="flex items-center gap-2"><Store className="h-5 w-5 text-brand-600" /><h2 className="text-lg font-semibold text-gray-900">Published teams</h2></div>
        {publicationsQuery.isLoading && <Spinner />}
        {!publicationsQuery.isLoading && publications.length === 0 && <EmptyState title="No published teams" description="No public marketplace publications are currently available to this tenant." />}
        <div className="grid gap-4 lg:grid-cols-2">
          {publications.map((publication) => <article key={publication.id} className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <div className="flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-wide text-gray-400">Public publication · v{shortId(publication.team_version_id)}</p><h3 className="mt-1 font-semibold text-gray-900">{publication.title}</h3><p className="mt-1 text-sm text-gray-500">{publication.summary || "No summary provided."}</p></div><Badge status={publication.status} /></div>
            <div className="mt-4 grid gap-2 text-xs text-gray-500"><span>Published {formatDate(publication.published_at)}</span><span>Publication {shortId(publication.id)}</span></div>
            <div className="mt-5 flex justify-end"><Button size="sm" onClick={() => setSelected(publication)}><Download className="h-3.5 w-3.5" /> Review & install</Button></div>
          </article>)}
        </div>
      </section>

      {selected && <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
        <div className="flex items-start justify-between gap-4"><div><p className="text-xs uppercase tracking-wide text-gray-400">Installation review</p><h2 className="mt-1 text-lg font-semibold text-gray-900">{selected.title}</h2><p className="mt-1 text-sm text-gray-500">Source publication {shortId(selected.id)} · version {shortId(selected.team_version_id)}</p></div><button className="text-sm text-gray-500 hover:text-gray-900" onClick={() => setSelected(null)}>Close</button></div>
        <div className="mt-4 grid gap-3 md:grid-cols-3"><div className="rounded-lg bg-gray-50 p-3"><p className="text-xs text-gray-400">Customer acceptance</p><p className="mt-1 text-sm font-medium text-gray-700">Not implied</p></div><div className="rounded-lg bg-gray-50 p-3"><p className="text-xs text-gray-400">Production deployment</p><p className="mt-1 text-sm font-medium text-gray-700">Not implied</p></div><div className="rounded-lg bg-gray-50 p-3"><p className="text-xs text-gray-400">Trust basis</p><p className="mt-1 text-sm font-medium text-gray-700">Recorded evidence only</p></div></div>
        <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">Installing creates tenant-local definitions and provenance. It does not provision an AI Employee instance or deploy anything to production.</div>
        <div className="mt-5 flex justify-end"><Button loading={installMutation.isPending} onClick={() => installMutation.mutate({ id: selected.id, workspaceKey: workspace.trim() })} disabled={!workspace.trim()}><CheckCircle2 className="h-4 w-4" /> Install tenant-local copy</Button></div>
      </section>}
    </div>
  </>);
}
