"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage } from "@/lib/errors";
import { listProducts, createProduct, updateProduct, updateProductInventory } from "@/lib/api";
import { Package, Plus, RefreshCw, Search } from "lucide-react";
import { useState } from "react";
import { useI18n } from "@/lib/i18n/provider";

export default function ProductsPage() {
  const qc = useQueryClient();
  const { t } = useI18n();
  const m = t.commerce.products;
  const [search, setSearch] = useState("");
  const [name, setName] = useState("");
  const [price, setPrice] = useState("0");
  const [inventory, setInventory] = useState("0");
  const [inventoryDrafts, setInventoryDrafts] = useState<Record<string, string>>({});
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editSku, setEditSku] = useState("");
  const [editCategory, setEditCategory] = useState("");
  const [editPrice, setEditPrice] = useState("0");
  const [editActive, setEditActive] = useState(true);

  const q = useQuery({
    queryKey: ["products", search],
    queryFn: () => listProducts(search.trim() || undefined),
  });

  const create = useMutation({
    mutationFn: () =>
      createProduct({
        name: name.trim(),
        price,
        currency: "EUR",
        inventory: Number(inventory),
      }),
    onSuccess: () => {
      setName("");
      setPrice("0");
      setInventory("0");
      qc.invalidateQueries({ queryKey: ["products"] });
    },
  });

  const editMut = useMutation({
    mutationFn: () => {
      if (!editingId) throw new Error("No product selected");
      return updateProduct(editingId, {
        name: editName.trim(),
        sku: editSku.trim() || null,
        category: editCategory.trim() || null,
        price: editPrice,
        is_active: editActive,
      });
    },
    onSuccess: () => {
      setEditingId(null);
      qc.invalidateQueries({ queryKey: ["products"] });
    },
  });

  const inventoryMut = useMutation({
    mutationFn: ({ id, value }: { id: string; value: number }) =>
      updateProductInventory(id, value),
    onSuccess: (_, variables) => {
      setInventoryDrafts((current) => {
        const next = { ...current };
        delete next[variables.id];
        return next;
      });
      qc.invalidateQueries({ queryKey: ["products"] });
    },
  });

  const permissionDenied =
    q.isError && getErrorMessage(q.error).toLowerCase().includes("permission");
  const createPermissionDenied =
    create.isError &&
    getErrorMessage(create.error).toLowerCase().includes("permission");
  const inventoryPermissionDenied =
    inventoryMut.isError &&
    getErrorMessage(inventoryMut.error).toLowerCase().includes("permission");

  const canCreate =
    name.trim().length > 0 &&
    Number.isFinite(Number(price)) &&
    Number(price) >= 0 &&
    Number.isInteger(Number(inventory)) &&
    Number(inventory) >= 0 &&
    !createPermissionDenied;

  const startEdit = (product: import("@/types").Product) => {
    setEditingId(product.id);
    setEditName(product.name);
    setEditSku(product.sku ?? "");
    setEditCategory(product.category ?? "");
    setEditPrice(String(product.price));
    setEditActive(product.is_active);
  };

  const retryProducts = () => {
    void q.refetch();
  };

  return (
    <>
      <Header
        title={m.title}
        description={m.description}
        actions={
          <Button
            size="sm"
            onClick={() => document.getElementById("product-name")?.focus()}
          >
            <Plus className="h-4 w-4" />
            {m.add}
          </Button>
        }
      />

      <div className="space-y-6 p-6">
        {permissionDenied && (
          <div
            role="alert"
            className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800"
          >
            {m.permissionDenied}
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle>{m.addTitle}</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-4">
            <input
              id="product-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={m.namePlaceholder}
              className="rounded-lg border px-3 py-2 text-sm"
              aria-label={m.product}
            />
            <input
              type="number"
              min="0"
              step="0.01"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder={m.pricePlaceholder}
              className="rounded-lg border px-3 py-2 text-sm"
              aria-label={m.price}
            />
            <input
              type="number"
              min="0"
              step="1"
              value={inventory}
              onChange={(e) => setInventory(e.target.value)}
              placeholder={m.inventoryPlaceholder}
              className="rounded-lg border px-3 py-2 text-sm"
              aria-label={m.inventory}
            />
            <Button
              disabled={!canCreate}
              loading={create.isPending}
              onClick={() => create.mutate()}
            >
              {m.save}
            </Button>
          </CardContent>
          {create.isError && (
            <p role="alert" className="px-6 pb-4 text-sm text-red-600">
              {createPermissionDenied ? m.permissionDenied : m.saveError}
            </p>
          )}
        </Card>

        <Card>
          <CardHeader className="space-y-4">
            <CardTitle>{m.catalog}</CardTitle>
            <div className="flex flex-col gap-2 sm:flex-row">
              <div className="relative flex-1">
                <Search className="pointer-events-none absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder={m.searchPlaceholder}
                  className="w-full rounded-lg border py-2 ps-9 pe-3 text-sm"
                  aria-label={m.search}
                />
              </div>
              <Button
                variant="outline"
                onClick={retryProducts}
                disabled={q.isFetching}
                aria-label={m.retry}
              >
                <RefreshCw className="h-4 w-4" />
                {m.retry}
              </Button>
            </div>
          </CardHeader>

          <CardContent className="p-0">
            {q.isLoading ? (
              <div className="flex justify-center p-12">
                <Spinner />
              </div>
            ) : q.isError ? (
              <div className="flex flex-col items-center gap-3 p-12 text-center">
                <p role="alert" className="text-sm text-red-600">
                  {permissionDenied ? m.permissionDenied : m.error}
                </p>
                {!permissionDenied && (
                  <Button variant="outline" onClick={retryProducts} disabled={q.isFetching}>
                    <RefreshCw className="h-4 w-4" />
                    {m.retry}
                  </Button>
                )}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-start text-sm">
                  <thead>
                    <tr className="border-b text-xs uppercase text-slate-500">
                      <th className="px-5 py-3">{m.product}</th>
                      <th className="px-5 py-3">{m.price}</th>
                      <th className="px-5 py-3">{m.inventory}</th>
                      <th className="px-5 py-3">{m.source}</th>\n                      <th className="px-5 py-3">{m.status}</th>
                      <th className="px-5 py-3">{m.actions}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(q.data ?? []).map((p) => {
                      const draft = inventoryDrafts[p.id] ?? String(p.inventory);
                      const parsedInventory = Number(draft);
                      const validInventory =
                        draft.trim() !== "" &&
                        Number.isInteger(parsedInventory) &&
                        parsedInventory >= 0;

                      return (
                        <tr key={p.id} className="border-b border-slate-50">
                          <td className="px-5 py-3 font-medium">
                            {p.name}
                            <div className="text-xs text-slate-400">
                              {p.sku || p.category || m.noSku}
                            </div>
                          </td>
                          <td className="px-5 py-3">
                            {p.price} {p.currency}
                          </td>
                          <td className="px-5 py-3">
                            <input
                              type="number"
                              min="0"
                              step="1"
                              value={draft}
                              disabled={inventoryMut.isPending}
                              onChange={(e) =>
                                setInventoryDrafts((current) => ({
                                  ...current,
                                  [p.id]: e.target.value,
                                }))
                              }
                              className="w-24 rounded border px-2 py-1"
                              aria-label={m.inventory}
                            />
                          </td>
                          <td className="px-5 py-3 text-slate-500">{p.source}</td>\n                          <td className="px-5 py-3">{p.is_active ? m.active : m.inactive}</td>
                          <td className="px-5 py-3">
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={
                                !validInventory ||
                                Number(draft) === p.inventory ||
                                inventoryMut.isPending
                              }
                              loading={
                                inventoryMut.isPending &&
                                inventoryMut.variables?.id === p.id
                              }
                              onClick={() =>
                                inventoryMut.mutate({
                                  id: p.id,
                                  value: parsedInventory,
                                })
                              }
                            >
                              {m.update}
                            </Button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>

                {(q.data ?? []).length === 0 && (
                  <div className="p-12 text-center">
                    <Package className="mx-auto h-8 w-8 text-slate-300" />
                    <p className="mt-3 text-sm text-slate-600">{m.empty}</p>
                  </div>
                )}
              </div>
            )}

            {inventoryMut.isError && (
              <p role="alert" className="p-4 text-sm text-red-600">
                {inventoryPermissionDenied
                  ? m.permissionDenied
                  : m.inventoryError}
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
