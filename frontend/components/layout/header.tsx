"use client";

import { useAuthStore } from "@/lib/auth-store";
import { useI18n } from "@/lib/i18n/provider";
import { resellerMessages } from "@/lib/i18n/reseller";
import { usePathname, useRouter } from "next/navigation";

interface HeaderProps { title: string; description?: string; actions?: React.ReactNode; }

export function Header({ title, description, actions }: HeaderProps) {
  const tenant = useAuthStore((s) => s.tenant);
  const { locale, t } = useI18n();
  const rm = resellerMessages[locale];
  const pathname = usePathname();
  const router = useRouter();
  const customerLinks = [["/dashboard", t.nav.overview], ["/chat", t.nav.chat], ["/employees", t.nav.employees], ["/workflows", t.nav.workflows], ["/customers", t.nav.customers], ["/orders", t.nav.orders], ["/settings", t.nav.settings]] as const;
  const resellerLinks = [["/reseller/dashboard", rm.overview], ["/reseller/clients", rm.clients], ["/reseller/team", rm.humanEmployees], ["/reseller/ai-employees", rm.aiEmployees], ["/reseller/support", rm.clientSupport], ["/reseller/settings", rm.settings]] as const;
  const adminLinks = [["/admin", t.nav.overview], ["/admin/tenants", locale === "fa" ? "تننت‌ها" : "Tenants"], ["/admin/operations", locale === "fa" ? "عملیات" : "Operations"], ["/admin/audit", locale === "fa" ? "حسابرسی" : "Audit"], ["/admin/ai-employees", t.nav.employees]] as const;
  const mobileLinks = pathname.startsWith("/admin") ? adminLinks : pathname.startsWith("/reseller") ? resellerLinks : customerLinks;
  const fallback = pathname.startsWith("/admin") ? "/admin" : pathname.startsWith("/reseller") ? "/reseller/dashboard" : "/dashboard";

  return <header className="flex items-start justify-between gap-4 border-b border-gray-200 bg-white px-6 py-5">
    <div><h1 className="text-xl font-semibold tracking-tight text-gray-900">{title}</h1>{description && <p className="mt-0.5 text-sm text-gray-500">{description}</p>}</div>
    <div className="flex items-center gap-3">
      <select aria-label={locale === "fa" ? "پیمایش" : "Navigate"} value={mobileLinks.find(([href]) => pathname === href || pathname.startsWith(href + "/"))?.[0] ?? fallback} onChange={(e) => router.push(e.target.value)} className="h-9 max-w-32 rounded-lg border border-gray-200 bg-white px-2 text-xs md:hidden">{mobileLinks.map(([href,label]) => <option key={href} value={href}>{label}</option>)}</select>
      {actions}
      {tenant && <span className="hidden rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600 sm:inline-flex">{tenant.slug}</span>}
    </div>
  </header>;
}
