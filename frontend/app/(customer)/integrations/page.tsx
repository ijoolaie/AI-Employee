"use client";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { createCommerceIntegration, listCommerceIntegrations, testCommerceIntegration, syncCommerceProducts, syncCommerceOrders, reconcileCommerce, shopifyInstallUrl } from "@/lib/api";
import { CheckCircle2, PlugZap, RefreshCw, ShoppingBag } from "lucide-react";

export default function IntegrationsPage() {
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["integrations"], queryFn: listCommerceIntegrations });
  const [shopDomain, setShopDomain] = useState("");
  const [accessToken, setAccessToken] = useState("");
  const [apiVersion, setApiVersion] = useState("2025-10");
  const [name, setName] = useState("My Shopify store");
  const [oauthShop, setOauthShop] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const create = useMutation({
    mutationFn: () => createCommerceIntegration({ provider: "shopify", name, config: { shop_domain: shopDomain, access_token: accessToken, api_version: apiVersion, currency: "EUR" } }),
    onSuccess: () => { setAccessToken(""); setMessage("Shopify connection saved. Test the connection to verify it."); qc.invalidateQueries({ queryKey: ["integrations"] }); }
  });
  const test = useMutation({ mutationFn: testCommerceIntegration, onSuccess: (x) => { setMessage(`Connected to ${x.shop?.name ?? "Shopify"}.`); qc.invalidateQueries({ queryKey: ["integrations"] }); } });
  const syncProducts = useMutation({ mutationFn: syncCommerceProducts, onSuccess: (x) => { setMessage(`Products synced: ${x.created} created, ${x.updated} updated.`); qc.invalidateQueries({ queryKey: ["products"] }); qc.invalidateQueries({ queryKey: ["integrations"] }); } });
  const syncOrders = useMutation({ mutationFn: syncCommerceOrders, onSuccess: (x) => { setMessage(`Orders synced: ${x.created} created, ${x.updated} updated.`); qc.invalidateQueries({ queryKey: ["orders"] }); qc.invalidateQueries({ queryKey: ["customers"] }); qc.invalidateQueries({ queryKey: ["integrations"] }); } });
  const reconcile = useMutation({ mutationFn: reconcileCommerce, onSuccess: () => { setMessage("Shopify reconciliation completed."); qc.invalidateQueries({ queryKey: ["products"] }); qc.invalidateQueries({ queryKey: ["orders"] }); qc.invalidateQueries({ queryKey: ["customers"] }); qc.invalidateQueries({ queryKey: ["integrations"] }); } });

  return <>
    <Header title="Commerce Integrations" description="Connect live store data so the AI Employee can search products, check inventory and answer order questions." />
    <div className="space-y-6 p-6">

      <Card>
        <CardHeader><CardTitle>Connect with Shopify OAuth</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-slate-600">For production installs, use OAuth so the merchant grants the minimum scopes without pasting an Admin API token into your SaaS.</p>
          <div className="flex gap-2">
            <input value={oauthShop} onChange={e => setOauthShop(e.target.value)} placeholder="your-store.myshopify.com" className="flex-1 rounded-lg border px-3 py-2 text-sm" />
            <Button disabled={!oauthShop} onClick={() => { window.location.href = shopifyInstallUrl(oauthShop); }}>Connect Shopify</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><ShoppingBag className="h-5 w-5" /> Connect Shopify</CardTitle></CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2">
          <input value={name} onChange={e => setName(e.target.value)} placeholder="Store name" className="rounded-lg border px-3 py-2 text-sm" />
          <input value={shopDomain} onChange={e => setShopDomain(e.target.value)} placeholder="your-store.myshopify.com" className="rounded-lg border px-3 py-2 text-sm" />
          <input value={accessToken} onChange={e => setAccessToken(e.target.value)} placeholder="Admin API access token" type="password" className="rounded-lg border px-3 py-2 text-sm" />
          <input value={apiVersion} onChange={e => setApiVersion(e.target.value)} placeholder="API version" className="rounded-lg border px-3 py-2 text-sm" />
          <div className="md:col-span-2 rounded-lg bg-slate-50 p-3 text-xs text-slate-600">Use a Shopify Admin API token with the minimum read scopes required for products, inventory, orders and customers. Secrets are never returned by the integration API.</div>
          <Button className="md:col-span-2" loading={create.isPending} disabled={!shopDomain || !accessToken} onClick={() => create.mutate()}><PlugZap className="h-4 w-4" /> Save Shopify connection</Button>
        </CardContent>
      </Card>

      {message && <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{message}</div>}

      <div className="grid gap-4">
        {(q.data ?? []).map(x => <Card key={x.id}><CardContent className="flex flex-col gap-4 p-5 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3"><div className="rounded-lg bg-brand-50 p-2"><PlugZap className="h-5 w-5 text-brand-600" /></div><div><p className="font-medium">{x.name}</p><p className="text-xs text-slate-500">{x.provider} · {x.status}</p></div></div>
          <div className="flex flex-wrap gap-2"><span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs text-emerald-700"><CheckCircle2 className="h-3.5 w-3.5" />{x.is_active ? "Active" : "Inactive"}</span>{x.provider === "shopify" && <><Button size="sm" variant="outline" loading={test.isPending} onClick={() => test.mutate(x.id)}>Test</Button><Button size="sm" variant="outline" loading={syncProducts.isPending} onClick={() => syncProducts.mutate(x.id)}><RefreshCw className="h-4 w-4" /> Products</Button><Button size="sm" variant="outline" loading={syncOrders.isPending} onClick={() => syncOrders.mutate(x.id)}><RefreshCw className="h-4 w-4" /> Orders</Button><Button size="sm" variant="outline" loading={reconcile.isPending} onClick={() => reconcile.mutate(x.id)}>Reconcile all</Button></>}</div>
        </CardContent></Card>)}
        {!q.isLoading && (q.data ?? []).length === 0 && <Card><CardContent className="py-12 text-center text-sm text-slate-500">No commerce connections yet.</CardContent></Card>}
      </div>
    </div>
  </>;
}
