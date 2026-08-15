"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { listEmployeeTemplates, installEmployeeTemplate, getErrorMessage } from "@/lib/api";
import { useRouter } from "next/navigation";
export default function TemplatesPage(){
 const q=useQuery({queryKey:["employee-templates"],queryFn:listEmployeeTemplates}); const qc=useQueryClient(); const router=useRouter();
 const m=useMutation({mutationFn:installEmployeeTemplate,onSuccess:(e)=>{qc.invalidateQueries({queryKey:["employees"]});router.push(`/employees/${e.id}`)}});
 return <><Header title="Employee Templates" description="Start with a proven role, then customize tools and guardrails."/><div className="grid gap-4 p-6 md:grid-cols-3">{q.isLoading&&<Spinner/>}{q.error&&<div className="text-sm text-red-600">{getErrorMessage(q.error)}</div>}{(q.data??[]).map(t=><Card key={t.code}><CardHeader><CardTitle>{t.name}</CardTitle></CardHeader><CardContent className="space-y-4"><p className="text-sm text-gray-600">{t.description}</p><div className="text-xs text-gray-500">{t.allowed_tools.length} tools · Guardrails included</div><Button onClick={()=>m.mutate(t.code)} loading={m.isPending}>Install template</Button></CardContent></Card>)}</div></>;
}
