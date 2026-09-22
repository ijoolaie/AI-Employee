"use client";

import Link from "next/link";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/lib/auth-store";
import { useI18n } from "@/lib/i18n/provider";

export default function SettingsPage() {
  const { user, tenant } = useAuthStore();
  const { t } = useI18n();
  const m = t.settings;
  return <>
    <Header title={m.title} description={m.description} />
    <div className="mx-auto max-w-2xl space-y-6 p-6">
      <Card><CardHeader><CardTitle>{m.profile}</CardTitle></CardHeader><CardContent className="space-y-3 text-sm">
        <Row label={m.email} value={user?.email}/><Row label={m.fullName} value={user?.full_name||"—"}/><Row label={m.userId} value={user?.id} mono/><Row label={m.status} value={user?.is_active?m.active:m.inactive}/>
      </CardContent></Card>
      <Card><CardHeader><CardTitle>{m.security}</CardTitle></CardHeader><CardContent className="space-y-3 text-sm"><p className="text-gray-600">{m.securityDescription}</p><Link href="/settings/security" className="inline-flex rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">{m.securityAction}</Link></CardContent></Card>
      <Card><CardHeader><CardTitle>{m.organization}</CardTitle></CardHeader><CardContent className="space-y-3 text-sm">
        <Row label={m.name} value={tenant?.name}/><Row label={m.slug} value={tenant?.slug} mono/><Row label={m.tenantId} value={tenant?.id} mono/><Row label={m.status} value={tenant?.status}/>
      </CardContent></Card>
      <Card><CardHeader><CardTitle>{m.related}</CardTitle></CardHeader><CardContent className="space-y-2 text-sm">
        <p className="text-gray-600">{m.relatedDescription}</p>
        <ul className="list-inside list-disc space-y-1 text-brand-700">
          <li><Link href="/billing" className="hover:underline">{m.billing}</Link></li>
          <li><Link href="/usage" className="hover:underline">{m.usage}</Link></li>
          <li><Link href="/knowledge" className="hover:underline">{m.knowledge}</Link></li>
          <li><Link href="/memory" className="hover:underline">{m.memory}</Link></li>
          <li><Link href="/team" className="hover:underline">{m.team}</Link></li>
          <li><Link href="/api-keys" className="hover:underline">{m.apiKeys}</Link></li>
        </ul>
        <p className="pt-2 text-xs text-gray-400">{m.teamNote}</p>
      </CardContent></Card>
    </div>
  </>;
}
function Row({label,value,mono}:{label:string;value?:string|null;mono?:boolean}) {
  return <div className="flex items-center justify-between gap-4 border-b border-gray-50 pb-2 last:border-0 last:pb-0"><span className="text-gray-500">{label}</span><span className={mono?"truncate font-mono text-xs text-gray-700":"truncate font-medium text-gray-900"}>{value??"—"}</span></div>;
}
