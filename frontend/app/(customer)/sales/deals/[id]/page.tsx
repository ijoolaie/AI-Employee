"use client";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card,CardContent,CardHeader,CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Button } from "@/components/ui/button";
import { getErrorMessage,getDeal } from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";
export default function DealDetail(){
 const {t}=useI18n(); const m=t.dealDetail; const {id}=useParams<{id:string}>();
 const q=useQuery({queryKey:["deal",id],queryFn:()=>getDeal(id)});
 if(q.isLoading)return <><Header title={m.detail} description={m.information}/><div className="p-6"><Spinner/></div></>;
 if(q.isError)return <><Header title={m.detail} description={m.information}/><div className="space-y-3 p-6"><p className="text-sm text-red-600">{getErrorMessage(q.error)||m.loadError}</p><Button variant="secondary" onClick={()=>void q.refetch()}>{m.retry}</Button></div></>;
 const d=q.data!;
 return <><Header title={d.title} description={`${m.detail} · ${d.stage}`}/><div className="grid gap-6 p-6 lg:grid-cols-3">
 <Card className="lg:col-span-2"><CardHeader><CardTitle>{m.information}</CardTitle></CardHeader><CardContent className="grid gap-4 sm:grid-cols-2 text-sm"><Item l={m.customer} v={d.customer_name}/><Item l={m.email} v={d.customer_email??"—"}/><Item l={m.amount} v={`${Number(d.amount).toLocaleString()} ${d.currency}`}/><Item l={m.probability} v={`${d.probability}%`}/><Item l={m.expectedClose} v={d.expected_close_date??"—"}/><Item l={m.owner} v={d.owner_name??"—"}/><Item l={m.source} v={d.source??"—"}/><Item l={m.order} v={d.order_id??"—"}/></CardContent></Card>
 <Card><CardHeader><CardTitle>{m.notes}</CardTitle></CardHeader><CardContent className="text-sm whitespace-pre-wrap text-gray-700">{d.notes||m.noNotes}</CardContent></Card>
 <Card className="lg:col-span-3"><CardHeader><CardTitle>{m.timeline}</CardTitle></CardHeader><CardContent className="text-sm text-gray-600"><p>{m.created}: {new Date(d.created_at).toLocaleString()}</p><p className="mt-2">{m.updated}: {new Date(d.updated_at).toLocaleString()}</p></CardContent></Card>
 </div></>;
}
function Item({l,v}:{l:string,v:string}){return <div><p className="text-gray-500">{l}</p><p className="mt-1 font-medium text-gray-900">{v}</p></div>}
