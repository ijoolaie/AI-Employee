"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Copy, KeyRound, Plus, ShieldCheck, Trash2 } from "lucide-react";
import { createApiKey, getErrorMessage, listApiKeys, revokeApiKey } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function ApiKeysPage() {
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [newKey, setNewKey] = useState<string | null>(null);
  const keys = useQuery({ queryKey: ["api-keys"], queryFn: listApiKeys });
  const create = useMutation({
    mutationFn: () => createApiKey({ name: name.trim() }),
    onSuccess: (data) => { setNewKey(data.key); setName(""); qc.invalidateQueries({ queryKey: ["api-keys"] }); },
  });
  const revoke = useMutation({
    mutationFn: revokeApiKey,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["api-keys"] }),
  });
  const copy = async () => { if (newKey) await navigator.clipboard?.writeText(newKey); };

  return <>
    <Header title="API Keys" description="Create and revoke tenant-scoped service credentials." />
    <div className="space-y-6 p-6">
      {newKey && <Card className="border-amber-200 bg-amber-50"><CardHeader><CardTitle className="text-amber-900">New API key — copy it now</CardTitle></CardHeader><CardContent><p className="mb-3 text-sm text-amber-800">For security, the full secret is shown only once.</p><div className="flex gap-2"><code className="min-w-0 flex-1 overflow-auto rounded-lg bg-white p-3 text-xs">{newKey}</code><Button variant="secondary" onClick={copy}><Copy className="h-4 w-4" />Copy</Button><Button variant="secondary" onClick={() => setNewKey(null)}>Done</Button></div></CardContent></Card>}
      <div className="grid gap-6 lg:grid-cols-[1fr_2fr]">
        <Card><CardHeader><CardTitle className="flex items-center gap-2"><Plus className="h-4 w-4" />Create key</CardTitle></CardHeader><CardContent className="space-y-4">
          <input value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Production automation" className="h-10 w-full rounded-lg border border-gray-300 px-3 text-sm" />
          <Button disabled={!name.trim() || create.isPending} onClick={() => create.mutate()}><KeyRound className="h-4 w-4" />{create.isPending ? "Creating…" : "Create API key"}</Button>
          {create.error && <p className="text-sm text-red-600">{getErrorMessage(create.error)}</p>}
          <div className="rounded-lg bg-gray-50 p-3 text-xs text-gray-500"><ShieldCheck className="mr-1 inline h-4 w-4" />Keys are tenant-scoped and can authenticate API requests with <code>X-API-Key</code>.</div>
        </CardContent></Card>
        <Card><CardHeader><CardTitle>Active credentials</CardTitle></CardHeader><CardContent>
          {keys.isLoading ? <p className="text-sm text-gray-500">Loading…</p> : keys.error ? <p className="text-sm text-red-600">{getErrorMessage(keys.error)}</p> : (keys.data ?? []).length === 0 ? <p className="text-sm text-gray-500">No API keys yet.</p> :
          <div className="divide-y">{(keys.data ?? []).map(k => <div key={k.id} className="flex flex-wrap items-center justify-between gap-3 py-3"><div><div className="flex items-center gap-2"><span className="font-medium">{k.name}</span><Badge status={k.is_active ? "active" : "revoked"} /></div><p className="mt-1 font-mono text-xs text-gray-500">{k.key_prefix}•••• · created {formatDate(k.created_at)}</p>{k.last_used_at && <p className="text-xs text-gray-400">Last used {formatDate(k.last_used_at)}</p>}</div>{k.is_active && <Button variant="secondary" size="sm" disabled={revoke.isPending} onClick={() => revoke.mutate(k.id)}><Trash2 className="h-4 w-4" />Revoke</Button>}</div>)}</div>}
        </CardContent></Card>
      </div>
    </div>
  </>;
}
