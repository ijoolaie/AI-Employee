"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage } from "@/lib/errors";
import { listProducts, createProduct, updateProductInventory } from "@/lib/api";
import { Package, Plus } from "lucide-react";
import { useState } from "react";
import { useI18n } from "@/lib/i18n/provider";

export default function ProductsPage() {
  const qc = useQueryClient();
  const { t } = useI18n();
  const m = t.commerce.products;
  const q = useQuery({ queryKey: ["products"], queryFn: () => listProducts() });
  const [name, setName] = useState("");
  const [price, setPrice] = useState("0");
  const [inventory, setInventory] = useState("0");

  const create = useMutation({
    mutationFn: () => createProduct({ name, price, currency: "EUR", inventory: Number(inventory) }),
    onSuccess: () => {
      setName(""); setPrice("0"); setInventory("0");
      qc.invalidateQueries({ queryKey: ["products"] });
    },
  });
  const inventoryMut = useMutation({
    mutationFn: ({ id, value }: { id: string; value: number }) => updateProductInventory(id, value),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["products"] }),
  });
  const permissionDenied = q.isError && getErrorMessage(q.error).toLowerCase().includes("permission");
  const createPermissionDenied = create.isError && getErrorMessage(create.error).toLowerCase().includes("permission");

  return (
    <>
      <Header title={m.title} description={m.description} actions={
        <Button size="sm" onClick={() => document.getElementById("product-name")?.focus()}>
          <Plus className="h-4 w-4" />{m.add}
        </Button>
      } />
      <div className="space-y-6 p-6">
        {permissionDenied && <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">{m.permissionDenied}</div>}
        <Card>
          <CardHeader><CardTitle>{m.addTitle}</CardTitle></CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-4">
            <input id="product-name" value={name} onChange={e => setName(e.target.value)} placeholder={m.namePlaceholder} className="rounded-lg border px-3 py-2 text-sm" />
            <input value={price} onChange={e => setPrice(e.target.value)} placeholder={m.pricePlaceholder} className="rounded-lg border px-3 py-2 text-sm" />
            <input value={inventory} onChange={e => setInventory(e.target.value)} placeholder={m.inventoryPlaceholder} className="rounded-lg border px-3 py-2 text-sm" />
            <Button disabled={!name.trim() || createPermissionDenied} loading={create.isPending} onClick={() => create.mutate()}>{m.save}</Button>
          </CardContent>
          {create.isError && <p className="px-6 pb-4 text-sm text-red-600">{createPermissionDenied ? m.permissionDenied : m.saveError}</p>}
        </Card>
        <Card>
          <CardHeader><CardTitle>{m.catalog}</CardTitle></CardHeader>
          <CardContent className="p-0">
            {q.isLoading ? <div className="flex justify-center p-12"><Spinner /></div> :
             q.isError ? <p className="p-6 text-sm text-red-600">{permissionDenied ? m.permissionDenied : m.error}</p> :
             <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead><tr className="border-b text-xs uppercase text-slate-500">
                  <th className="px-5 py-3">{m.product}</th><th className="px-5 py-3">{m.price}</th><th className="px-5 py-3">{m.inventory}</th><th className="px-5 py-3">{m.source}</th>
                </tr></thead>
                <tbody>{(q.data ?? []).map(p => <tr key={p.id} className="border-b border-slate-50">
                  <td className="px-5 py-3 font-medium">{p.name}<div className="text-xs text-slate-400">{p.sku || p.category || m.noSku}</div></td>
                  <td className="px-5 py-3">{p.price} {p.currency}</td>
                  <td className="px-5 py-3"><input type="number" value={p.inventory} disabled={inventoryMut.isPending} onChange={e => inventoryMut.mutate({ id: p.id, value: Number(e.target.value) })} className="w-24 rounded border px-2 py-1" aria-label={m.inventory} /></td>
                  <td className="px-5 py-3 text-slate-500">{p.source}</td>
                </tr>)}</tbody>
              </table>
              {(q.data ?? []).length === 0 && <div className="p-12 text-center"><Package className="mx-auto h-8 w-8 text-slate-300" /><p className="mt-3 text-sm text-slate-600">{m.empty}</p></div>}
             </div>}
            {inventoryMut.isError && <p className="p-4 text-sm text-red-600">{getErrorMessage(inventoryMut.error).toLowerCase().includes("permission") ? m.permissionDenied : m.inventoryError}</p>}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
