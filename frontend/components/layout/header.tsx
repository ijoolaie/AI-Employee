"use client";

import { useAuthStore } from "@/lib/auth-store";
import { usePathname, useRouter } from "next/navigation";

interface HeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}

export function Header({ title, description, actions }: HeaderProps) {
  const tenant = useAuthStore((s) => s.tenant);
  const pathname = usePathname();
  const router = useRouter();
  const customerLinks = [["/dashboard", "Overview"], ["/chat", "AI Chat"], ["/employees", "Employees"], ["/workflows", "Workflows"], ["/runs", "Runs"], ["/knowledge", "Knowledge"], ["/memory", "Memory"], ["/analytics", "Analytics"], ["/developer", "Developer"], ["/settings", "Settings"]] as const;
  const adminLinks = [["/admin", "Overview"], ["/admin/tenants", "Tenants"], ["/admin/validation", "Validation"]] as const;
  const mobileLinks = pathname.startsWith("/admin") ? adminLinks : customerLinks;

  return (
    <header className="flex items-start justify-between gap-4 border-b border-gray-200 bg-white px-6 py-5">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-gray-900">
          {title}
        </h1>
        {description && (
          <p className="mt-0.5 text-sm text-gray-500">{description}</p>
        )}
      </div>
      <div className="flex items-center gap-3">
        <select aria-label="Navigate" value={mobileLinks.find(([href]) => pathname === href || pathname.startsWith(href + "/"))?.[0] ?? "/dashboard"} onChange={(e) => router.push(e.target.value)} className="h-9 max-w-32 rounded-lg border border-gray-200 bg-white px-2 text-xs md:hidden">{mobileLinks.map(([href,label]) => <option key={href} value={href}>{label}</option>)}</select>
        {actions}
        {tenant && (
          <span className="hidden rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600 sm:inline-flex">
            {tenant.slug}
          </span>
        )}
      </div>
    </header>
  );
}
