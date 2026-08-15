"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { listCustomers, getErrorMessage } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { Search, Users, Phone, Mail } from "lucide-react";
export default function CustomersPage(){
 const [q,setQ]=useState(""); const query=useQuery({queryKey:["customers",q],queryFn:()=>listCustomers(q),refetchInterval:15000});
 return <><Header title="Customers" description="Customer profiles connected to your AI Employees and channels."/><div className="space-y-5 p-6"><div className="max-w-xl"><div className="relative"><Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400"/><Input className="pl-9" value={q} onChange={e=>setQ(e.target.value)} placeholder="Search name, email or phone…"/></div></div><Card><CardHeader><CardTitle className="flex items-center gap-2"><Users className="h-5 w-5"/>Customer directory</CardTitle></CardHeader><CardContent className="p-0">{query.isLoading?<div className="p-8"><Spinner/></div>:query.error?<p className="p-6 text-sm text-red-600">{getErrorMessage(query.error)}</p>:<div className="divide-y">{(query.data??[]).map(c=><div key={c.id} className="grid gap-3 p-5 md:grid-cols-[1.5fr_1fr_1fr_auto] md:items-center"><div><p className="font-medium text-slate-900">{c.name||"Anonymous customer"}</p><p className="text-xs text-slate-400">{c.external_key}</p></div><div className="flex items-center gap-2 text-sm text-slate-600">{c.email&&<><Mail className="h-4 w-4"/>{c.email}</>}{!c.email&&c.phone&&<><Phone className="h-4 w-4"/>{c.phone}</>}</div><div className="flex flex-wrap gap-1">{c.tags.map(t=><span key={t} className="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-600">{t}</span>)}</div><div className="text-xs text-slate-400">{c.last_channel||"—"} · {formatDate(c.updated_at)}</div></div>)}{(query.data??[]).length===0&&<div className="p-12 text-center text-sm text-slate-500">No customers yet. Customers appear automatically when they start conversations.</div>}</div>}</CardContent></Card></div></>;
}
