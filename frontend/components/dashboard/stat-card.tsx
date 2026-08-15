import type { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export function StatCard({ icon: Icon, label, value, hint, href }: { icon: LucideIcon; label: string; value: string | number; hint?: string; href?: string }) {
  const content = <Card className="h-full"><CardContent className="flex items-start gap-3"><div className="rounded-xl bg-brand-50 p-2.5 text-brand-600"><Icon className="h-5 w-5" /></div><div className="min-w-0"><p className="text-xs font-medium uppercase tracking-wide text-gray-400">{label}</p><p className="mt-1 text-2xl font-semibold text-gray-900">{value}</p>{hint && <p className="mt-1 text-xs text-gray-500">{hint}</p>}</div></CardContent></Card>;
  return href ? <a href={href} className="block transition hover:-translate-y-0.5">{content}</a> : content;
}
