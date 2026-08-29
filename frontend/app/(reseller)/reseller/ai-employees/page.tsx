"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Bot, Plus } from "lucide-react";
import { listEmployees } from "@/lib/api";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ResellerAIEmployeesPage() {
  const employees = useQuery({ queryKey: ["reseller-ai-employees"], queryFn: listEmployees });
  return <>
    <Header title="AI Employees" description="Your reseller's internal AI workforce. Client AI employees remain isolated inside each client workspace." />
    <div className="p-6"><Card><CardHeader className="flex flex-row items-center justify-between"><CardTitle>Internal AI workforce</CardTitle><Link href="/employees/new" className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-3 py-2 text-sm font-medium text-white"><Plus className="h-4 w-4" />New AI employee</Link></CardHeader><CardContent>{employees.isLoading ? <p className="text-sm text-gray-500">Loading…</p> : employees.isError ? <p className="text-sm text-red-600">Unable to load AI employees.</p> : employees.data?.length === 0 ? <div className="rounded-lg border border-dashed p-8 text-center"><Bot className="mx-auto h-8 w-8 text-gray-300" /><p className="mt-3 font-medium">No internal AI employees</p><p className="mt-1 text-sm text-gray-500">Create AI roles for reseller operations such as support triage, sales, marketing, finance, or account management.</p></div> : <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{employees.data?.map(employee => <Link key={employee.id} href={`/employees/${employee.id}`} className="rounded-lg border border-gray-200 p-4 hover:border-brand-200 hover:bg-brand-50/30"><div className="flex items-center gap-2"><Bot className="h-4 w-4 text-brand-600" /><p className="font-medium">{employee.name}</p></div><p className="mt-1 text-xs text-gray-500">{employee.slug} · {employee.kind}</p><p className="mt-3 text-xs">{employee.is_active ? "Active" : "Disabled"}</p></Link>)}</div>}</CardContent></Card></div>
  </>;
}
