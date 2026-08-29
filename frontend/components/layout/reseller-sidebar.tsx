"use client";

import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/auth-store";
import { Building2, Bot, BarChart3, CreditCard, FileText, LayoutDashboard, LogOut, Settings, ShieldCheck, Users, Workflow, LifeBuoy, UserRound, PlugZap } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useI18n } from "@/lib/i18n/provider";

const groups = [
  { label: "Reseller", items: [
    { href: "/reseller/dashboard", label: "Overview", icon: LayoutDashboard },
    { href: "/reseller/clients", label: "Clients", icon: Building2 },
    { href: "/reseller/team", label: "Human Employees", icon: Users },
    { href: "/reseller/ai-employees", label: "AI Employees", icon: Bot },
  ]},
  { label: "Service Delivery", items: [
    { href: "/reseller/support", label: "Client Support", icon: LifeBuoy },
    { href: "/reseller/workflows", label: "Workflows", icon: Workflow },
    { href: "/reseller/usage", label: "Usage & Cost", icon: BarChart3 },
    { href: "/reseller/integrations", label: "Integrations", icon: PlugZap },
  ]},
  { label: "Commercial", items: [
    { href: "/reseller/billing", label: "Billing", icon: CreditCard },
    { href: "/reseller/reports", label: "Reports", icon: FileText },
  ]},
  { label: "Settings", items: [
    { href: "/reseller/settings", label: "Settings", icon: Settings },
    { href: "/reseller/security", label: "Security", icon: ShieldCheck },
  ]},
];

export function ResellerSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, tenant, logout } = useAuthStore();
  const { locale, setLocale, t } = useI18n();

  function handleLogout() { logout(); router.push("/login"); }

  return (
    <aside className="hidden h-screen w-72 shrink-0 flex-col border-r border-slate-800 bg-slate-950 text-slate-200 md:flex">
      <div className="flex items-center gap-3 border-b border-slate-800 px-5 py-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600"><Building2 className="h-4 w-4 text-white" /></div>
        <div className="min-w-0"><p className="truncate text-sm font-semibold text-white">Reseller Workspace</p><p className="truncate text-xs text-slate-400">{tenant?.name ?? "Reseller"}</p></div>
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
        <button onClick={handleLogout} className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-400 hover:bg-slate-900 hover:text-white"><LogOut className="h-4 w-4" />Sign out</button>
      </div>
    </aside>
  );
}
