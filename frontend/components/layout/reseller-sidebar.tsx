"use client";

import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/auth-store";
import { Building2, Bot, BarChart3, CreditCard, FileText, LayoutDashboard, LogOut, Settings, ShieldCheck, Users, Workflow, LifeBuoy, UserRound, PlugZap } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useI18n } from "@/lib/i18n/provider";
import { resellerMessages } from "@/lib/i18n/reseller";

export function ResellerSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, tenant, logout } = useAuthStore();
  const { locale, setLocale, t } = useI18n();
  const m = resellerMessages[locale];

  const groups = [
    { label: m.fallback, items: [
      { href: "/reseller/dashboard", label: m.overview, icon: LayoutDashboard },
      { href: "/reseller/clients", label: m.clients, icon: Building2 },
      { href: "/reseller/team", label: m.humanEmployees, icon: Users },
      { href: "/reseller/ai-employees", label: m.aiEmployees, icon: Bot },
    ]},
    { label: m.serviceDelivery, items: [
      { href: "/reseller/test-center", label: m.testCenter, icon: ShieldCheck },
      { href: "/reseller/support", label: m.clientSupport, icon: LifeBuoy },
      { href: "/reseller/workflows", label: m.workflows, icon: Workflow },
      { href: "/reseller/usage", label: m.usageCost, icon: BarChart3 },
      { href: "/reseller/integrations", label: m.integrations, icon: PlugZap },
    ]},
    { label: m.commercial, items: [
      { href: "/reseller/billing", label: m.billing, icon: CreditCard },
      { href: "/reseller/reports", label: m.reports, icon: FileText },
    ]},
    { label: m.settingsGroup, items: [
      { href: "/reseller/settings", label: m.settings, icon: Settings },
      { href: "/reseller/security", label: m.security, icon: ShieldCheck },
    ]},
  ];

  function handleLogout() { logout(); router.push("/login"); }

  return (
    <aside className="hidden h-screen w-72 shrink-0 flex-col border-r border-slate-800 bg-slate-950 text-slate-200 md:flex">
      <div className="flex items-center gap-3 border-b border-slate-800 px-5 py-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600"><Building2 className="h-4 w-4 text-white" /></div>
        <div className="min-w-0"><p className="truncate text-sm font-semibold text-white">{m.workspace}</p><p className="truncate text-xs text-slate-400">{tenant?.name ?? m.fallback}</p></div>
      </div>
      <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4">
        {groups.map(group => <div key={group.label}>
          <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">{group.label}</p>
          <div className="space-y-0.5">{group.items.map(item => {
            const active = pathname === item.href || pathname.startsWith(item.href + "/");
            return <Link key={item.href} href={item.href} className={cn("flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors", active ? "bg-slate-800 text-white" : "text-slate-400 hover:bg-slate-900 hover:text-white")}><item.icon className="h-4 w-4" />{item.label}</Link>;
          })}</div>
        </div>)}
      </nav>
      <div className="border-t border-slate-800 px-3 py-3">
        <div className="mb-2 flex items-center justify-between px-3"><span className="text-xs text-slate-500">{t.common.language}</span><div className="flex rounded-md border border-slate-700 text-[11px]"><button onClick={() => setLocale("en")} className={cn("px-2 py-1", locale === "en" ? "bg-slate-800 font-semibold" : "")}>EN</button><button onClick={() => setLocale("fa")} className={cn("px-2 py-1", locale === "fa" ? "bg-slate-800 font-semibold" : "")}>فا</button></div></div>
        <div className="mb-2 flex items-center gap-2 px-3 text-xs text-slate-400"><UserRound className="h-3.5 w-3.5" />{user?.full_name || user?.email}</div>
        <button onClick={handleLogout} className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-400 hover:bg-slate-900 hover:text-white"><LogOut className="h-4 w-4" />{m.signOut}</button>
      </div>
    </aside>
  );
}
