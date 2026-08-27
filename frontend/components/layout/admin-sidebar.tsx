"use client";

import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/auth-store";
import { LayoutDashboard, LogOut, ShieldCheck, Users, ArrowLeft, ClipboardCheck, Activity, ScrollText, PlugZap, Bot } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

const groups = [
  { label: "Control Plane", items: [
    { href: "/admin", label: "Overview", icon: LayoutDashboard },
    { href: "/admin/tenants", label: "Tenants", icon: Users },
    { href: "/admin/operations", label: "Operations", icon: Activity },
    { href: "/admin/audit", label: "Audit Logs", icon: ScrollText },
  ]},
  { label: "Internal Workforce", items: [
    { href: "/admin/ai-employees", label: "Internal AI Employees", icon: Bot },
  ]},
  { label: "Engineering", items: [
    { href: "/admin/validation", label: "Validation", icon: ClipboardCheck },
    { href: "/admin/providers", label: "AI Providers", icon: PlugZap },
  ]},
];

export function AdminSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { logout } = useAuthStore();
  function handleLogout() { logout(); router.push("/login"); }

  return <aside className="flex h-screen w-64 flex-col border-r border-slate-800 bg-slate-950 text-slate-200">
    <div className="flex items-center gap-3 border-b border-slate-800 px-5 py-4"><div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600"><ShieldCheck className="h-5 w-5 text-white" /></div><div><p className="text-sm font-semibold text-white">Platform Control Plane</p><p className="text-xs text-slate-400">Vendor operations</p></div></div>
    <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4">{groups.map(group => <div key={group.label}><p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">{group.label}</p><div className="space-y-0.5">{group.items.map(item => { const active = pathname === item.href || pathname.startsWith(item.href + "/"); return <Link key={item.href} href={item.href} className={cn("flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium", active ? "bg-slate-800 text-white" : "text-slate-400 hover:bg-slate-900 hover:text-white")}><item.icon className="h-4 w-4" />{item.label}</Link>; })}</div></div>)}</nav>
    <div className="space-y-1 border-t border-slate-800 px-3 py-3"><Link href="/dashboard" className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-400 hover:bg-slate-900 hover:text-white"><ArrowLeft className="h-4 w-4" />Client Workspace</Link><button onClick={handleLogout} className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-400 hover:bg-slate-900 hover:text-white"><LogOut className="h-4 w-4" />Sign out</button></div>
  </aside>;
}
