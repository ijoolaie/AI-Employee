"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2 } from "lucide-react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, getErrorMessage } from "@/lib/api";

interface Reseller {
  id: string;
  name: string;
  slug: string;
  status: string;
  tenant_kind: string;
  parent_tenant_id: string | null;
  vendor_release_tag: string | null;
  delivery_revision: string | null;
}

async function listResellers() {
  const response = await api.get<{ success: boolean; data: Reseller[] }>("/edition/vendor/resellers");
  if (!response.data.success) throw new Error("Unable to load resellers");
  return response.data.data;
}

export default function AdminResellersPage() {
  const qc = useQueryClient();
  const [form, setForm] = useState({ name: "", slug: "", admin_email: "", admin_password: "", full_name: "" });
  const resellers = useQuery({ queryKey: ["vendor-resellers"], queryFn: listResellers });
  const action = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      api.post("/edition/vendor/resellers/" + id + "/" + (status === "active" ? "suspend" : status === "suspended" ? "resume" : "resume")),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["vendor-resellers"] }),
  });
  const deprovision = useMutation({
    mutationFn: (id: string) => api.post("/edition/vendor/resellers/" + id + "/deprovision"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["vendor-resellers"] }),
  });
  const create = useMutation({
    mutationFn: () => api.post("/edition/vendor/resellers", {
      name: form.name.trim(),
      slug: form.slug.trim(),
      admin_email: form.admin_email.trim(),
      admin_password: form.admin_password,
      full_name: form.full_name.trim() || undefined,
    }),
    onSuccess: () => {
      setForm({ name: "", slug: "", admin_email: "", admin_password: "", full_name: "" });
      qc.invalidateQueries({ queryKey: ["vendor-resellers"] });
    },
  });
  const canCreate = form.name.trim().length >= 2 && form.slug.trim().length >= 2 &&
    form.admin_email.trim().length >= 3 && form.admin_password.length >= 12;

  return <>
    <Header title="Resellers" description="Manage direct reseller tenants from the vendor control plane." />
    <div className="space-y-6 p-6">
      <Card>
        <CardHeader><CardTitle>Create reseller</CardTitle></CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <input aria-label="Reseller name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Reseller name" className="rounded-lg border px-3 py-2 text-sm" />
            <input aria-label="Reseller slug" value={form.slug} onChange={e => setForm({ ...form, slug: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "-") })} placeholder="reseller-slug" className="rounded-lg border px-3 py-2 text-sm" />
            <input aria-label="Admin email" type="email" value={form.admin_email} onChange={e => setForm({ ...form, admin_email: e.target.value })} placeholder="Admin email" className="rounded-lg border px-3 py-2 text-sm" />
            <input aria-label="Admin password" type="password" value={form.admin_password} onChange={e => setForm({ ...form, admin_password: e.target.value })} placeholder="Admin password (12+ characters)" className="rounded-lg border px-3 py-2 text-sm" />
            <input aria-label="Admin full name" value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} placeholder="Admin full name (optional)" className="rounded-lg border px-3 py-2 text-sm md:col-span-2" />
          </div>
          {create.isError && <p className="mt-3 text-sm text-red-600">{getErrorMessage(create.error)}</p>}
          {create.isSuccess && <p className="mt-3 text-sm text-emerald-600">Reseller created successfully.</p>}
          <button disabled={!canCreate || create.isPending} onClick={() => create.mutate()} className="mt-4 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">{create.isPending ? "Creating..." : "Create reseller"}</button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Reseller portfolio</CardTitle></CardHeader>
        <CardContent className="overflow-x-auto p-0">
          {resellers.isLoading ? <p className="p-6 text-sm text-gray-500">Loading resellers...</p> :
            resellers.isError ? <p className="p-6 text-sm text-red-600">{getErrorMessage(resellers.error)}</p> :
            resellers.data?.length === 0 ? <div className="p-10 text-center"><Building2 className="mx-auto h-8 w-8 text-gray-300" /><p className="mt-3 font-medium">No reseller tenants</p><p className="mt-1 text-sm text-gray-500">Create the first direct reseller from this control plane.</p></div> :
            <table className="w-full text-left text-sm">
              <thead><tr className="border-b bg-gray-50 text-xs uppercase text-gray-500"><th className="px-5 py-3">Reseller</th><th className="px-5 py-3">Status</th><th className="px-5 py-3">Release</th><th className="px-5 py-3">Actions</th></tr></thead>
              <tbody>{resellers.data?.map(r => <tr key={r.id} className="border-b border-gray-50">
                <td className="px-5 py-4"><p className="font-medium">{r.name}</p><p className="text-xs text-gray-500">{r.slug}</p></td>
                <td className="px-5 py-4">{r.status}</td>
                <td className="px-5 py-4 text-xs text-gray-500">{r.vendor_release_tag ?? "—"}{r.delivery_revision ? " / " + r.delivery_revision : ""}</td>
                <td className="px-5 py-4"><div className="flex gap-2">
                  {r.status !== "deprovisioned" && <button disabled={action.isPending} onClick={() => action.mutate({ id: r.id, status: r.status })} className="rounded-lg border px-3 py-1.5 text-xs">{r.status === "active" ? "Suspend" : "Resume"}</button>}
                  {r.status !== "deprovisioned" && <button disabled={deprovision.isPending} onClick={() => deprovision.mutate(r.id)} className="rounded-lg border border-red-200 px-3 py-1.5 text-xs text-red-700">Deprovision</button>}
                </div></td>
              </tr>)}</tbody>
            </table>}
        </CardContent>
      </Card>
    </div>
  </>;
}
