"use client";

import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/auth-store";
import { LayoutDashboard, LogOut, Settings, BarChart3, CreditCard, Sparkles, GitBranch, CalendarClock, ShieldCheck, BookOpen, Brain, ShoppingCart, TrendingUp, Activity, MessageCircle, Bot, Play, FileText, Radio, Package, PlugZap, ListChecks, UserRound, KeyRound, Users, Code2, FlaskConical, Store } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useI18n } from "@/lib/i18n/provider";

const groups = [
  { key: "business", label: "Business", items: [
    { href: "/dashboard", key: "overview", label: "Overview", icon: LayoutDashboard },
    { href: "/customers", key: "customers", label: "Customers", icon: UserRound },
    { href: "/orders", key: "orders", label: "Orders", icon: ShoppingCart },
    { href: "/products", key: "products", label: "Products", icon: Package },
    { href: "/sales", key: "sales", label: "Sales", icon: TrendingUp },
    { href: "/analytics", key: "analytics", label: "Analytics", icon: BarChart3 },
    { href: "/reports", key: "reports", label: "Reports", icon: FileText },
  ]},
  { key: "peopleAi", label: "People & AI", items: [
    { href: "/team", key: "team", label: "Human Employees", icon: Users },
    { href: "/employees", key: "employees", label: "AI Employees", icon: Bot },
    { href: "/templates", key: "templates", label: "Employee Templates", icon: Sparkles },
    { href: "/workspace", key: "workspace", label: "AI Workspace", icon: Sparkles },
    { href: "/chat", key: "chat", label: "AI Chat", icon: MessageCircle },
    { href: "/governance", key: "governance", label: "Workforce Governance", icon: ShieldCheck },
    { href: "/knowledge", key: "knowledge", label: "Knowledge Base", icon: BookOpen },
    { href: "/memory", key: "memory", label: "Memory", icon: Brain },
  ]},
  { key: "customerOperations", label: "Customer Operations", items: [
    { href: "/inbox", key: "inbox", label: "Unified Inbox", icon: ListChecks },
    { href: "/conversations", key: "conversations", label: "Conversations", icon: MessageCircle },
    { href: "/channels", key: "channels", label: "Customer Channels", icon: Radio },
    { href: "/workflows", key: "workflows", label: "Workflows", icon: GitBranch },
    { href: "/tasks", key: "tasks", label: "Tasks", icon: ListChecks },
    { href: "/approvals", key: "approvals", label: "Approvals", icon: ShieldCheck },
    { href: "/schedules", key: "schedules", label: "Schedules", icon: CalendarClock },
  ]},
  { key: "financePlatform", label: "Finance & Platform", items: [
    { href: "/billing", key: "billing", label: "Billing", icon: CreditCard },
    { href: "/invoices", key: "invoices", label: "Invoices", icon: FileText },
    { href: "/usage", key: "usage", label: "Usage & Cost", icon: BarChart3 },
    { href: "/integrations", key: "integrations", label: "Integrations", icon: PlugZap },
    { href: "/files", key: "files", label: "Files", icon: FileText },
    { href: "/runs", key: "runs", label: "Runs", icon: Play },
    { href: "/traces", key: "traces", label: "Trace Explorer", icon: Activity },
  ]},
  { key: "developer", label: "Developer", items: [
    { href: "/developer", key: "developerConsole", label: "Developer Console", icon: Code2 },
    { href: "/test-center", key: "testCenter", label: "Test Center", icon: FlaskConical },
    { href: "/marketplace", key: "marketplace", label: "Marketplace", icon: Store },
    { href: "/api-keys", key: "apiKeys", label: "API Keys", icon: KeyRound },
    { href: "/webhooks", key: "webhooks", label: "Webhooks", icon: Radio },
  ]},
  { key: "settings", label: "Settings", items: [
    { href: "/settings", key: "settings", label: "Settings", icon: Settings },
    { href: "/settings/security", key: "security", label: "Security / Password", icon: KeyRound },
  ]},
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, tenant, logout } = useAuthStore();
  const { locale, setLocale, t } = useI18n();
  const n = t.nav;

  function handleLogout() {
    logout();
    router.push("/login");
  }

  return (
    <aside className="hidden h-screen w-72 shrink-0 flex-col border-r border-gray-200 bg-white md:flex">
      <div className="flex items-center gap-3 border-b border-gray-100 px-5 py-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600"><Sparkles className="h-4 w-4 text-white" /></div>
        <div className="min-w-0"><p className="truncate text-sm font-semibold text-gray-900">AI Employee</p><p className="truncate text-xs text-gray-500">{tenant?.name ?? n.workspaceFallback}</p></div>
      </div>
      <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4">
        {groups.map((group) => <div key={group.label}><p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-gray-400">{(n as Record<string,string>)[group.key ?? group.label] ?? group.label}</p><div className="space-y-0.5">{group.items.map((item) => { const active = pathname === item.href || pathname.startsWith(item.href + "/"); return <Link key={item.href} href={item.href} className={cn("flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors", active ? "bg-brand-50 text-brand-700" : "text-gray-600 hover:bg-gray-50 hover:text-gray-900")}><item.icon className="h-4 w-4 shrink-0" />{(n as Record<string,string>)[item.key] ?? item.key}</Link>; })}</div></div>)}
      </nav>
      <div className="border-t border-gray-100 px-3 py-3">
        <div className="mb-2 flex items-center justify-between px-3"><span className="text-xs text-gray-500">{t.common.language}</span><div className="flex rounded-md border border-gray-200 text-[11px]"><button onClick={() => setLocale("en")} className={cn("px-2 py-1", locale === "en" ? "bg-gray-100 font-semibold" : "")}>EN</button><button onClick={() => setLocale("fa")} className={cn("px-2 py-1", locale === "fa" ? "bg-gray-100 font-semibold" : "")}>فا</button></div></div>
        <div className="mb-2 truncate px-3 text-xs text-gray-500">{user?.full_name || user?.email}</div>
        <button onClick={handleLogout} className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-50 hover:text-gray-900"><LogOut className="h-4 w-4" />{t.common.signOut}</button>
      </div>
    </aside>
  );
}
