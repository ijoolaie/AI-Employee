"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Workflow as WorkflowIcon, ExternalLink } from "lucide-react";
import { ResellerSurface } from "@/components/reseller/reseller-surface";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { listWorkflows } from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";

export default function ResellerWorkflowsPage() {
  const { locale } = useI18n();
  const m = locale === "fa" ? {
    title: "گردش‌کارهای خدمات", description: "اتوماسیون عملیات نماینده؛ گردش‌کارهای مشتریان داخل تننت همان مشتری باقی می‌مانند.",
    catalog: "گردش‌کارهای عملیاتی", catalogDescription: "گردش‌کارهای متعلق به این نماینده را مشاهده و مدیریت کنید.",
    manage: "مدیریت گردش‌کارها", loading: "در حال بارگذاری گردش‌کارها…", error: "بارگذاری گردش‌کارها انجام نشد.",
    empty: "هنوز گردش‌کاری وجود ندارد", emptyText: "برای اتوماسیون عملیات متعلق به نماینده یک گردش‌کار ایجاد کنید.",
    active: "فعال", disabled: "غیرفعال", builder: "سازنده", name: "نام", slug: "شناسه", status: "وضعیت", open: "باز کردن"
  } : {
    title: "Service Workflows", description: "Automation used by the reseller operation. Client workflows stay inside client tenants.",
    catalog: "Operational workflows", catalogDescription: "View and manage workflows owned by this reseller tenant.",
    manage: "Manage workflows", loading: "Loading workflows…", error: "Could not load workflows.",
    empty: "No reseller workflows yet", emptyText: "Create a workflow for reseller-owned operational automation.",
    active: "Active", disabled: "Disabled", builder: "Builder", name: "Name", slug: "Slug", status: "Status", open: "Open"
  };
  const q = useQuery({ queryKey: ["reseller-workflows"], queryFn: listWorkflows });
  return <>
    <ResellerSurface title={m.title} description={m.description} capabilities={locale === "fa"
      ? ["گردش‌کارهای داخلی پشتیبانی و ارجاع", "اتوماسیون پذیرش و تحویل مشتری", "گزارش‌های عملیاتی زمان‌بندی‌شده", "اقدامات تحت کنترل تأیید", "اجرا، تلاش مجدد و مشاهده حسابرسی گردش‌کار"]
      : ["Internal support and escalation workflows", "Client onboarding and handoff automation", "Scheduled operational reports", "Approval-controlled actions", "Workflow runs, retries, and audit visibility"]} />
    <div className="space-y-4 p-6 pt-0">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div><h2 className="text-lg font-semibold">{m.catalog}</h2><p className="text-sm text-gray-500">{m.catalogDescription}</p></div>
        <Button asChild><Link href="/workflows"><ExternalLink className="h-4 w-4" />{m.manage}</Link></Button>
      </div>
      {q.isLoading && <Card><CardContent className="flex justify-center py-10"><Spinner /></CardContent></Card>}
      {q.isError && <Card><CardContent className="p-6 text-sm text-red-600">{m.error}</CardContent></Card>}
      {!q.isLoading && !q.isError && (q.data?.length ? <Card><CardContent className="p-0 overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b text-start text-xs uppercase text-gray-500"><th className="px-5 py-3">{m.name}</th><th className="px-5 py-3">{m.slug}</th><th className="px-5 py-3">{m.status}</th><th className="px-5 py-3">{m.builder}</th></tr></thead><tbody>{q.data.map(w => <tr key={w.id} className="border-b"><td className="px-5 py-3"><Link className="font-medium text-brand-600 hover:underline" href={`/workflows/${w.id}`}>{w.name}</Link></td><td className="px-5 py-3 text-gray-600">{w.slug}</td><td className="px-5 py-3">{w.is_active ? m.active : m.disabled}</td><td className="px-5 py-3"><Link className="text-brand-600 hover:underline" href={`/workflows/${w.id}/builder`}>{m.builder}</Link></td></tr>)}</tbody></table></CardContent></Card> : <Card><CardContent className="flex flex-col items-center gap-2 p-10 text-center"><WorkflowIcon className="h-8 w-8 text-gray-300" /><p className="font-medium">{m.empty}</p><p className="text-sm text-gray-500">{m.emptyText}</p><Button asChild className="mt-2"><Link href="/workflows">{m.manage}</Link></Button></CardContent></Card>)}
    </div>
  </>;
}
