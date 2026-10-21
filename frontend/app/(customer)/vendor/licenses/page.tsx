"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, getErrorMessage } from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";

interface Target { id: string; name: string; slug: string; tenant_kind: string }
async function listTargets() {
  const response = await api.get<{ success: boolean; data: Target[] }>("/edition/vendor/tenants");
  if (!response.data.success) throw new Error("Unable to load license targets");
  return response.data.data;
}

export default function VendorLicensesPage() {
  const { locale } = useI18n();
  const fa = locale === "fa";
  const targets = useQuery({ queryKey: ["vendor-license-targets"], queryFn: listTargets });
  const [tenantId, setTenantId] = useState("");
  const [featureCodes, setFeatureCodes] = useState("");
  const [expiresInDays, setExpiresInDays] = useState("365");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const codes = featureCodes.split(",").map((code) => code.trim()).filter(Boolean);
  const validDays = !expiresInDays.trim() || (Number(expiresInDays) >= 1 && Number(expiresInDays) <= 3650);

  async function issueLicense() {
    setSubmitting(true); setMessage(""); setError("");
    try {
      await api.post("/edition/licenses/vendor/tenants/" + tenantId, {
        feature_codes: codes,
        expires_in_days: expiresInDays.trim() ? Number(expiresInDays) : undefined,
        metadata: { source: "vendor_license_page" },
      });
      setMessage(fa ? "\u0645\u062c\u0648\u0632 \u0628\u0627 \u0645\u0648\u0641\u0642\u06cc\u062a \u0635\u0627\u062f\u0631 \u0634\u062f." : "License issued successfully.");
      setFeatureCodes("");
      await targets.refetch();
    } catch (e) { setError(getErrorMessage(e)); }
    finally { setSubmitting(false); }
  }

  return <>
    <Header title={fa ? "\u0645\u062c\u0648\u0632\u0647\u0627\u06cc \u062a\u062c\u0627\u0631\u06cc" : "Commercial licenses"} description={fa ? "\u0635\u062f\u0648\u0631 \u0645\u062c\u0648\u0632 \u0628\u0631\u0627\u06cc \u0646\u0645\u0627\u06cc\u0646\u062f\u06af\u06cc\u200c\u0647\u0627 \u0648 \u0645\u0634\u062a\u0631\u06cc\u0627\u0646 \u0632\u06cc\u0631\u0645\u062c\u0645\u0648\u0639\u0647\u0654 \u0647\u0645\u06cc\u0646 Vendor" : "Issue licenses to resellers and customers in your vendor hierarchy."} />
    <div className="p-6">
      <Card>
        <CardHeader><CardTitle>{fa ? "\u0635\u062f\u0648\u0631 \u062f\u0633\u062a\u06cc \u0645\u062c\u0648\u0632 \u062a\u062c\u0627\u0631\u06cc" : "Manually issue a commercial license"}</CardTitle></CardHeader>
        <CardContent>
          <p className="mb-4 text-sm text-gray-500">{fa ? "\u06a9\u062f\u0647\u0627\u06cc \u0642\u0627\u0628\u0644\u06cc\u062a \u0631\u0627 \u0628\u0627 \u06a9\u0627\u0645\u0627 \u062c\u062f\u0627 \u06a9\u0646\u06cc\u062f. \u0641\u0642\u0637 \u062a\u0646\u0646\u062a\u200c\u0647\u0627\u06cc \u0645\u062c\u0627\u0632 \u062f\u0631 \u0633\u0627\u062e\u062a\u0627\u0631 \u0647\u0645\u06cc\u0646 Vendor \u0642\u0627\u0628\u0644 \u0627\u0646\u062a\u062e\u0627\u0628 \u0647\u0633\u062a\u0646\u062f." : "Enter authorized feature codes separated by commas. Only tenants in your vendor hierarchy are available."}</p>
          {targets.isLoading && <p className="text-sm text-gray-500">{fa ? "\u062f\u0631 \u062d\u0627\u0644 \u062f\u0631\u06cc\u0627\u0641\u062a..." : "Loading license targets..."}</p>}
          {targets.isError && <p role="alert" className="mb-3 text-sm text-red-600">{getErrorMessage(targets.error)}</p>}
          <div className="grid gap-4 md:grid-cols-3">
            <label className="grid gap-1 text-sm"><span>{fa ? "\u0645\u0634\u062a\u0631\u06cc / \u0646\u0645\u0627\u06cc\u0646\u062f\u06af\u06cc" : "Reseller / customer"}</span><select aria-label="License target" value={tenantId} onChange={(e) => setTenantId(e.target.value)} className="rounded-lg border px-3 py-2" disabled={targets.isLoading || targets.isError}><option value="">{fa ? "\u0627\u0646\u062a\u062e\u0627\u0628 \u0645\u0642\u0635\u062f" : "Select target"}</option>{targets.data?.map((target) => <option key={target.id} value={target.id}>{target.name} ({target.tenant_kind}) — {target.slug}</option>)}</select></label>
            <label className="grid gap-1 text-sm md:col-span-2"><span>{fa ? "\u06a9\u062f\u0647\u0627\u06cc \u0642\u0627\u0628\u0644\u06cc\u062a" : "Feature codes (comma-separated)"}</span><input aria-label="Feature codes" value={featureCodes} onChange={(e) => setFeatureCodes(e.target.value)} placeholder="tool:send_email, tool:sales_forecast" className="rounded-lg border px-3 py-2" /></label>
            <label className="grid gap-1 text-sm"><span>{fa ? "\u0645\u062f\u062a \u0627\u0639\u062a\u0628\u0627\u0631 \u0628\u0647 \u0631\u0648\u0632 (\u062e\u0627\u0644\u06cc = \u0628\u062f\u0648\u0646 \u0627\u0646\u0642\u0636\u0627)" : "Validity in days (blank = no expiry)"}</span><input aria-label="Validity in days" type="number" min="1" max="3650" value={expiresInDays} onChange={(e) => setExpiresInDays(e.target.value)} className="rounded-lg border px-3 py-2" /></label>
          </div>
          {error && <p role="alert" className="mt-3 text-sm text-red-600">{error}</p>}{message && <p role="status" className="mt-3 text-sm text-emerald-600">{message}</p>}
          <button disabled={!tenantId || codes.length === 0 || !validDays || submitting || targets.isLoading} onClick={issueLicense} className="mt-4 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">{submitting ? (fa ? "\u062f\u0631 \u062d\u0627\u0644 \u0635\u062f\u0648\u0631..." : "Issuing...") : (fa ? "\u0635\u062f\u0648\u0631 \u0645\u062c\u0648\u0632" : "Issue license")}</button>
        </CardContent>
      </Card>
    </div>
  </>;
}
