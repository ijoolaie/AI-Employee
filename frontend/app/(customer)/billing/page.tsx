"use client";

import { useState } from "react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { cancelSubscription, changeSubscription, createCheckoutSession, createPortalSession, getBillingEntitlements, getErrorMessage, getSubscription, listBillingPlans } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { useI18n } from "@/lib/i18n/provider";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

function localizedStatus(status: string, m: { trialing: string; activeStatus: string; canceled: string; pastDue: string }) {
  if (status === "trialing") return m.trialing;
  if (status === "active") return m.activeStatus;
  if (status === "canceled") return m.canceled;
  if (status === "past_due") return m.pastDue;
  return status;
}
function isPermissionError(error: unknown) {
  const message = getErrorMessage(error).toLowerCase();
  return message.includes("permission") || message.includes("403") || message.includes("forbidden");
}
export default function BillingPage() {
  const { t }=useI18n(); const m=t.billing; const qc=useQueryClient(); const [message,setMessage]=useState<string|null>(null);
  const plans=useQuery({queryKey:["billing-plans"],queryFn:listBillingPlans});
  const subscription=useQuery({queryKey:["subscription"],queryFn:getSubscription});
  const entitlements=useQuery({queryKey:["billing-entitlements"],queryFn:getBillingEntitlements});
  const change=useMutation({mutationFn:changeSubscription,onSuccess:()=>{setMessage(m.subscriptionUpdated);void qc.invalidateQueries({queryKey:["subscription"]});void qc.invalidateQueries({queryKey:["billing-entitlements"]});},onError:e=>setMessage(isPermissionError(e)?m.permissionDenied:getErrorMessage(e)||m.updateError)});
  const cancel=useMutation({mutationFn:cancelSubscription,onSuccess:()=>{setMessage(m.cancellationScheduled);void qc.invalidateQueries({queryKey:["subscription"]});},onError:e=>setMessage(isPermissionError(e)?m.permissionDenied:getErrorMessage(e)||m.cancelError)});
  const checkout=useMutation({mutationFn:createCheckoutSession,onSuccess:data=>{window.location.href=data.checkout_url},onError:e=>setMessage(isPermissionError(e)?m.permissionDenied:getErrorMessage(e)||m.checkoutError)});
  const portal=useMutation({mutationFn:createPortalSession,onSuccess:data=>{window.location.href=data.portal_url},onError:e=>setMessage(isPermissionError(e)?m.permissionDenied:getErrorMessage(e)||m.portalError)});
  const choosePlan=(code:string)=>code==="starter"?change.mutate(code):checkout.mutate(code);
  const retry=()=>{void plans.refetch();void subscription.refetch();void entitlements.refetch();};
  const loadError=plans.error||subscription.error||entitlements.error;
  const busy=change.isPending||cancel.isPending||checkout.isPending||portal.isPending;
  return <><Header title={m.title} description={m.description}/><div className="space-y-6 p-6">
    {loadError&&<div role="alert" className="space-y-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700"><p>{isPermissionError(loadError)?m.permissionDenied:m.loadError}</p><Button variant="secondary" onClick={retry}>{m.retry}</Button></div>}
    {plans.isLoading||subscription.isLoading||entitlements.isLoading?<div className="flex justify-center py-8" aria-label={m.loading}><Spinner/></div>:null}
    {message&&<div role="status" className="rounded-lg border border-gray-200 bg-white px-4 py-3 text-sm text-gray-700">{message}</div>}
    {!plans.error&&!subscription.error&&subscription.data?.status==="trialing"&&subscription.data.trial_ends_at&&<div className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800">{m.trialEnds} <strong>{new Date(subscription.data.trial_ends_at).toLocaleDateString()}</strong>.</div>}
    {!entitlements.error&&entitlements.data&&<Card><CardHeader><CardTitle>{m.currentUsage}</CardTitle></CardHeader><CardContent className="grid gap-4 text-sm md:grid-cols-4">
      <div><p className="text-gray-500">{m.runs}</p><p className="font-semibold">{entitlements.data.usage.runs.toLocaleString()} / {entitlements.data.plan.monthly_runs.toLocaleString()}</p></div>
      <div><p className="text-gray-500">{m.aiTokens}</p><p className="font-semibold">{entitlements.data.usage.tokens.toLocaleString()} / {entitlements.data.plan.monthly_tokens.toLocaleString()}</p></div>
      <div><p className="text-gray-500">{m.employees}</p><p className="font-semibold">{entitlements.data.usage.employees} / {entitlements.data.plan.max_employees}</p></div>
      <div><p className="text-gray-500">{m.workflows}</p><p className="font-semibold">{entitlements.data.usage.workflows} / {entitlements.data.plan.max_workflows}</p></div>
    </CardContent></Card>}
    {!subscription.error&&subscription.data&&<Card><CardHeader><CardTitle>{m.currentSubscription}</CardTitle></CardHeader><CardContent className="grid gap-4 text-sm md:grid-cols-4">
      <div><p className="text-gray-500">{m.plan}</p><p className="font-semibold text-gray-900">{subscription.data.plan.name}</p></div>
      <div><p className="text-gray-500">{m.status}</p><p className="font-semibold text-gray-900">{localizedStatus(subscription.data.status, m)}</p></div>
      <div><p className="text-gray-500">{m.monthlyPrice}</p><p className="font-semibold text-gray-900">{formatCurrency(Number(subscription.data.plan.monthly_price_usd))}</p></div>
      <div><p className="text-gray-500">{m.periodEnd}</p><p className="font-semibold text-gray-900">{new Date(subscription.data.current_period_end).toLocaleDateString()}</p></div>
    </CardContent></Card>}
    {!subscription.error&&subscription.data?.provider==="stripe"&&<Button variant="outline" loading={portal.isPending} onClick={()=>portal.mutate()}>{m.manageBilling}</Button>}
    {!plans.error&&(plans.data??[]).length===0?<EmptyState title={m.noPlans} description={m.noPlansDescription}/>:
    !plans.error&&<div className="grid gap-4 md:grid-cols-3">{(plans.data??[]).map(plan=><Card key={plan.code} className={subscription.data?.plan.code===plan.code?"ring-2 ring-brand-500":""}>
      <CardHeader><CardTitle>{plan.name}</CardTitle><p className="text-2xl font-semibold">{formatCurrency(Number(plan.monthly_price_usd))}<span className="text-sm font-normal text-gray-500"> / {m.month}</span></p></CardHeader>
      <CardContent className="space-y-2 text-sm text-gray-600"><p>{plan.monthly_runs.toLocaleString()} {m.runsPerMonth}</p><p>{plan.monthly_tokens.toLocaleString()} {m.tokensPerMonth}</p><p>{m.upTo} {plan.max_employees} {m.employees}</p><p>{m.upTo} {plan.max_workflows} {m.workflows}</p>
        <Button className="mt-3 w-full" disabled={busy||subscription.data?.plan.code===plan.code} loading={(plan.code==="starter"?change.isPending:checkout.isPending)} onClick={()=>choosePlan(plan.code)}>
          {subscription.data?.plan.code===plan.code?m.currentPlan:plan.code==="starter"?m.choose.replace("{plan}",plan.name):m.subscribe.replace("{plan}",plan.name)}
        </Button>
      </CardContent>
    </Card>)}</div>}
    {!subscription.error&&subscription.data?.status==="active"&&!subscription.data.cancel_at_period_end&&subscription.data.plan.code!=="starter"&&<Button variant="outline" disabled={cancel.isPending} onClick={()=>{if(window.confirm(m.confirmCancel))cancel.mutate(true)}}>{m.cancelAtPeriodEnd}</Button>}
  </div></>;
}
