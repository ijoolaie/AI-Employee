"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getOnboarding, updateOnboarding } from "@/lib/api";
import { Check, Rocket, Store, Sparkles, Package, Radio, ShieldCheck } from "lucide-react";
import { useState } from "react";
import Link from "next/link";
import { useI18n } from "@/lib/i18n/provider";

export default function OnboardingPage() {
  const { t } = useI18n();
  const m = t.customerLegacy.onboarding;
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["onboarding"], queryFn: getOnboarding });
  const [type, setType] = useState("retail");
  const mutation = useMutation({
    mutationFn: (step: number) => updateOnboarding({ step, business_type: type, data: { business_type: type } }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["onboarding"] }),
  });
  const data = query.data;
  const current = data?.current_step ?? 1;
  const completed = new Set(data?.completed_steps ?? []);
  const steps = [[m.business, m.businessDesc, Store],[m.brand, m.brandDesc, Sparkles],[m.products, m.productsDesc, Package],[m.employee, m.employeeDesc, ShieldCheck],[m.channel, m.channelDesc, Radio],[m.launch, m.launchDesc, Rocket]] as const;

  if (query.isLoading) return <><Header title={m.title} description={m.description}/><div className="p-6">Loading…</div></>;
  if (query.isError) return <><Header title={m.title} description={m.description}/><div className="space-y-3 p-6"><p className="text-sm text-red-600">{m.loadError}</p><Button variant="secondary" onClick={() => void query.refetch()}>{m.retry}</Button></div></>;

  return <>
    <Header title={m.title} description={m.description}/>
    <div className="mx-auto max-w-5xl space-y-6 p-6" dir="auto">
      <Card className="border-brand-100 bg-gradient-to-br from-brand-50 to-white"><CardContent className="p-6">
        <div className="flex items-center gap-3"><div className="rounded-xl bg-brand-600 p-3"><Rocket className="h-6 w-6 text-white"/></div><div><h2 className="text-xl font-semibold">{m.checklist}</h2><p className="text-sm text-slate-500">{m.checklistDescription}</p></div></div>
        <div className="mt-5 h-2 overflow-hidden rounded-full bg-slate-200"><div className="h-full bg-brand-600 transition-all" style={{width: `${(completed.size / 6) * 100}%`}} /></div>
      </CardContent></Card>
      <div className="grid gap-4 md:grid-cols-2">
        {steps.map(([title, description, Icon], index) => {
          const step=index+1; const done=completed.has(step);
          return <Card key={title} className={step===current&&!done?"ring-2 ring-brand-200":""}><CardHeader><div className="flex items-start justify-between"><div className="flex items-center gap-3"><div className={`rounded-lg p-2 ${done?"bg-emerald-50":"bg-slate-100"}`}><Icon className={`h-5 w-5 ${done?"text-emerald-600":"text-slate-600"}`}/></div><div><CardTitle className="text-base">{step}. {title}</CardTitle><p className="mt-1 text-xs text-slate-500">{description}</p></div></div>{done&&<Check className="h-5 w-5 text-emerald-600"/>}</div></CardHeader><CardContent>
            {step===1&&<select aria-label={m.business} value={type} onChange={e=>setType(e.target.value)} className="w-full rounded-lg border px-3 py-2 text-sm"><option value="retail">Retail / Store</option><option value="ecommerce">E-commerce</option><option value="services">Services</option><option value="restaurant">Restaurant</option><option value="other">Other</option></select>}
            <div className="mt-3 grid gap-2 sm:grid-cols-2"><Button className="w-full" variant={done?"outline":"primary"} loading={mutation.isPending&&mutation.variables===step} onClick={()=>mutation.mutate(step)}>{done?m.completed:m.complete}</Button>
              {step===3&&<Link href="/integrations"><Button type="button" variant="outline" className="w-full">{m.connectShopify}</Button></Link>}
              {step===4&&<><Link href="/templates"><Button type="button" variant="outline" className="w-full">{m.chooseTemplate}</Button></Link><Link href="/employees/new"><Button type="button" variant="outline" className="w-full">{m.configureEmployee}</Button></Link></>}
              {step===5&&<Link href="/channels"><Button type="button" variant="outline" className="w-full">{m.manageChannels}</Button></Link>}
              {step===6&&<><Link href="/inbox"><Button type="button" variant="outline" className="w-full">{m.openInbox}</Button></Link><Link href="/analytics"><Button type="button" variant="outline" className="w-full">{m.viewRoi}</Button></Link>}
            </div>
          </CardContent></Card>;
        })}
      </div>
      {data?.completed&&<Card className="border-emerald-200 bg-emerald-50"><CardContent className="flex items-center gap-3 p-5"><Check className="h-6 w-6 text-emerald-600"/><div><p className="font-semibold text-emerald-900">{m.ready}</p><p className="text-sm text-emerald-700">{m.readyDescription}</p></div></CardContent></Card>}
    </div>
  </>;
}
