"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Building2, LayoutDashboard, LogOut, ShieldCheck, Users } from "lucide-react";
import { useAuthStore } from "@/lib/auth-store";
import { cn } from "@/lib/utils";
import { useI18n } from "@/lib/i18n/provider";

export function VendorSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, tenant, logout } = useAuthStore();
  const { locale, setLocale, t } = useI18n();
  const fa = locale === "fa";
  const items = [
    { href: "/vendor/dashboard", label: fa ? "نمای کلی" : "Overview", icon: LayoutDashboard },
    { href: "/vendor/resellers", label: fa ? "نمایندگی‌ها" : "Resellers", icon: Building2 },
    { href: "/vendor/customers", label: fa ? "مشتریان مستقیم" : "Direct customers", icon: Users },
    { href: "/vendor/licenses", label: fa ? "مجوزهای تجاری" : "Commercial licenses", icon: ShieldCheck },
  ];
  return <aside className="hidden h-screen w-72 shrink-0 flex-col border-r border-slate-800 bg-slate-950 text-slate-200 md:flex">
    <div className="border-b border-slate-800 px-5 py-4"><p className="text-sm font-semibold text-white">AI Employee · Vendor</p><p className="truncate text-xs text-slate-400">{tenant?.name ?? "Vendor workspace"}</p></div>
    <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">{items.map(item => { const active = pathname === item.href || pathname.startsWith(item.href + "/"); return <Link key={item.href} href={item.href} className={cn("flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium", active ? "bg-slate-800 text-white" : "text-slate-400 hover:bg-slate-900 hover:text-white")}><item.icon className="h-4 w-4" />{item.label}</Link>; })}</nav>
    <div className="border-t border-slate-800 px-3 py-3"><div className="mb-2 flex items-center justify-between px-3"><span className="text-xs text-slate-500">{t.common.language}</span><div className="flex rounded-md border border-slate-700 text-[11px]"><button onClick={() => setLocale("en")} className={cn("px-2 py-1", locale === "en" ? "bg-slate-800 font-semibold" : "")}>EN</button><button onClick={() => setLocale("fa")} className={cn("px-2 py-1", locale === "fa" ? "bg-slate-800 font-semibold" : "")}>فا</button></div></div><div className="mb-2 truncate px-3 text-xs text-slate-400">{user?.full_name || user?.email}</div><button onClick={() => { logout(); router.push("/login"); }} className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-400 hover:bg-slate-900 hover:text-white"><LogOut className="h-4 w-4" />{fa ? "خروج" : "Sign out"}</button></div>
  </aside>;
}
