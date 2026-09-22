"use client";
import { useState } from "react";
import { useParams } from "next/navigation";
import { useMutation,useQuery,useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card,CardContent,CardHeader,CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage,getInvoice,updateInvoice,updateInvoiceStatus,exportInvoicePdf } from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";
export default function InvoiceDetail(){
 const {t}=useI18n(); const m=t.invoices; const [editing,setEditing]=useState(false); const [name,setName]=useState(""); const [email,setEmail]=useState(""); const [notes,setNotes]=useState(""); const {id}=useParams<{id:string}>(); const qc=useQueryClient(); const [msg,setMsg]=useState("");
 const q=useQuery({queryKey:["invoice",id],queryFn:()=>getInvoice(id)});
 const edit=useMutation({mutationFn:()=>updateInvoice(id,{customer_name:name,customer_email:email||null,notes:notes||null}),onSuccess:()=>{setEditing(false);setMsg(m.statusUpdated);void qc.invalidateQueries({queryKey:["invoice",id]});void qc.invalidateQueries({queryKey:["invoices"]});},onError:e=>setMsg(getErrorMessage(e)||m.loadError)});
 const status=useMutation({mutationFn:(s:string)=>updateInvoiceStatus(id,s),onSuccess:()=>{setMsg(m.statusUpdated);void qc.invalidateQueries({queryKey:["invoice",id]});void qc.invalidateQueries({queryKey:["invoices"]});},onError:e=>setMsg(getErrorMessage(e)||m.loadError)});
 const pdf=useMutation({mutationFn:()=>exportInvoicePdf(id),onSuccess:d=>setMsg(d?.url?m.pdfReady:m.pdfExported),onError:e=>setMsg(getErrorMessage(e)||m.loadError)});
 if(q.isLoading)return <><Header title={m.title} description={m.description}/><div className="p-6"><Spinner/></div></>;
 if(q.isError)return <><Header title={m.title} description={m.description}/><div className="space-y-3 p-6"><p className="text-sm text-red-600">{getErrorMessage(q.error)||m.loadError}</p><Button variant="secondary" onClick={()=>void q.refetch()}>{m.retry}</Button></div></>;
 const i=q.data!;
 return <><Header title={`${m.title} ${i.number}`} description={`${i.customer_name} · ${i.status}`}/><div className="space-y-6 p-6">
 <Card><CardContent className="grid gap-4 p-6 md:grid-cols-4 text-sm"><div><span className="text-gray-500">{m.customer}</span><p className="font-semibold">{i.customer_name}</p></div><div><span className="text-gray-500">{m.issueDate}</span><p>{i.issue_date}</p></div><div><span className="text-gray-500">{m.dueDate}</span><p>{i.due_date??"—"}</p></div><div><span className="text-gray-500">{m.totalLabel}</span><p className="font-semibold">{Number(i.total).toLocaleString()} {i.currency}</p></div></CardContent></Card>
 <Card><CardHeader><CardTitle>{m.lineItems}</CardTitle></CardHeader><CardContent><div className="space-y-2">{(i.line_items??[]).map((x:any,n:number)=><div key={n} className="flex justify-between border-b py-2 text-sm"><span>{x.description} × {x.quantity}</span><span>{Number(x.amount??x.unit_price*x.quantity).toLocaleString()} {i.currency}</span></div>)}</div><div className="mt-4 text-end font-semibold">{m.totalLabel}: {Number(i.total).toLocaleString()} {i.currency}</div></CardContent></Card>
 {editing&&i.status==="draft"&&<Card><CardContent className="grid gap-3 p-6 md:grid-cols-2"><label className="text-sm"><span>{m.customer}</span><input className="mt-1 w-full rounded-lg border px-3 py-2" value={name} onChange={e=>setName(e.target.value)}/></label><label className="text-sm"><span>{m.email}</span><input className="mt-1 w-full rounded-lg border px-3 py-2" value={email} onChange={e=>setEmail(e.target.value)}/></label><label className="text-sm md:col-span-2"><span>{m.notes}</span><textarea className="mt-1 w-full rounded-lg border px-3 py-2" value={notes} onChange={e=>setNotes(e.target.value)}/></label><div className="flex gap-2"><Button onClick={()=>edit.mutate()} disabled={edit.isPending}>{edit.isPending?m.saving:m.save}</Button><Button variant="secondary" onClick={()=>setEditing(false)}>{m.cancel}</Button></div></CardContent></Card>}
 <div className="flex flex-wrap gap-2">{i.status==="draft"&&<Button variant="secondary" onClick={()=>{setName(i.customer_name);setEmail(i.customer_email??"");setNotes(i.notes??"");setEditing(true)}}>{m.edit}</Button>}<select aria-label={m.status} className="rounded-lg border px-3 py-2 text-sm" value={i.status} onChange={e=>status.mutate(e.target.value)} disabled={status.isPending}>{["draft","sent","paid","overdue","void"].map(s=><option key={s}>{s}</option>)}</select><Button variant="secondary" onClick={()=>pdf.mutate()} disabled={pdf.isPending}>{pdf.isPending?m.exporting:m.exportPdf}</Button></div>{msg&&<p className="text-sm text-gray-600">{msg}</p>}
 </div></>;
}
