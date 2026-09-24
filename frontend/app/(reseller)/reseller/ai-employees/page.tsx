"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Bot, Plus } from "lucide-react";
import { listEmployees } from "@/lib/api";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useI18n } from "@/lib/i18n/provider";
import { resellerMessages } from "@/lib/i18n/reseller";

export default function ResellerAIEmployeesPage() {
  const { locale } = useI18n();
  const m = resellerMessages[locale];
  const employees = useQuery({ queryKey: ["reseller-ai-employees"], queryFn: listEmployees });
  return <>
    <Header title={m.aiTitle} description={m.aiDescription} />
    <div className="p-6"><Card><CardHeader className="flex flex-row items-center justify-between"><CardTitle>{m.internalAiWorkforce}</CardTitle><Link href="/employees/new" className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-3 py-2 text-sm font-medium text-white"><Plus className="h-4 w-4" />{m.newAiEmployee}</Link></CardHeader><CardContent>
      {employees.isLoading ? <p className="text-sm text-gray-500">{m.teamLoading}</p> : employees.isError ? <p className="text-sm text-red-600">Unable to load AI employees.</p> : employees.data?.length === 0 ? <div className="rounded-lg border border-dashed p-8 text-center"><Bot className="mx-auto h-8 w-8 text-gray-300" /><p className="mt-3 font-medium">{m.noInternalAi}</p><p className="mt-1 text-sm text-gray-500">{m.noInternalAiText}</p></div> : <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{employees.data?.map(employee => <Link key={employee.id} href={`/employees/${employee.id}`} className="rounded-lg border border-gray-200 p-4 hover:border-brand-200 hover:bg-brand-50/30"><div className="flex items-center gap-2"><Bot className="h-4 w-4 text-brand-600" /><p className="font-medium">{employee.name}</p></div><p className="mt-1 text-xs text-gray-500">{employee.slug} · {employee.kind}</p><p className="mt-3 text-xs">{employee.is_active ? m.active : m.disabled}</p></Link>)}</div>}
    </CardContent></Card></div>
  </>;
}
