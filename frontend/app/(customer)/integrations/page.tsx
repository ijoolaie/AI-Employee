"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { createCommerceIntegration, getErrorMessage, listCommerceIntegrations, reconcileCommerce, shopifyInstallUrl, syncCommerceOrders, syncCommerceProducts, testCommerceIntegration } from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";
import { CheckCircle2, PlugZap, RefreshCw, ShoppingBag } from "lucide-react";

function isPermissionError(error: unknown) {
  const message = getErrorMessage(error).toLowerCase();
  return message.includes("permission") || message.includes("403") || message.includes("forbidden");
}
export default function IntegrationsPage() {
  const { t } = useI18n(); const m = t.integrations; const qc = useQueryClient();
  const q = useQuery({ queryKey: ["integrations"], queryFn: listCommerceIntegrations });
  const [shopDomain,setShopDomain]=useState(""); const [accessToken,setAccessToken]=useState(""); const [apiVersion,setApiVersion]=useState("2025-10");
  const [name,setName]=useState("My Shopify store"); const [oauthShop,setOauthShop]=useState(""); const [error,setError]=useState<string|null>(null); const [success,setSuccess]=useState<string|null>(null);
  const create=useMutation({mutationFn:()=>createCommerceIntegration({provider:"shopify",name,config:{shop_domain:shopDomain,access_token:accessToken,api_version:apiVersion,currency:"EUR"}}),onSuccess:()=>{setAccessToken("");setError(null);setSuccess(m.connectionSaved);void qc.invalidateQueries({queryKey:["integrations"]});},onError:e=>{setSuccess(null);setError(isPermissionError(e)?m.permissionDenied:getErrorMessage(e)||m.createError);}});
  const test=useMutation({mutationFn:testCommerceIntegration,onSuccess:x=>{setError(null);setSuccess(m.connected.replace("{shop}",x.shop?.name??"Shopify"));void qc.invalidateQueries({queryKey:["integrations"]});},onError:e=>{setSuccess(null);setError(isPermissionError(e)?m.permissionDenied:getErrorMessage(e)||m.testError);}});
  const syncProducts=useMutation({mutationFn:syncCommerceProducts,onSuccess:x=>{setError(null);setSuccess(m.productsSynced.replace("{created}",String(x.created)).replace("{updated}",String(x.updated)));void qc.invalidateQueries({queryKey:["products"]});void qc.invalidateQueries({queryKey:["integrations"]});},onError:e=>{setSuccess(null);setError(isPermissionError(e)?m.permissionDenied:getErrorMessage(e)||m.syncError);}});
  const syncOrders=useMutation({mutationFn:syncCommerceOrders,onSuccess:x=>{setError(null);setSuccess(m.ordersSynced.replace("{created}",String(x.created)).replace("{updated}",String(x.updated)));void qc.invalidateQueries({queryKey:["orders"]});void qc.invalidateQueries({queryKey:["customers"]});void qc.invalidateQueries({queryKey:["integrations"]});},onError:e=>{setSuccess(null);setError(isPermissionError(e)?m.permissionDenied:getErrorMessage(e)||m.syncError);}});
  const reconcile=useMutation({mutationFn:reconcileCommerce,onSuccess:()=>{setError(null);setSuccess(m.reconciled);void qc.invalidateQueries({queryKey:["products"]});void qc.invalidateQueries({queryKey:["orders"]});void qc.invalidateQueries({queryKey:["customers"]});void qc.invalidateQueries({queryKey:["integrations"]});},onError:e=>{setSuccess(null);setError(isPermissionError(e)?m.permissionDenied:getErrorMessage(e)||m.reconcileError);}});
  const busy= create.isPending||test.isPending||syncProducts.isPending||syncOrders.isPending||reconcile.isPending;
  return <><Header title={m.title} description={m.description}/><div className="space-y-6 p-6">
    {q.isLoading&&<div className="flex justify-center py-8" aria-label={m.loading}><Spinner/></div>}
    {q.error&&<div role="alert" className="space-y-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700"><p>{isPermissionError(q.error)?m.permissionDenied:m.loadError}</p><Button variant="secondary" onClick={()=>void q.refetch()}>{m.retry}</Button></div>}
    {error&&<div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
    {success&&<div role="status" className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{success}</div>}
    {!q.isLoading&&!q.error&&<Card><CardHeader><CardTitle>{m.oauthTitle}</CardTitle></CardHeader><CardContent className="space-y-3"><p className="text-sm text-slate-600">{m.oauthDescription}</p><div className="flex flex-col gap-2 sm:flex-row"><input value={oauthShop} onChange={e=>setOauthShop(e.target.value)} placeholder={m.shopPlaceholder} aria-label={m.shopPlaceholder} className="flex-1 rounded-lg border px-3 py-2 text-sm text-start"/><Button disabled={!oauthShop||busy} onClick={()=>{window.location.href=shopifyInstallUrl(oauthShop)}}>{m.connectShopify}</Button></div></CardContent></Card>}
    {!q.isLoading&&!q.error&&<Card><CardHeader><CardTitle className="flex items-center gap-2"><ShoppingBag className="h-5 w-5"/>{m.manualTitle}</CardTitle></CardHeader><CardContent className="grid gap-3 md:grid-cols-2">
      <input value={name} onChange={e=>setName(e.target.value)} placeholder={m.storeName} aria-label={m.storeName} className="rounded-lg border px-3 py-2 text-sm text-start"/>
      <input value={shopDomain} onChange={e=>setShopDomain(e.target.value)} placeholder={m.shopPlaceholder} aria-label={m.shopPlaceholder} className="rounded-lg border px-3 py-2 text-sm text-start"/>
      <input value={accessToken} onChange={e=>setAccessToken(e.target.value)} placeholder={m.tokenPlaceholder} aria-label={m.tokenPlaceholder} type="password" className="rounded-lg border px-3 py-2 text-sm text-start"/>
      <input value={apiVersion} onChange={e=>setApiVersion(e.target.value)} placeholder={m.apiVersion} aria-label={m.apiVersion} className="rounded-lg border px-3 py-2 text-sm text-start"/>
      <div className="md:col-span-2 rounded-lg bg-slate-50 p-3 text-xs text-slate-600">{m.secretNote}</div>
      <Button className="md:col-span-2" loading={create.isPending} disabled={!shopDomain||!accessToken||!name||busy} onClick={()=>create.mutate()}><PlugZap className="h-4 w-4"/>{m.save}</Button>
    </CardContent></Card>}
    {!q.isLoading&&!q.error&&(q.data??[]).length===0?<EmptyState icon={PlugZap} title={m.emptyTitle} description={m.emptyDescription}/>:
      !q.isLoading&&!q.error&&<div className="grid gap-4">{(q.data??[]).map(x=><Card key={x.id}><CardContent className="flex flex-col gap-4 p-5 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3"><div className="rounded-lg bg-brand-50 p-2"><PlugZap className="h-5 w-5 text-brand-600"/></div><div><p className="font-medium">{x.name}</p><p className="text-xs text-slate-500">{x.provider} · {x.status}</p></div></div>
        <div className="flex flex-wrap gap-2"><span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs text-emerald-700"><CheckCircle2 className="h-3.5 w-3.5"/>{x.is_active?m.active:m.inactive}</span>{x.provider==="shopify"&&<><Button size="sm" variant="outline" loading={test.isPending} disabled={busy} onClick={()=>test.mutate(x.id)}>{m.test}</Button><Button size="sm" variant="outline" loading={syncProducts.isPending} disabled={busy} onClick={()=>syncProducts.mutate(x.id)}><RefreshCw className="h-4 w-4"/>{m.products}</Button><Button size="sm" variant="outline" loading={syncOrders.isPending} disabled={busy} onClick={()=>syncOrders.mutate(x.id)}><RefreshCw className="h-4 w-4"/>{m.orders}</Button><Button size="sm" variant="outline" loading={reconcile.isPending} disabled={busy} onClick={()=>reconcile.mutate(x.id)}>{m.reconcile}</Button></>}</div>
      </CardContent></Card>)}</div>}
  </div></>;
}
