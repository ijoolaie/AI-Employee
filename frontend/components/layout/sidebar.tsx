"use client";

import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/auth-store";
import { LayoutDashboard, LogOut, Settings, BarChart3, CreditCard, Sparkles, GitBranch, CalendarClock, ShieldCheck, BookOpen, Brain, ShoppingCart, TrendingUp, Activity, MessageCircle, Bot, Play, FileText, Radio, Package, PlugZap, ListChecks, UserRound, KeyRound, Users, Code2, FlaskConical } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useI18n } from "@/lib/i18n/provider";

const groups = [
  { label: "Business", items: [
    { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
    { href: "/customers", label: "Customers", icon: UserRound },
    { href: "/orders", label: "Orders", icon: ShoppingCart },
    { href: "/products", label: "Products", icon: Package },
    { href: "/sales", label: "Sales", icon: TrendingUp },
    { href: "/analytics", label: "Analytics", icon: BarChart3 },
    { href: "/reports", label: "Reports", icon: FileText },
  ]},
  { label: "People & AI", items: [
    { href: "/team", label: "Human Employees", icon: Users },
    { href: "/employees", label: "AI Employees", icon: Bot },
    { href: "/templates", label: "Employee Templates", icon: Sparkles },
    { href: "/workspace", label: "AI Workspace", icon: Sparkles },
    { href: "/chat", label: "AI Chat", icon: MessageCircle },
    { href: "/knowledge", label: "Knowledge Base", icon: BookOpen },
    { href: "/memory", label: "Memory", icon: Brain },
  ]},
  { label: "Customer Operations", items: [
    { href: "/inbox", label: "Unified Inbox", icon: ListChecks },
    { href: "/conversations", label: "Conversations", icon: MessageCircle },
    { href: "/channels", label: "Customer Channels", icon: Radio },
    { href: "/workflows", label: "Workflows", icon: GitBranch },
    { href: "/tasks", label: "Tasks", icon: ListChecks },
    { href: "/approvals", label: "Approvals", icon: ShieldCheck },
    { href: "/schedules", label: "Schedules", icon: CalendarClock },
  ]},
  { label: "Finance & Platform", items: [
    { href: "/billing", label: "Billing", icon: CreditCard },
    { href: "/invoices", label: "Invoices", icon: FileText },
    { href: "/usage", label: "Usage & Cost", icon: BarChart3 },
    { href: "/integrations", label: "Integrations", icon: PlugZap },
    { href: "/files", label: "Files", icon: FileText },
    { href: "/runs", label: "Runs", icon: Play },
    { href: "/test-center", label: "Test Center", icon: FlaskConical },
    { href: "/traces", label: "Trace Explorer", icon: Activity },
  ]},
  { label: "Developer", items: [
    { href: "/developer", label: "Developer Console", icon: Code2 },
    { href: "/api-keys", label: "API Keys", icon: KeyRound },
    { href: "/webhooks", label: "Webhooks", icon: Radio },
  ]},
  { label: "Settings", items: [
    { href: "/settings", label: "Settings", icon: Settings },
    { href: "/settings/security", label: "Security / Password", icon: KeyRound },
  ]},
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, tenant, logout } = useAuthStore();
  const { locale, setLocale, t } = useI18n();

  function handleLogout() {
    logout();
    router.push("/login");
  }

  return (
    <aside className="hidden h-screen w-72 shrink-0 flex-col border-r border-gray-200 bg-white md:flex">
      <div className="flex items-center gap-3 border-b border-gray-100 px-5 py-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600">
          <Sparkles className="h-4 w-4 text-white" />
        </div>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-gray-900">AI Employee</p>
          <p className="truncate text-xs text-gray-500">{tenant?.name ?? "Business Workspace"}</p>
        </div>
      </div>

      <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4">
        {groups.map((group) => (
          <div key={group.label}>
            <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-gray-400">{group.label}</p>
            <div className="space-y-0.5">
              {group.items.map((item) => {
                const active = pathname === item.href || pathname.startsWith(item.href + "/");
                return (
                  <Link key={item.href} href={item.href} className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    active ? "bg-brand-50 text-brand-700" : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                  )}>
                    <item.icon className="h-4 w-4 shrink-0" />
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-gray-100 px-3 py-3">
        <div className="mb-2 flex items-center justify-between px-3">
          <span className="text-xs text-gray-500">{t.common.language}</span>
          <div className="flex rounded-md border border-gray-200 text-[11px]">
            <button onClick={() => setLocale("en")} className={cn("px-2 py-1", locale === "en" ? "bg-gray-100 font-semibold" : "")}>EN</button>
            <button onClick={() => setLocale("fa")} className={cn("px-2 py-1", locale === "fa" ? "bg-gray-100 font-semibold" : "")}>فا</button>
          </div>
        </div>
        <div className="mb-2 truncate px-3 text-xs text-gray-500">{user?.full_name || user?.email}</div>
        <button onClick={handleLogout} className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-50 hover:text-gray-900">
          <LogOut className="h-4 w-4" />Sign out
        </button>
      </div>
    </aside>
  );
}
