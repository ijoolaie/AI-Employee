"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { listEmployeeTemplates, installEmployeeTemplate, getErrorMessage } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useI18n } from "@/lib/i18n/provider";
export default function TemplatesPage(){
 const { t } = useI18n();
 const tx = t.employee;
 const q=useQuery({queryKey:["employee-templates"],queryFn:listEmployeeTemplates}); const qc=useQueryClient(); const router=useRouter();
 const m=useMutation({mutationFn:installEmployeeTemplate,onSuccess:(e)=>{qc.invalidateQueries({queryKey:["employees"]});router.push(`/employees/${e.id}`)}});
 return <><Header title={tx.templates} description={tx.templatesDescription}/><div className="grid gap-4 p-6 md:grid-cols-3">{q.isLoading&&<Spinner/>}{q.error&&<div className="space-y-2 text-sm text-red-600"><p>{getErrorMessage(q.error)}</p><Button variant="secondary" onClick={()=>void q.refetch()}>{tx.retry}</Button></div>}{(q.data??[]).map(t=><Card key={t.code}><CardHeader><CardTitle>{t.name}</CardTitle></CardHeader><CardContent className="space-y-4"><p className="text-sm text-gray-600">{t.description}</p><div className="text-xs text-gray-500">{t.allowed_tools.length} tools · Guardrails included</div><Button onClick={()=>m.mutate(t.code)} loading={m.isPending}>{tx.createEmployee}</Button></CardContent></Card>)}</div></>;
}
