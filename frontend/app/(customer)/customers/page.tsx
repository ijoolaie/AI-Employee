"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { Button } from "@/components/ui/button";
import { listCustomers, updateCustomer, getErrorMessage } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { Search, Users, Phone, Mail, RefreshCw } from "lucide-react";
import { useI18n } from "@/lib/i18n/provider";

export default function CustomersPage(){
 const [q,setQ]=useState(""); const [editingId,setEditingId]=useState<string|null>(null); const [name,setName]=useState(""); const [email,setEmail]=useState(""); const [phone,setPhone]=useState(""); const [notes,setNotes]=useState(""); const [active,setActive]=useState(true);
 const qc=useQueryClient(); const { t } = useI18n(); const m=t.customers;
 const query=useQuery({queryKey:["customers",q],queryFn:()=>listCustomers(q),refetchInterval:15000});
 const mut=useMutation({mutationFn:()=>updateCustomer(editingId!,{name:name.trim()||null,email:email.trim()||null,phone:phone.trim()||null,notes:notes.trim()||null,is_active:active}),onSuccess:()=>{setEditingId(null);void qc.invalidateQueries({queryKey:["customers"]});},});
 const start=(c: import("@/types").Customer)=>{setEditingId(c.id);setName(c.name??"");setEmail(c.email??"");setPhone(c.phone??"");setNotes(c.notes??"");setActive(c.is_active);};
 const permissionDenied=!!query.error&&getErrorMessage(query.error).toLowerCase().includes("permission");
 return <><Header title={m.title} description={m.description}/><div className="space-y-5 p-6">
 <div className="max-w-xl"><div className="relative"><Search className="absolute start-3 top-2.5 h-4 w-4 text-slate-400"/><Input className="ps-9" value={q} onChange={e=>setQ(e.target.value)} placeholder={m.searchPlaceholder}/></div></div>
 {permissionDenied&&<div role="alert" className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">{m.permissionDenied}</div>}
 <Card><CardHeader><CardTitle className="flex items-center gap-2"><Users className="h-5 w-5"/>{m.directory}</CardTitle></CardHeader><CardContent className="p-0">
 {query.isLoading?<div className="p-8"><Spinner/></div>:query.error?<div className="space-y-3 p-6"><p role="alert" className="text-sm text-red-600">{permissionDenied?m.permissionDenied:getErrorMessage(query.error)}</p>{!permissionDenied&&<Button variant="outline" onClick={()=>void query.refetch()}><RefreshCw className="h-4 w-4"/>{m.retry}</Button>}</div>:<div className="divide-y">
 {(query.data??[]).map(c=><div key={c.id} className="grid gap-3 p-5 md:grid-cols-[1.5fr_1fr_1fr_auto] md:items-center"><div><p className="font-medium text-slate-900">{c.name||m.anonymous}</p><p className="text-xs text-slate-400">{c.external_key}</p></div><div className="flex items-center gap-2 text-sm text-slate-600">{c.email&&<><Mail className="h-4 w-4"/>{c.email}</>}{!c.email&&c.phone&&<><Phone className="h-4 w-4"/>{c.phone}</>}</div><div className="flex flex-wrap gap-1"><span className={`rounded-full px-2 py-1 text-xs ${c.is_active?"bg-emerald-50 text-emerald-700":"bg-slate-100 text-slate-500"}`}>{c.is_active?m.active:m.inactive}</span>{c.tags.map(t=><span key={t} className="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-600">{t}</span>)}</div><div className="flex items-center gap-2 text-xs text-slate-400"><span>{c.last_channel||"—"} · {formatDate(c.updated_at)}</span><Button size="sm" variant="outline" onClick={()=>start(c)}>{m.edit}</Button></div></div>)}
 {(query.data??[]).length===0&&<div className="p-12 text-center text-sm text-slate-500">{m.empty}</div>}
 {editingId&&<div className="border-t p-5"><div className="mb-4 flex items-center justify-between"><h3 className="font-medium">{m.editTitle}</h3></div><div className="grid gap-3 md:grid-cols-2"><Input value={name} onChange={e=>setName(e.target.value)} placeholder={m.name} aria-label={m.name}/><Input value={email} onChange={e=>setEmail(e.target.value)} placeholder={m.email} aria-label={m.email}/><Input value={phone} onChange={e=>setPhone(e.target.value)} placeholder={m.phone} aria-label={m.phone}/><Input value={notes} onChange={e=>setNotes(e.target.value)} placeholder={m.notes} aria-label={m.notes}/><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={active} onChange={e=>setActive(e.target.checked)}/>{active?m.active:m.inactive}</label><div className="flex gap-2"><Button loading={mut.isPending} onClick={()=>mut.mutate()}>{m.save}</Button><Button variant="outline" disabled={mut.isPending} onClick={()=>setEditingId(null)}>{m.cancel}</Button></div></div>{mut.isError&&<p role="alert" className="mt-3 text-sm text-red-600">{getErrorMessage(mut.error).toLowerCase().includes("permission")?m.permissionDenied:m.updateError}</p>}</div>}
 </div>}
 </CardContent></Card></div></>;
}
