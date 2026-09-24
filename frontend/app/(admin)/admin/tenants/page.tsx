"use client";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Badge } from "@/components/ui/badge";
import { getErrorMessage, listAdminTenants } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { useI18n } from "@/lib/i18n/provider";

export default function AdminTenantsPage() {
  const { locale } = useI18n();
  const fa = locale === "fa";
  const m = fa ? { title:"مستأجرها", description:"فهرست و استفاده از مستأجرهای پلتفرم", all:"همه مستأجرها", tenant:"مستأجر", status:"وضعیت", users:"کاربران", workflows:"گردش‌کارها", runs:"اجراها", cost:"هزینه", created:"ایجاد شده" } : { title:"Tenants", description:"Platform-wide tenant inventory and usage", all:"All tenants", tenant:"Tenant", status:"Status", users:"Users", workflows:"Workflows", runs:"Runs", cost:"Cost", created:"Created" };
  const { data, isLoading, error } = useQuery({ queryKey: ["admin-tenants"], queryFn: () => listAdminTenants(), refetchInterval: 30000 });
  return <><Header title={m.title} description={m.description} /><div className="p-6"><Card><CardHeader><CardTitle>{m.all}</CardTitle></CardHeader><CardContent className="p-0">{isLoading ? <Spinner /> : error ? <p className="p-5 text-sm text-red-700">{getErrorMessage(error)}</p> : <div className="overflow-x-auto"><table className="w-full text-start text-sm"><thead><tr className="border-b border-gray-100 text-xs uppercase text-gray-500"><th className="px-5 py-3">{m.tenant}</th><th className="px-5 py-3">{m.status}</th><th className="px-5 py-3">{m.users}</th><th className="px-5 py-3">{m.workflows}</th><th className="px-5 py-3">{m.runs}</th><th className="px-5 py-3">{m.cost}</th><th className="px-5 py-3">{m.created}</th></tr></thead><tbody>{data?.map(t => <tr key={t.id} className="border-b border-gray-50"><td className="px-5 py-3"><p className="font-medium">{t.name}</p><p className="text-xs text-gray-500">{t.slug}</p></td><td className="px-5 py-3"><Badge status={t.status}/></td><td className="px-5 py-3">{t.users}</td><td className="px-5 py-3">{t.workflows}</td><td className="px-5 py-3">{t.runs}</td><td className="px-5 py-3">{formatCurrency(t.cost_usd)}</td><td className="px-5 py-3 text-gray-500">{formatDate(t.created_at)}</td></tr>)}</tbody></table></div>}</CardContent></Card></div></>;
}
