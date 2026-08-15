"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getOnboarding, updateOnboarding } from "@/lib/api";
import { Check, Rocket, Store, Sparkles, Package, Radio, ShieldCheck } from "lucide-react";
import { useState } from "react";
import Link from "next/link";

const steps = [
  ["Business", "Tell us what you sell.", Store], ["Brand", "Set your store identity and tone.", Sparkles],
  ["Products", "Add products or connect Shopify for live catalog and inventory.", Package], ["Employee", "Choose tools such as product search, inventory and order tracking.", ShieldCheck],
  ["Channel", "Publish website chat, WhatsApp or a public link.", Radio], ["Launch", "Run a live customer conversation and verify the commerce loop.", Rocket],
] as const;
export default function OnboardingPage() {
  const qc = useQueryClient(); const q = useQuery({queryKey:["onboarding"],queryFn:getOnboarding}); const [type,setType]=useState("retail");
  const m=useMutation({mutationFn:(step:number)=>updateOnboarding({step,business_type:type,data:{business_type:type}}),onSuccess:()=>qc.invalidateQueries({queryKey:["onboarding"]})});
  const p=q.data; const current=p?.current_step??1; const completed=new Set(p?.completed_steps??[]);
  return <><Header title="Get your business live" description="A guided setup that takes a new customer from signup to a working AI Employee." />
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <Card className="border-brand-100 bg-gradient-to-br from-brand-50 to-white"><CardContent className="p-6"><div className="flex items-center gap-3"><div className="rounded-xl bg-brand-600 p-3"><Rocket className="h-6 w-6 text-white"/></div><div><h2 className="text-xl font-semibold">Launch checklist</h2><p className="text-sm text-slate-500">Complete the six steps once. You can return to any setup area later.</p></div></div><div className="mt-5 h-2 overflow-hidden rounded-full bg-slate-200"><div className="h-full bg-brand-600 transition-all" style={{width:`${(completed.size/6)*100}%`}}/></div></CardContent></Card>
      <div className="grid gap-4 md:grid-cols-2">{steps.map(([title,desc,Icon],i)=>{const n=i+1;const done=completed.has(n);return <Card key={title} className={n===current&&!done?"ring-2 ring-brand-200":""}><CardHeader><div className="flex items-start justify-between"><div className="flex items-center gap-3"><div className={`rounded-lg p-2 ${done?"bg-emerald-50":"bg-slate-100"}`}><Icon className={`h-5 w-5 ${done?"text-emerald-600":"text-slate-600"}`}/></div><div><CardTitle className="text-base">{n}. {title}</CardTitle><p className="mt-1 text-xs text-slate-500">{desc}</p></div></div>{done&&<Check className="h-5 w-5 text-emerald-600"/>}</div></CardHeader><CardContent>{n===1&&<select value={type} onChange={e=>setType(e.target.value)} className="w-full rounded-lg border px-3 py-2 text-sm"><option value="retail">Retail / Store</option><option value="ecommerce">E-commerce</option><option value="services">Services</option><option value="restaurant">Restaurant</option><option value="other">Other</option></select>}<div className="mt-3 grid gap-2 sm:grid-cols-2"><Button className="w-full" variant={done?"outline":"primary"} loading={m.isPending&&m.variables===n} onClick={()=>m.mutate(n)}>{done?"Completed — mark again":"Complete step"}</Button>{n===3&&<Link href="/integrations"><Button type="button" variant="outline" className="w-full">Connect Shopify</Button></Link>}{n===4&&<><Link href="/templates"><Button type="button" variant="outline" className="w-full">Choose Template</Button></Link><Link href="/employees/new"><Button type="button" variant="outline" className="w-full">Configure Employee</Button></Link></>}{n===5&&<Link href="/channels"><Button type="button" variant="outline" className="w-full">Manage Channels</Button></Link>}{n===6&&<><Link href="/inbox"><Button type="button" variant="outline" className="w-full">Open Inbox</Button></Link><Link href="/analytics"><Button type="button" variant="outline" className="w-full">View ROI</Button></Link></>}</div></CardContent></Card>})}</div>
      {p?.completed&&<Card className="border-emerald-200 bg-emerald-50"><CardContent className="flex items-center gap-3 p-5"><Check className="h-6 w-6 text-emerald-600"/><div><p className="font-semibold text-emerald-900">Your business is ready to launch.</p><p className="text-sm text-emerald-700">Publish an Employee and connect a customer channel.</p></div></CardContent></Card>}
    </div></>;
}
