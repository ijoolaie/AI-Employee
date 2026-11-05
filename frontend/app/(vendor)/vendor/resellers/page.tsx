"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2 } from "lucide-react";
import { api, getErrorMessage } from "@/lib/api";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useI18n } from "@/lib/i18n/provider";

interface Reseller { id: string; name: string; slug: string; status: string; tenant_kind: string; parent_tenant_id: string | null; }
const emptyForm = { name: "", slug: "", admin_email: "", full_name: "" };
async function listResellers() {
  const response = await api.get<{ success: boolean; data: Reseller[] }>("/edition/vendor/resellers");
  if (!response.data.success) throw new Error("Unable to load resellers");
  return response.data.data;
}

export default function VendorResellersPage() {
  const { locale } = useI18n();
  const fa = locale === "fa";
  const qc = useQueryClient();
  const [form, setForm] = useState(emptyForm);
  const [createdInvitation, setCreatedInvitation] = useState<{ token: string; email: string; expiresAt: string } | null>(null);
  const resellers = useQuery({ queryKey: ["vendor-resellers"], queryFn: listResellers });
  const create = useMutation({
    mutationFn: async () => {
      const response = await api.post<{ success: boolean; data: { tenant: Reseller; invitation_token: string; invitation_expires_at: string } }>("/edition/vendor/resellers", {
        name: form.name.trim(), slug: form.slug.trim(), admin_email: form.admin_email.trim(),
        full_name: form.full_name.trim() || undefined,
      });
      if (!response.data.success) throw new Error("Unable to create reseller");
      return response.data.data;
    },
    onSuccess: async (data) => { setCreatedInvitation({ token: data.invitation_token, email: form.admin_email.trim(), expiresAt: data.invitation_expires_at }); setForm(emptyForm); await qc.invalidateQueries({ queryKey: ["vendor-resellers"] }); await qc.invalidateQueries({ queryKey: ["vendor-license-targets"] }); },
  });
  const canCreate = form.name.trim().length >= 2 && /^[a-z0-9][a-z0-9-]{1,99}$/.test(form.slug.trim()) && form.admin_email.trim().length >= 3;

  return <>
    <Header title={fa ? "مدیریت نمایندگی‌ها" : "Reseller management"} description={fa ? "ایجاد و مدیریت نمایندگی‌های مستقیم زیرمجموعه این Vendor." : "Create and review resellers directly under this vendor."} />
    <div className="space-y-6 p-6">
      <Card><CardHeader><CardTitle>{fa ? "ایجاد نمایندگی جدید" : "Create a reseller"}</CardTitle></CardHeader><CardContent>
        <p className="mb-4 text-sm text-gray-500">{fa ? "برای مدیر نمایندگی یک حساب کاربری ساخته می‌شود. رمز عبور باید حداقل ۱۲ نویسه داشته باشد." : "Creates a reseller tenant and sends its administrator a one-time invitation. The account stays inactive until payment or an approved Demo grant."}</p>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="grid gap-1 text-sm"><span>{fa ? "نام نمایندگی" : "Reseller name"}</span><input aria-label="Reseller name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="rounded-lg border px-3 py-2" autoComplete="organization" /></label>
          <label className="grid gap-1 text-sm"><span>{fa ? "شناسه (slug)" : "Slug"}</span><input aria-label="Reseller slug" value={form.slug} onChange={e => setForm({ ...form, slug: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "-") })} placeholder="example-reseller" className="rounded-lg border px-3 py-2" /></label>
          <label className="grid gap-1 text-sm"><span>{fa ? "ایمیل مدیر" : "Admin email"}</span><input aria-label="Admin email" type="email" value={form.admin_email} onChange={e => setForm({ ...form, admin_email: e.target.value })} className="rounded-lg border px-3 py-2" autoComplete="email" /></label>
          <label className="grid gap-1 text-sm md:col-span-2"><span>{fa ? "نام کامل مدیر (اختیاری)" : "Admin full name (optional)"}</span><input aria-label="Admin full name" value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} className="rounded-lg border px-3 py-2" autoComplete="name" /></label>
        </div>
        {create.isError && <p role="alert" className="mt-3 text-sm text-red-600">{getErrorMessage(create.error)}</p>}
        {createdInvitation && <div className="mt-3 rounded-lg border p-3 text-sm"><p className="font-medium">Invitation for {createdInvitation.email}. Share this one-time token securely; it is shown only once.</p><a className="mt-2 inline-block text-brand-700 underline" href="/accept-invitation">Open invitation acceptance page</a><code className="mt-2 block break-all rounded bg-gray-50 p-2">{createdInvitation.token}</code><p className="mt-1 text-xs text-gray-500">Expires {new Date(createdInvitation.expiresAt).toLocaleString()}</p></div>}
        <button disabled={!canCreate || create.isPending} onClick={() => create.mutate()} className="mt-4 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">{create.isPending ? (fa ? "در حال ایجاد..." : "Creating...") : (fa ? "ایجاد نمایندگی" : "Create reseller")}</button>
      </CardContent></Card>
      <Card><CardHeader><CardTitle>{fa ? "نمایندگی‌های مستقیم" : "Direct resellers"}</CardTitle></CardHeader><CardContent className="overflow-x-auto p-0">
        {resellers.isLoading ? <p className="p-6 text-sm text-gray-500">{fa ? "در حال دریافت..." : "Loading resellers..."}</p> : resellers.isError ? <p role="alert" className="p-6 text-sm text-red-600">{getErrorMessage(resellers.error)}</p> : resellers.data?.length === 0 ? <div className="p-10 text-center"><Building2 className="mx-auto h-8 w-8 text-gray-300" /><p className="mt-3 font-medium">{fa ? "هنوز نمایندگی‌ای ساخته نشده است" : "No resellers yet"}</p><p className="mt-1 text-sm text-gray-500">{fa ? "با فرم بالا اولین نمایندگی زیرمجموعه را ایجاد کنید." : "Create your first direct reseller using the form above."}</p></div> : <table className="w-full text-start text-sm"><thead><tr className="border-b bg-gray-50 text-xs uppercase text-gray-500"><th className="px-5 py-3 text-start">{fa ? "نمایندگی" : "Reseller"}</th><th className="px-5 py-3 text-start">{fa ? "وضعیت" : "Status"}</th><th className="px-5 py-3 text-start">{fa ? "شناسه" : "Slug"}</th></tr></thead><tbody>{resellers.data?.map(r => <tr key={r.id} className="border-b border-gray-50"><td className="px-5 py-4 font-medium">{r.name}</td><td className="px-5 py-4">{r.status}</td><td className="px-5 py-4 text-gray-500">{r.slug}</td></tr>)}</tbody></table>}
      </CardContent></Card>
    </div>
  </>;
}
