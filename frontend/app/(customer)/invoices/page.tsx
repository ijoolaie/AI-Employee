"use client";
import Link from "next/link";
import { useI18n } from "@/lib/i18n/provider";
import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card,CardContent,CardHeader,CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { getErrorMessage,listInvoices,getInvoiceSummary } from "@/lib/api";
export default function InvoicesPage(){
 const {t}=useI18n(); const m=t.invoices;
 const q=useQuery({queryKey:["invoices"],queryFn:()=>listInvoices()});
 const s=useQuery({queryKey:["invoice-summary"],queryFn:getInvoiceSummary});
 const retry=()=>{void q.refetch();void s.refetch();};
 if(q.isLoading||s.isLoading)return <><Header title={m.title} description={m.description}/><div className="p-6"><Spinner/></div></>;
 if(q.isError||s.isError)return <><Header title={m.title} description={m.description}/><div className="space-y-3 p-6"><p className="text-sm text-red-600">{getErrorMessage(q.error||s.error)||m.loadError}</p><Button variant="secondary" onClick={retry}>{m.retry}</Button></div></>;
 const invoices=q.data??[];
 return <><Header title={m.title} description={m.description}/><div className="space-y-6 p-6">
 <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><Metric title={m.total} value={String(s.data?.total_invoices??0)}/>{Object.entries(s.data?.counts_by_status??{}).slice(0,3).map(([k,v])=><Metric key={k} title={k} value={String(v)}/>)}</div>
 {invoices.length===0?<EmptyState title={m.title} description={m.loadError}/>:<Card><CardHeader><CardTitle>{m.register}</CardTitle></CardHeader><CardContent className="p-0 overflow-x-auto"><table className="w-full min-w-[720px] text-start text-sm"><thead><tr className="border-b text-xs uppercase text-gray-500"><th className="px-4 py-3 text-start">{m.number}</th><th className="px-4 py-3 text-start">{m.customer}</th><th className="px-4 py-3 text-start">{m.status}</th><th className="px-4 py-3 text-start">{m.totalLabel}</th><th className="px-4 py-3 text-start">{m.due}</th></tr></thead><tbody>{invoices.map(i=><tr key={String(i.id)} className="border-b border-gray-50"><td className="px-4 py-3"><Link className="font-medium text-brand-700 hover:underline" href={`/invoices/${i.id}`}>{i.number}</Link></td><td className="px-4 py-3">{i.customer_name}</td><td className="px-4 py-3">{i.status}</td><td className="px-4 py-3">{Number(i.total).toLocaleString()} {i.currency}</td><td className="px-4 py-3">{i.due_date??"—"}</td></tr>)}</tbody></table></CardContent></Card>}
 </div></>;
}
function Metric({title,value}:{title:string,value:string}){return <Card><CardContent className="pt-5"><p className="text-sm text-gray-500">{title}</p><p className="mt-2 text-2xl font-semibold">{value}</p></CardContent></Card>}
