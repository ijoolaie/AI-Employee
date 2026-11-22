"use client";

import Link from "next/link";
import { Gamepad2, LayoutDashboard, Store, Users } from "lucide-react";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/auth-store";

export function ModeSwitch() {
  const pathname = usePathname();
  const world = pathname === "/world" || pathname.startsWith("/world/");
  const tenantKind = (useAuthStore((s) => s.tenant) as (ReturnType<typeof useAuthStore.getState>["tenant"] & { tenant_kind?: string }) | null)?.tenant_kind;
  return (
    <div className="flex flex-wrap items-center gap-1 rounded-lg border border-gray-200 bg-white p-1 shadow-sm">
      <Link href="/dashboard" className={cn("inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium", !world && "bg-gray-100 text-gray-900")}>
        <LayoutDashboard className="h-3.5 w-3.5" /> Customer / Business
      </Link>
      <Link href="/world" className={cn("inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium", world && "bg-brand-50 text-brand-700")}>
        <Gamepad2 className="h-3.5 w-3.5" /> World
      </Link>
      {(tenantKind === "reseller" || tenantKind === "vendor") && (
        <Link href="/reseller/dashboard" className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50">
          <Users className="h-3.5 w-3.5" /> Reseller
        </Link>
      )}
      {tenantKind === "vendor" && (
        <Link href="/vendor/dashboard" className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50">
          <Store className="h-3.5 w-3.5" /> Vendor
        </Link>
      )}
    </div>
  );
}
