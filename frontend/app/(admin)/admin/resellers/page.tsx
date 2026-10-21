"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2 } from "lucide-react";
import { useI18n } from "@/lib/i18n/provider";
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

async function listVendorLicenseTargets() {
  const response = await api.get<{ success: boolean; data: Reseller[] }>("/edition/vendor/tenants");
  if (!response.data.success) throw new Error("Unable to load license targets");
  return response.data.data;
}

export default function AdminResellersPage() {
  const qc = useQueryClient();
  const { t, locale } = useI18n();
  const m = t.vendorResellers;
  const fa = locale === "fa";
  const [form, setForm] = useState({ name: "", slug: "", admin_email: "", admin_password: "", full_name: "" });
  const [licenseForm, setLicenseForm] = useState({ tenant_id: "", feature_codes: "", expires_in_days: "365" });
  const resellers = useQuery({ queryKey: ["vendor-resellers"], queryFn: listResellers });
  const licenseTargets = useQuery({ queryKey: ["vendor-license-targets"], queryFn: listVendorLicenseTargets });
  const issueLicense = useMutation({
    mutationFn: () => api.post("/edition/licenses/vendor/tenants/" + licenseForm.tenant_id, {
      feature_codes: licenseForm.feature_codes.split(",").map(code => code.trim()).filter(Boolean),
      expires_in_days: licenseForm.expires_in_days.trim() ? Number(licenseForm.expires_in_days) : undefined,
      metadata: { source: "vendor_admin_ui" },
    }),
    onSuccess: () => {
      setLicenseForm({ ...licenseForm, feature_codes: "" });
      qc.invalidateQueries({ queryKey: ["vendor-license-targets"] });
    },
  });
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
  const featureCodes = licenseForm.feature_codes.split(",").map(code => code.trim()).filter(Boolean);
  const canIssueLicense = Boolean(licenseForm.tenant_id) && featureCodes.length > 0 &&
    (!licenseForm.expires_in_days.trim() || (Number(licenseForm.expires_in_days) >= 1 && Number(licenseForm.expires_in_days) <= 3650));

  const statusLabel = (status: string) => ({
    active: m.active,
    suspended: m.suspended,
    deprovisioned: m.deprovisioned,
  }[status] ?? status);

  return <>
    <Header title={m.title} description={m.description} />
    <div className="space-y-6 p-6">
      <Card>
        <CardHeader><CardTitle>{fa ? "صدور دستی مجوز تجاری" : "Manually issue a commercial license"}</CardTitle></CardHeader>
        <CardContent>
          <p className="mb-4 text-sm text-gray-500">{fa ? "برای یک نمایندگی یا مشتری موجود در ساختار همین Vendor مجوز صادر کنید. هر مجوز فعال باید قابلیت‌های مجاز را مشخص کند." : "Issue a license to an existing reseller or customer in this vendor hierarchy. Each active license must specify its authorized feature codes."}</p>
          {licenseTargets.isError ? <p role="alert" className="mb-3 text-sm text-red-600">{getErrorMessage(licenseTargets.error)}</p> : null}
          <div className="grid gap-4 md:grid-cols-3">
            <label className="grid gap-1 text-sm">
              <span>{fa ? "مستأجر مقصد" : "Target tenant"}</span>
              <select aria-label={fa ? "مستأجر مقصد" : "Target tenant"} value={licenseForm.tenant_id} onChange={e => setLicenseForm({ ...licenseForm, tenant_id: e.target.value })} className="rounded-lg border px-3 py-2" disabled={licenseTargets.isLoading}>
                <option value="">{fa ? "انتخاب نمایندگی یا مشتری" : "Select reseller or customer"}</option>
                {licenseTargets.data?.map(target => <option key={target.id} value={target.id}>{target.name} ({target.tenant_kind}) — {target.slug}</option>)}
              </select>
            </label>
            <label className="grid gap-1 text-sm md:col-span-2">
              <span>{fa ? "کدهای قابلیت (با ویرگول جدا کنید)" : "Feature codes (comma-separated)"}</span>
              <input aria-label={fa ? "کدهای قابلیت" : "Feature codes"} value={licenseForm.feature_codes} onChange={e => setLicenseForm({ ...licenseForm, feature_codes: e.target.value })} placeholder="tool:send_email, tool:sales_forecast" className="rounded-lg border px-3 py-2" />
            </label>
            <label className="grid gap-1 text-sm">
              <span>{fa ? "مدت اعتبار به روز (خالی = بدون انقضا)" : "Validity in days (blank = no expiry)"}</span>
              <input aria-label={fa ? "مدت اعتبار به روز" : "Validity in days"} type="number" min="1" max="3650" value={licenseForm.expires_in_days} onChange={e => setLicenseForm({ ...licenseForm, expires_in_days: e.target.value })} className="rounded-lg border px-3 py-2" />
            </label>
          </div>
          {issueLicense.isError && <p role="alert" className="mt-3 text-sm text-red-600">{getErrorMessage(issueLicense.error)}</p>}
          {issueLicense.isSuccess && <p role="status" className="mt-3 text-sm text-emerald-600">{fa ? "مجوز صادر شد." : "License issued successfully."}</p>}
          <button disabled={!canIssueLicense || issueLicense.isPending || licenseTargets.isLoading} onClick={() => issueLicense.mutate()} className="mt-4 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">{issueLicense.isPending ? (fa ? "در حال صدور..." : "Issuing...") : (fa ? "صدور مجوز" : "Issue license")}</button>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>{m.createTitle}</CardTitle></CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <input aria-label={m.name} value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder={m.name} className="rounded-lg border px-3 py-2 text-sm" />
            <input aria-label={m.slug} value={form.slug} onChange={e => setForm({ ...form, slug: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "-") })} placeholder={m.slugPlaceholder} className="rounded-lg border px-3 py-2 text-sm" />
            <input aria-label={m.adminEmail} type="email" value={form.admin_email} onChange={e => setForm({ ...form, admin_email: e.target.value })} placeholder={m.adminEmail} className="rounded-lg border px-3 py-2 text-sm" />
            <input aria-label={m.adminPassword} type="password" value={form.admin_password} onChange={e => setForm({ ...form, admin_password: e.target.value })} placeholder={m.adminPasswordPlaceholder} className="rounded-lg border px-3 py-2 text-sm" />
            <input aria-label={m.adminFullName} value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} placeholder={m.adminFullNamePlaceholder} className="rounded-lg border px-3 py-2 text-sm md:col-span-2" />
          </div>
          {create.isError && <p role="alert" className="mt-3 text-sm text-red-600">{m.createError}</p>}
          {create.isSuccess && <p className="mt-3 text-sm text-emerald-600">{m.created}</p>}
          <button disabled={!canCreate || create.isPending} onClick={() => create.mutate()} className="mt-4 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">{create.isPending ? m.creating : m.create}</button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>{m.portfolio}</CardTitle></CardHeader>
        <CardContent className="overflow-x-auto p-0">
          {resellers.isLoading ? <p className="p-6 text-sm text-gray-500">{m.loading}</p> :
            resellers.isError ? <p role="alert" className="p-6 text-sm text-red-600">{m.error}</p> :
            resellers.data?.length === 0 ? <div className="p-10 text-center"><Building2 className="mx-auto h-8 w-8 text-gray-300" /><p className="mt-3 font-medium">{m.empty}</p><p className="mt-1 text-sm text-gray-500">{m.emptyDescription}</p></div> :
            <table className="w-full text-start text-sm">
              <thead><tr className="border-b bg-gray-50 text-xs uppercase text-gray-500"><th className="px-5 py-3">{m.reseller}</th><th className="px-5 py-3">{m.status}</th><th className="px-5 py-3">{m.release}</th><th className="px-5 py-3">{m.actions}</th></tr></thead>
              <tbody>{resellers.data?.map(r => <tr key={r.id} className="border-b border-gray-50">
                <td className="px-5 py-4"><p className="font-medium">{r.name}</p><p className="text-xs text-gray-500">{r.slug}</p></td>
                <td className="px-5 py-4">{statusLabel(r.status)}</td>
                <td className="px-5 py-4 text-xs text-gray-500">{r.vendor_release_tag ?? "—"}{r.delivery_revision ? " / " + r.delivery_revision : ""}</td>
                <td className="px-5 py-4"><div className="flex gap-2">
                  {r.status !== "deprovisioned" && <button disabled={action.isPending} onClick={() => action.mutate({ id: r.id, status: r.status })} className="rounded-lg border px-3 py-1.5 text-xs">{r.status === "active" ? m.suspend : m.resume}</button>}
                  {r.status !== "deprovisioned" && <button disabled={deprovision.isPending} onClick={() => deprovision.mutate(r.id)} className="rounded-lg border border-red-200 px-3 py-1.5 text-xs text-red-700">{m.deprovision}</button>}
                </div></td>
              </tr>)}</tbody>
            </table>}
        </CardContent>
      </Card>
    </div>
  </>;
}
