"use client";
import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { EmptyState } from "@/components/ui/empty-state";
import { getAuditLogs, getErrorMessage } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { useI18n } from "@/lib/i18n/provider";
export default function LogsPage() {
 const {t}=useI18n(); const m=t.auditLogs;
 const q=useQuery({queryKey:["logs"],queryFn:()=>getAuditLogs({limit:100}),refetchInterval:10000});
 return <><Header title={m.title} description={m.description}/><div className="p-6"><Card><CardHeader><CardTitle>{m.recent}</CardTitle></CardHeader><CardContent>
 {q.isLoading?<Spinner/>:q.error?<div className="space-y-3"><p className="text-sm text-red-600">{getErrorMessage(q.error)||m.loadError}</p><Button variant="secondary" onClick={()=>void q.refetch()}>{m.retry}</Button></div>:(q.data??[]).length===0?<EmptyState title={m.empty} description={m.description}/>:<div className="overflow-x-auto"><table className="w-full min-w-[640px] text-start text-sm"><thead><tr className="border-b text-xs uppercase text-gray-500"><th className="p-3 text-start">{m.time}</th><th className="p-3 text-start">{m.action}</th><th className="p-3 text-start">{m.status}</th><th className="p-3 text-start">{m.request}</th></tr></thead><tbody>{(q.data??[]).map(l=><tr key={l.id} className="border-b last:border-0"><td className="p-3 text-gray-500">{formatDate(l.created_at)}</td><td className="p-3 font-medium">{l.action}</td><td className="p-3"><Badge status={l.status}/></td><td className="p-3 font-mono text-xs text-gray-500">{l.request_id?l.request_id.slice(0,16)+"…":"—"}</td></tr>)}</tbody></table></div>}
 </CardContent></Card></div></>;
}
