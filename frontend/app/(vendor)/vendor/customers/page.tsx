"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2 } from "lucide-react";
import { api, getErrorMessage } from "@/lib/api";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useI18n } from "@/lib/i18n/provider";

interface Customer { id: string; name: string; slug: string; status: string; tenant_kind: string; created_at: string }
interface ProvisionResult { tenant: Customer; invitation_token: string; invitation_expires_at: string }
const emptyForm = { name: "", slug: "", admin_email: "", full_name: "" };

async function listCustomers() {
  const response = await api.get<{ success: boolean; data: Customer[] }>("/edition/vendor/customers");
  if (!response.data.success) throw new Error("Unable to load direct customers");
  return response.data.data;
}

export default function VendorCustomersPage() {
  const { locale } = useI18n();
  const fa = locale === "fa";
  const qc = useQueryClient();
  const [form, setForm] = useState(emptyForm);
  const [invitation, setInvitation] = useState<{ token: string; email: string; expiresAt: string } | null>(null);
  const customers = useQuery({ queryKey: ["vendor-customers"], queryFn: listCustomers });

  const create = useMutation({
    mutationFn: async () => {
      const response = await api.post<{ success: boolean; data: ProvisionResult }>("/edition/vendor/customers", {
        name: form.name.trim(),
        slug: form.slug.trim(),
        admin_email: form.admin_email.trim(),
        full_name: form.full_name.trim() || undefined,
      });
      if (!response.data.success) throw new Error("Unable to create Customer tenant");
      return response.data.data;
    },
    onSuccess: async (data) => {
      setInvitation({ token: data.invitation_token, email: form.admin_email.trim(), expiresAt: data.invitation_expires_at });
      setForm(emptyForm);
      await qc.invalidateQueries({ queryKey: ["vendor-customers"] });
      await qc.invalidateQueries({ queryKey: ["vendor-license-targets"] });
    },
  });

  const lifecycle = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      api.post("/edition/vendor/customers/" + id + "/" + (status === "active" ? "suspend" : "resume")),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["vendor-customers"] }),
  });

  const deprovision = useMutation({
    mutationFn: (id: string) => api.post("/edition/vendor/customers/" + id + "/deprovision"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["vendor-customers"] }),
  });

  const canCreate = form.name.trim().length >= 2 &&
    /^[a-z0-9][a-z0-9-]{1,99}$/.test(form.slug.trim()) &&
    form.admin_email.trim().length >= 3;

  return <>
    <Header
      title={fa ? "مشتریان مستقیم" : "Direct customers"}
      description={fa ? "مشتریان مستقیمی که مستقیماً زیرمجموعه این Vendor هستند." : "Customer tenants owned directly by this Vendor, separate from Reseller-managed customers."}
    />
    <div className="space-y-6 p-6">
      <Card>
        <CardHeader><CardTitle>{fa ? "ایجاد مشتری مستقیم" : "Create a direct Customer"}</CardTitle></CardHeader>
        <CardContent>
          <p className="mb-4 text-sm text-gray-500">{fa ? "حساب مدیر از طریق دعوت‌نامه یک‌بارمصرف ایجاد می‌شود و فعال‌سازی فضای کاری به پرداخت یا Demo تأییدشده وابسته است." : "Creates a direct Customer tenant and a one-time administrator invitation. Workspace access remains gated by verified payment or an approved Demo grant."}</p>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="grid gap-1 text-sm"><span>{fa ? "نام مشتری" : "Customer name"}</span><input aria-label="Customer name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="rounded-lg border px-3 py-2" autoComplete="organization" /></label>
            <label className="grid gap-1 text-sm"><span>Slug</span><input aria-label="Customer slug" value={form.slug} onChange={e => setForm({ ...form, slug: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "-") })} placeholder="example-customer" className="rounded-lg border px-3 py-2" /></label>
            <label className="grid gap-1 text-sm"><span>{fa ? "ایمیل مدیر" : "Administrator email"}</span><input aria-label="Administrator email" type="email" value={form.admin_email} onChange={e => setForm({ ...form, admin_email: e.target.value })} className="rounded-lg border px-3 py-2" autoComplete="email" /></label>
            <label className="grid gap-1 text-sm md:col-span-2"><span>{fa ? "نام کامل مدیر (اختیاری)" : "Administrator full name (optional)"}</span><input aria-label="Administrator full name" value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} className="rounded-lg border px-3 py-2" autoComplete="name" /></label>
          </div>
          {create.isError && <p role="alert" className="mt-3 text-sm text-red-600">{getErrorMessage(create.error)}</p>}
          {invitation && <div className="mt-3 rounded-lg border p-3 text-sm"><p className="font-medium">One-time invitation for {invitation.email}. Share this token securely; it is shown only once.</p><a className="mt-2 inline-block text-brand-700 underline" href="/accept-invitation">Open invitation acceptance page</a><code className="mt-2 block break-all rounded bg-gray-50 p-2">{invitation.token}</code><p className="mt-1 text-xs text-gray-500">Expires {new Date(invitation.expiresAt).toLocaleString()}</p></div>}
          <button disabled={!canCreate || create.isPending} onClick={() => create.mutate()} className="mt-4 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">{create.isPending ? (fa ? "در حال ایجاد..." : "Creating...") : (fa ? "ایجاد مشتری" : "Create Customer")}</button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>{fa ? "مشتریان مستقیم این Vendor" : "Customers directly owned by this Vendor"}</CardTitle></CardHeader>
        <CardContent className="overflow-x-auto p-0">
          {customers.isLoading ? <p className="p-6 text-sm text-gray-500">{fa ? "در حال دریافت..." : "Loading customers..."}</p>
            : customers.isError ? <p role="alert" className="p-6 text-sm text-red-600">{getErrorMessage(customers.error)}</p>
            : customers.data?.length === 0 ? <div className="p-10 text-center"><Building2 className="mx-auto h-8 w-8 text-gray-300" /><p className="mt-3 font-medium">{fa ? "هنوز مشتری مستقیمی وجود ندارد" : "No direct Customers yet"}</p><p className="mt-1 text-sm text-gray-500">{fa ? "اولین مشتری مستقیم خود را ایجاد کنید." : "Create your first direct Customer using the form above."}</p></div>
            : <table className="w-full text-start text-sm"><thead><tr className="border-b bg-gray-50 text-xs uppercase text-gray-500"><th className="px-5 py-3 text-start">{fa ? "مشتری" : "Customer"}</th><th className="px-5 py-3 text-start">{fa ? "وضعیت" : "Status"}</th><th className="px-5 py-3 text-start">Slug</th><th className="px-5 py-3 text-end">{fa ? "عملیات" : "Actions"}</th></tr></thead><tbody>{customers.data?.map(customer => <tr key={customer.id} className="border-b border-gray-50"><td className="px-5 py-4 font-medium">{customer.name}</td><td className="px-5 py-4">{customer.status}</td><td className="px-5 py-4 text-gray-500">{customer.slug}</td><td className="px-5 py-4 text-end"><div className="flex flex-wrap justify-end gap-2"><button disabled={lifecycle.isPending || deprovision.isPending || customer.status === "deprovisioned"} onClick={() => lifecycle.mutate({ id: customer.id, status: customer.status })} className="rounded-lg border px-3 py-1.5 text-xs font-medium hover:bg-gray-50 disabled:opacity-50">{customer.status === "active" ? (fa ? "تعلیق" : "Suspend") : (fa ? "فعال‌سازی" : "Resume")}</button>{customer.status !== "deprovisioned" && <button disabled={deprovision.isPending || lifecycle.isPending} onClick={() => { if (window.confirm(fa ? "این مشتری غیرفعال دائمی شود؟" : "Deprovision this Customer permanently?")) deprovision.mutate(customer.id); }} className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-50 disabled:opacity-50">{fa ? "حذف نهایی" : "Deprovision"}</button>}</div></td></tr>)}</tbody></table>}
          {(lifecycle.isError || deprovision.isError) && <p role="alert" className="p-4 text-sm text-red-600">{getErrorMessage(lifecycle.error ?? deprovision.error)}</p>}
        </CardContent>
      </Card>
    </div>
  </>;
}
