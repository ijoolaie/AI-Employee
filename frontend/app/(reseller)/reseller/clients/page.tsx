"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2 } from "lucide-react";
import { api } from "@/lib/api";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ClientSummary { id: string; name: string; slug: string; status: string; tenant_kind: string; created_at: string }

async function getClients() {
  const response = await api.get<{ success: boolean; data: ClientSummary[] }>("/reseller-admin/clients");
  if (!response.data.success) throw new Error("Unable to load clients");
  return response.data.data;
}

export default function ResellerClientsPage() {
  const qc = useQueryClient();
  const clients = useQuery({ queryKey: ["reseller-clients"], queryFn: getClients });
  const action = useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => api.post(`/reseller-admin/clients/${id}/${status === "active" ? "suspend" : "activate"}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reseller-clients"] }),
  });

  return <>
    <Header title="Clients" description="Your directly managed customer tenants." />
    <div className="p-6"><Card><CardHeader><CardTitle>Client portfolio</CardTitle></CardHeader><CardContent className="p-0 overflow-x-auto">
      {clients.isLoading ? <p className="p-6 text-sm text-gray-500">Loading…</p> : clients.isError ? <p className="p-6 text-sm text-red-600">Unable to load client tenants.</p> : clients.data?.length === 0 ? <div className="p-10 text-center"><Building2 className="mx-auto h-8 w-8 text-gray-300" /><p className="mt-3 font-medium">No client tenants</p><p className="mt-1 text-sm text-gray-500">Client onboarding will create child customer tenants under this reseller.</p></div> : <table className="w-full text-left text-sm"><thead><tr className="border-b bg-gray-50 text-xs uppercase text-gray-500"><th className="px-5 py-3">Client</th><th className="px-5 py-3">Status</th><th className="px-5 py-3">Created</th><th className="px-5 py-3 text-right">Action</th></tr></thead><tbody>{clients.data?.map(client => <tr key={client.id} className="border-b border-gray-50"><td className="px-5 py-4"><p className="font-medium text-gray-900">{client.name}</p><p className="text-xs text-gray-500">{client.slug}</p></td><td className="px-5 py-4"><span className={client.status === "active" ? "rounded-full bg-emerald-50 px-2 py-1 text-xs text-emerald-700" : "rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-600"}>{client.status}</span></td><td className="px-5 py-4 text-gray-500">{new Date(client.created_at).toLocaleDateString()}</td><td className="px-5 py-4 text-right"><button disabled={action.isPending} onClick={() => action.mutate({ id: client.id, status: client.status })} className="rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium hover:bg-gray-50 disabled:opacity-50">{client.status === "active" ? "Suspend" : "Activate"}</button></td></tr>)}</tbody></table>}
    </CardContent></Card></div>
  </>;
}
