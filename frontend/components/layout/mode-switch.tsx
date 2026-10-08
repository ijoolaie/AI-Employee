"use client";

import Link from "next/link";
import { Gamepad2, LayoutDashboard } from "lucide-react";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

export function ModeSwitch() {
  const pathname = usePathname();
  const world = pathname === "/world" || pathname.startsWith("/world/");
  return (
    <div className="flex items-center gap-1 rounded-lg border border-gray-200 bg-white p-1 shadow-sm">
      <Link href="/dashboard" className={cn("inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium", !world && "bg-gray-100 text-gray-900")}>
        <LayoutDashboard className="h-3.5 w-3.5" /> Management
      </Link>
      <Link href="/world" className={cn("inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium", world && "bg-brand-50 text-brand-700")}>
        <Gamepad2 className="h-3.5 w-3.5" /> World
      </Link>
    </div>
  );
}
