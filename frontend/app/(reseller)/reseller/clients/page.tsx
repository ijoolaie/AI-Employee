"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2 } from "lucide-react";
import { api } from "@/lib/api";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useI18n } from "@/lib/i18n/provider";
import { resellerMessages } from "@/lib/i18n/reseller";

interface ClientSummary { id: string; name: string; slug: string; status: string; tenant_kind: string; created_at: string }

async function getClients() {
  const response = await api.get<{ success: boolean; data: ClientSummary[] }>("/edition/reseller/customers");
  if (!response.data.success) throw new Error("Unable to load clients");
  return response.data.data;
}

export default function ResellerClientsPage() {
  const { locale } = useI18n();
  const m = resellerMessages[locale];
  const qc = useQueryClient();
  const [form, setForm] = useState({ name: "", slug: "", admin_email: "", admin_password: "", full_name: "" });
  const clients = useQuery({ queryKey: ["reseller-clients"], queryFn: getClients });
  const action = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      api.post("/edition/reseller/customers/" + id + "/" + (status === "active" ? "suspend" : "resume")),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reseller-clients"] }),
  });
  const create = useMutation({
    mutationFn: () => api.post("/edition/reseller/customers", {
      name: form.name.trim(), slug: form.slug.trim(), admin_email: form.admin_email.trim(),
      admin_password: form.admin_password, full_name: form.full_name.trim() || undefined,
    }),
    onSuccess: () => {
      setForm({ name: "", slug: "", admin_email: "", admin_password: "", full_name: "" });
      qc.invalidateQueries({ queryKey: ["reseller-clients"] });
    },
  });
  const canCreate = form.name.trim().length >= 2 && form.slug.trim().length >= 2 && form.admin_email.trim().length >= 3 && form.admin_password.length >= 12;

  return <>
    <Header title={m.clientsTitle} description={m.clientsDescription} />
    <div className="space-y-6 p-6">
      <Card><CardHeader><CardTitle>{m.createClient}</CardTitle></CardHeader><CardContent>
        <div className="grid gap-4 md:grid-cols-2">
          <input aria-label={m.clientName} value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder={m.clientName} className="rounded-lg border px-3 py-2 text-sm" />
          <input aria-label={m.clientSlug} value={form.slug} onChange={e => setForm({ ...form, slug: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "-") })} placeholder={m.clientSlug} className="rounded-lg border px-3 py-2 text-sm" />
          <input aria-label={m.adminEmail} type="email" value={form.admin_email} onChange={e => setForm({ ...form, admin_email: e.target.value })} placeholder={m.adminEmail} className="rounded-lg border px-3 py-2 text-sm" />
          <input aria-label={m.adminPassword} type="password" value={form.admin_password} onChange={e => setForm({ ...form, admin_password: e.target.value })} placeholder={m.adminPassword} className="rounded-lg border px-3 py-2 text-sm" />
          <input aria-label={m.fullNameOptional} value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} placeholder={m.fullNameOptional} className="rounded-lg border px-3 py-2 text-sm md:col-span-2" />
        </div>
        {create.isError && <p className="mt-3 text-sm text-red-600">{m.createClientError}</p>}
        {create.isSuccess && <p className="mt-3 text-sm text-emerald-600">{m.createClientSuccess}</p>}
        <button disabled={!canCreate || create.isPending} onClick={() => create.mutate()} className="mt-4 rounded-lg px-4 py-2 text-sm font-medium text-white disabled:opacity-50">{create.isPending ? m.creatingClient : m.createClient}</button>
      </CardContent></Card>
      <Card><CardHeader><CardTitle>{m.clientPortfolio}</CardTitle></CardHeader><CardContent className="overflow-x-auto p-0">
        {clients.isLoading ? <p className="p-6 text-sm text-gray-500">{m.clientsLoading}</p> : clients.isError ? <p className="p-6 text-sm text-red-600">{m.clientsError}</p> : clients.data?.length === 0 ? <div className="p-10 text-center"><Building2 className="mx-auto h-8 w-8 text-gray-300" /><p className="mt-3 font-medium">{m.noClientTenants}</p><p className="mt-1 text-sm text-gray-500">{m.noClientTenantsText}</p></div> : <table className="w-full text-start text-sm"><thead><tr className="border-b bg-gray-50 text-xs uppercase text-gray-500"><th className="px-5 py-3 text-start">{m.client}</th><th className="px-5 py-3 text-start">{m.status}</th><th className="px-5 py-3 text-start">{m.created}</th><th className="px-5 py-3 text-end">{m.action}</th></tr></thead><tbody>{clients.data?.map(client => <tr key={client.id} className="border-b border-gray-50"><td className="px-5 py-4"><p className="font-medium text-gray-900">{client.name}</p><p className="text-xs text-gray-500">{client.slug}</p></td><td className="px-5 py-4"><span className={client.status === "active" ? "rounded-full bg-emerald-50 px-2 py-1 text-xs text-emerald-700" : "rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-600"}>{client.status === "active" ? m.active : m.disabled}</span></td><td className="px-5 py-4 text-gray-500">{new Date(client.created_at).toLocaleDateString(locale === "fa" ? "fa-IR" : "en-US")}</td><td className="px-5 py-4 text-end"><button disabled={action.isPending} onClick={() => action.mutate({ id: client.id, status: client.status })} className="rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium hover:bg-gray-50 disabled:opacity-50">{client.status === "active" ? m.suspend : m.activate}</button></td></tr>)}</tbody></table>}
      </CardContent></Card>
    </div>
  </>;
}