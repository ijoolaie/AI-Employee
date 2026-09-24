"use client";

import { useQuery } from "@tanstack/react-query";
import { BarChart3 } from "lucide-react";
import { ResellerSurface } from "@/components/reseller/reseller-surface";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { getUsageSummary } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { useI18n } from "@/lib/i18n/provider";

export default function ResellerUsagePage() {
  const { locale } = useI18n();
  const fa = locale === "fa";
  const m = fa ? {
    title:"مصرف و هزینه", description:"مصرف و هزینه ثبت‌شده در تننت نماینده را مشاهده کنید. داده تننت‌های مشتریان از این صفحه افشا نمی‌شود.",
    metrics:"خلاصه مصرف", calls:"فراخوانی هوش مصنوعی", tokens:"کل توکن‌ها", cost:"هزینه ثبت‌شده", latency:"میانگین تأخیر",
    breakdown:"تفکیک مصرف", provider:"ارائه‌دهنده", model:"مدل", success:"موفق", failed:"ناموفق", noData:"داده مصرفی وجود ندارد", loading:"در حال بارگذاری", error:"بارگذاری مصرف انجام نشد"
  } : {
    title:"Usage & Cost", description:"View recorded usage and cost for the reseller tenant. Client-tenant data is not exposed here.",
    metrics:"Usage summary", calls:"AI calls", tokens:"Total tokens", cost:"Recorded cost", latency:"Average latency",
    breakdown:"Usage breakdown", provider:"Provider", model:"Model", success:"Successful", failed:"Failed", noData:"No usage data", loading:"Loading", error:"Unable to load usage"
  };
  const q = useQuery({ queryKey:["reseller-usage"], queryFn:()=>getUsageSummary() });
  return <>
    <ResellerSurface title={m.title} description={m.description} capabilities={fa
      ? ["مصرف AI در تننت نماینده","هزینه ثبت‌شده و تفکیک ارائه‌دهنده/مدل","پایش فراخوانی موفق و ناموفق","مشاهده میانگین تأخیر","تفکیک مصرف قابل بررسی"]
      : ["AI usage in the reseller tenant","Recorded cost by provider/model","Successful and failed call monitoring","Average latency visibility","Inspectable usage breakdown"]} />
    <div className="space-y-4 p-6 pt-0">
      {q.isLoading && <div className="flex justify-center py-10" aria-label={m.loading}><Spinner /></div>}
      {q.isError && <Card><CardContent className="p-6 text-sm text-red-600">{m.error}</CardContent></Card>}
      {q.data && <>
        <Card><CardHeader><CardTitle className="flex items-center gap-2"><BarChart3 className="h-5 w-5"/>{m.metrics}</CardTitle></CardHeader><CardContent><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Metric title={m.calls} value={q.data.calls.toLocaleString()} /><Metric title={m.tokens} value={q.data.total_tokens.toLocaleString()} /><Metric title={m.cost} value={formatCurrency(q.data.cost_usd)} /><Metric title={m.latency} value={q.data.avg_latency_ms.toFixed(0) + " ms"} />
        </div></CardContent></Card>
        <Card><CardHeader><CardTitle>{m.breakdown}</CardTitle></CardHeader><CardContent className="p-0 overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b text-start text-xs uppercase text-gray-500"><th className="px-5 py-3">{m.provider}</th><th className="px-5 py-3">{m.model}</th><th className="px-5 py-3">{m.success}</th><th className="px-5 py-3">{m.failed}</th><th className="px-5 py-3">{m.cost}</th></tr></thead><tbody>{q.data.breakdown.map((b)=><tr key={b.provider + "-" + b.model} className="border-b"><td className="px-5 py-3">{b.provider}</td><td className="px-5 py-3">{b.model}</td><td className="px-5 py-3">{b.successful_calls.toLocaleString()}</td><td className="px-5 py-3">{b.failed_calls.toLocaleString()}</td><td className="px-5 py-3">{formatCurrency(b.cost_usd)}</td></tr>)}</tbody></table>{!q.data.breakdown.length && <p className="p-8 text-center text-sm text-gray-500">{m.noData}</p>}</CardContent></Card>
      </>}
    </div>
  </>;
}
function Metric({title,value}:{title:string;value:string}){return <div className="rounded-lg border p-4"><p className="text-xs text-gray-500">{title}</p><p className="mt-1 text-xl font-semibold">{value}</p></div>}
