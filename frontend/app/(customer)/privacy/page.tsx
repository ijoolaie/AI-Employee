"use client";
import { useState } from "react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getErrorMessage, exportCustomerData, deleteCustomerData } from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";
export default function PrivacyPage(){
 const {t}=useI18n(); const m=t.privacy; const [id,setId]=useState(""); const [data,setData]=useState<unknown>(null); const [msg,setMsg]=useState<string|null>(null); const [error,setError]=useState<string|null>(null);
 async function exportData(){setError(null);try{setData(await exportCustomerData(id.trim()));}catch(e){setError(getErrorMessage(e)||m.error);}}
 async function deleteData(){setError(null);if(!id.trim())return setError(m.customerId);if(!confirm(m.confirm))return;try{await deleteCustomerData(id.trim());setMsg(m.success);}catch(e){setError(getErrorMessage(e)||m.error);}}
 return <><Header title={m.title} description={m.description}/><div className="max-w-2xl space-y-6 p-6"><Card><CardHeader><CardTitle>{m.request}</CardTitle></CardHeader><CardContent className="space-y-3"><label className="block text-sm font-medium"><span>{m.customerId}</span><input value={id} onChange={e=>setId(e.target.value)} placeholder={m.customerId} className="mt-1 w-full rounded-lg border px-3 py-2 text-sm"/></label><div className="flex flex-wrap gap-2"><Button onClick={exportData} disabled={!id.trim()}>{m.exportData}</Button><Button variant="secondary" onClick={deleteData} disabled={!id.trim()}>{m.deleteAnonymize}</Button></div>{error&&<div role="alert" className="text-sm text-red-600">{error}</div>}{msg&&<p role="status" className="text-sm text-green-700">{msg}</p>}{data!==null&&<pre className="max-h-96 overflow-auto rounded-lg bg-slate-950 p-4 text-xs text-white">{JSON.stringify(data,null,2)}</pre>}</CardContent></Card></div></>;
}
