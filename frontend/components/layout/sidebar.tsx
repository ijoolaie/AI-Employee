"use client";

import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/auth-store";
import { LayoutDashboard, LogOut, Settings, BarChart3, CreditCard, Sparkles, GitBranch, CalendarClock, Webhook, ShieldCheck, Code2, BookOpen, Brain, ShoppingCart, TrendingUp, Activity, MessageCircle, Bot, Play, FileText, Radio, Package, PlugZap, ListChecks, UserRound, Terminal, KeyRound, type LucideIcon } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useI18n } from "@/lib/i18n/provider";

type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  children?: NavItem[];
};

type NavGroup = {
  label: string;
  items: NavItem[];
};

const groups: NavGroup[] = [
  { label: "Business", items: [
    { href: "/dashboard", label: "Business Dashboard", icon: LayoutDashboard },
    { href: "/orders", label: "Orders", icon: ShoppingCart },
    { href: "/products", label: "Product Catalog", icon: Package },
    { href: "/sales", label: "Sales", icon: TrendingUp },
    { href: "/analytics", label: "Analytics", icon: BarChart3 },
    { href: "/reports", label: "Reports", icon: FileText },
    { href: "/billing", label: "Billing", icon: CreditCard },
    { href: "/invoices", label: "Invoices", icon: FileText },
  ]},
  { label: "AI Workspace", items: [
    { href: "/workspace", label: "AI Workspace", icon: Sparkles },
    { href: "/chat", label: "AI Chat", icon: MessageCircle },
    { href: "/employees", label: "AI Employees", icon: Bot },
    { href: "/templates", label: "Employee Templates", icon: Sparkles },
    { href: "/conversations", label: "Customer Conversations", icon: MessageCircle },
    { href: "/inbox", label: "Unified Inbox", icon: ListChecks },
    { href: "/customers", label: "Customers (CRM)", icon: UserRound },
    { href: "/channels", label: "Customer Channels", icon: Radio },
    { href: "/knowledge", label: "Knowledge Base", icon: BookOpen },
    { href: "/memory", label: "Memory", icon: Brain },
    { href: "/studio", label: "AI Studio", icon: Sparkles },
  ]},
  { label: "Operations", items: [
    { href: "/workflows", label: "Workflows", icon: GitBranch },
    { href: "/tasks", label: "Tasks", icon: ListChecks },
    { href: "/runs", label: "Runs", icon: Play },
    { href: "/approvals", label: "Approvals", icon: ShieldCheck },
    { href: "/schedules", label: "Schedules", icon: CalendarClock },
    { href: "/files", label: "Files", icon: FileText },
    { href: "/usage", label: "Usage & Cost", icon: BarChart3 },
    { href: "/traces", label: "Trace Explorer", icon: Activity },
  ]},
  { label: "Developer", items: [
    { href: "/developer", label: "Developer Console", icon: Code2 },
    { href: "/api-console", label: "API Console", icon: Terminal },
    { href: "/logs", label: "Logs", icon: FileText },
    { href: "/api-keys", label: "API Keys", icon: Code2 },
    { href: "/integrations", label: "Commerce Integrations", icon: PlugZap },
    { href: "/webhooks", label: "Webhooks", icon: Webhook },
    { href: "/privacy", label: "Privacy & GDPR", icon: ShieldCheck },
    { href: "/settings", label: "Settings", icon: Settings, children: [
      { href: "/settings/security", label: "Security / Password", icon: KeyRound },
    ] },
    { href: "/team", label: "Team & Roles", icon: UserRound },
  ]},
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, tenant, logout } = useAuthStore();
  const { locale, setLocale, t } = useI18n();
  function handleLogout() { logout(); router.push("/login"); }
  return <aside className="hidden h-screen w-72 shrink-0 flex-col border-r border-gray-200 bg-white md:flex">
    <div className="flex items-center gap-2 border-b border-gray-100 px-5 py-4">
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600"><Sparkles className="h-4 w-4 text-white" /></div>
      <div className="min-w-0"><p className="truncate text-sm font-semibold text-gray-900">AI Employee</p><p className="truncate text-xs text-gray-500">{tenant?.name ?? "Platform"}</p></div>
    </div>
    <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4">
      {user?.is_platform_admin && <Link href="/admin" className="flex items-center gap-3 rounded-lg bg-slate-950 px-3 py-2 text-sm font-medium text-white"><ShieldCheck className="h-4 w-4 shrink-0" />Platform Admin</Link>}
      {groups.map(group => <div key={group.label}>
        <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-gray-400">{group.label}</p>
        <div className="space-y-0.5">{group.items.map(item => {
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          return <div key={item.href}>
            <Link href={item.href} className={cn("flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors", active ? "bg-brand-50 text-brand-700" : "text-gray-600 hover:bg-gray-50 hover:text-gray-900")}><item.icon className="h-4 w-4 shrink-0" />{item.label}</Link>
            {item.children && active && <div className="ml-7 mt-0.5 space-y-0.5 border-l border-gray-200 pl-2">
              {item.children.map(child => {
                const childActive = pathname === child.href || pathname.startsWith(child.href + "/");
                return <Link key={child.href} href={child.href} className={cn("flex items-center gap-2 rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors", childActive ? "bg-brand-50 text-brand-700" : "text-gray-500 hover:bg-gray-50 hover:text-gray-900")}><child.icon className="h-3.5 w-3.5 shrink-0" />{child.label}</Link>;
              })}
            </div>}
          </div>;
        })}</div>
      </div>)}
    </nav>
    <div className="border-t border-gray-100 px-3 py-3"><div className="mb-2 flex items-center justify-between px-3"><span className="text-xs text-gray-500">{t.common.language}</span><div className="flex rounded-md border border-gray-200 text-[11px]"><button onClick={() => setLocale("en")} className={cn("px-2 py-1", locale === "en" ? "bg-gray-100 font-semibold" : "")}>EN</button><button onClick={() => setLocale("fa")} className={cn("px-2 py-1", locale === "fa" ? "bg-gray-100 font-semibold" : "")}>فا</button></div></div><div className="mb-2 truncate px-3 text-xs text-gray-500">{user?.email}</div><button onClick={handleLogout} className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-50 hover:text-gray-900"><LogOut className="h-4 w-4" />Sign out</button></div>
  </aside>;
}
