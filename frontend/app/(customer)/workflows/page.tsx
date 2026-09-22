"use client";

import Link from "next/link";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Workflow as WorkflowIcon } from "lucide-react";

import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { EmptyState } from "@/components/ui/empty-state";
import { createWorkflow, getErrorMessage, api } from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";
import type { APIResponse, Workflow } from "@/types";

async function listWorkflows() {
  const res = await api.get<APIResponse<Workflow[]>>("/workflows");
  if (!res.data.success || !res.data.data) throw new Error("Unable to load workflows");
  return res.data.data;
}

function slugify(value: string) {
  return value.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 100);
}

function isPermissionError(error: unknown) {
  return getErrorMessage(error).toLowerCase().includes("permission") ||
    getErrorMessage(error).includes("403");
}

export default function WorkflowsPage() {
  const { t } = useI18n();
  const m = t.workflows;
  const qc = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [slugTouched, setSlugTouched] = useState(false);
  const [triggerType, setTriggerType] = useState<"manual" | "schedule" | "event">("manual");
  const [maxRuntime, setMaxRuntime] = useState("");

  const q = useQuery({ queryKey: ["workflows"], queryFn: listWorkflows });

  const createM = useMutation({
    mutationFn: () => {
      const runtime = maxRuntime.trim() ? Number(maxRuntime) : null;
      if (!name.trim()) throw new Error(m.nameRequired);
      if (!slug.trim()) throw new Error(m.slugRequired);
      if (runtime !== null && (!Number.isInteger(runtime) || runtime < 1 || runtime > 2592000)) {
        throw new Error(m.invalidRuntime);
      }
      return createWorkflow({
        name: name.trim(),
        slug: slug.trim(),
        trigger_type: triggerType,
        max_runtime_seconds: runtime,
        steps: [{
          key: "initial_step",
          type: "condition",
          retry_max: 0,
          timeout_seconds: 86400,
          condition_ref: "context.ready",
          condition_value: true,
          metadata: {},
        }],
      });
    },
    onSuccess: async (workflow) => {
      await qc.invalidateQueries({ queryKey: ["workflows"] });
      setShowCreate(false);
      setName("");
      setSlug("");
      setSlugTouched(false);
      setTriggerType("manual");
      setMaxRuntime("");
      window.location.href = `/workflows/${workflow.id}/builder`;
    },
  });

  const closeModal = () => {
    if (createM.isPending) return;
    setShowCreate(false);
    createM.reset();
  };

  const openCreate = () => {
    createM.reset();
    setShowCreate(true);
  };

  return (
    <>
      <Header title={m.title} description={m.description} />
      <div className="space-y-6 p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">{m.catalog}</h2>
            <p className="mt-1 max-w-3xl text-sm text-gray-500">{m.catalogDescription}</p>
          </div>
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" /> {m.create}
          </Button>
        </div>

        {q.isLoading && <Card><CardContent className="flex justify-center py-12"><Spinner /></CardContent></Card>}

        {q.error && (
          <Card>
            <CardContent className="space-y-3 p-6">
              <p className="text-sm text-red-600">{isPermissionError(q.error) ? m.permissionDenied : m.error}</p>
              <Button variant="secondary" onClick={() => q.refetch()}>{m.retry}</Button>
            </CardContent>
          </Card>
        )}

        {!q.isLoading && !q.error && (
          q.data?.length ? (
            <Card>
              <CardContent className="p-0">
                <div className="overflow-auto">
                  <table className="w-full text-sm">
                    <thead><tr className="border-b text-start text-xs uppercase text-gray-500">
                      <th className="px-5 py-3">{m.nameColumn}</th>
                      <th className="px-5 py-3">{m.slug}</th>
                      <th className="px-5 py-3">{m.status}</th>
                      <th className="px-5 py-3">{m.version}</th>
                      <th className="px-5 py-3">{m.builder}</th>
                    </tr></thead>
                    <tbody>
                      {q.data.map((w) => (
                        <tr key={w.id} className="border-b hover:bg-gray-50">
                          <td className="px-5 py-3">
                            <Link className="font-medium text-brand-600 hover:underline" href={`/workflows/${w.id}`}>{w.name}</Link>
                          </td>
                          <td className="px-5 py-3 text-gray-600">{w.slug}</td>
                          <td className="px-5 py-3">{w.is_active ? m.active : m.disabled}</td>
                          <td className="px-5 py-3 text-gray-600">{w.current_version_id?.slice(0, 8) ?? m.noVersion}</td>
                          <td className="px-5 py-3">
                            <Link className="text-brand-600 hover:underline" href={`/workflows/${w.id}/builder`}>{m.openBuilder}</Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          ) : (
            <EmptyState icon={WorkflowIcon} title={m.emptyTitle} description={m.emptyDescription} action={<Button onClick={openCreate}><Plus className="h-4 w-4" /> {m.create}</Button>} />
          )
        )}
      </div>

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" role="dialog" aria-modal="true" aria-labelledby="create-workflow-title">
          <div className="w-full max-w-lg rounded-2xl bg-white shadow-2xl">
            <div className="border-b px-6 py-5">
              <h2 id="create-workflow-title" className="text-lg font-semibold text-gray-900">{m.createTitle}</h2>
              <p className="mt-1 text-sm text-gray-500">{m.createDescription}</p>
            </div>
            <div className="space-y-5 px-6 py-6">
              {createM.error && (
                <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {isPermissionError(createM.error) ? m.permissionDenied : getErrorMessage(createM.error) || m.createError}
                </div>
              )}
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">{m.name}</label>
                <Input value={name} onChange={(e) => { setName(e.target.value); if (!slugTouched) setSlug(slugify(e.target.value)); }} placeholder={m.namePlaceholder} autoFocus />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">{m.slug}</label>
                <Input value={slug} onChange={(e) => { setSlugTouched(true); setSlug(slugify(e.target.value)); }} placeholder={m.slugPlaceholder} />
                <p className="mt-1 text-xs text-gray-500">{m.slugHelp}</p>
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">{m.trigger}</label>
                <select value={triggerType} onChange={(e) => setTriggerType(e.target.value as typeof triggerType)} className="h-10 w-full rounded-lg border border-gray-300 bg-white px-3 text-sm">
                  <option value="manual">{m.manual}</option>
                  <option value="schedule">{m.schedule}</option>
                  <option value="event">{m.event}</option>
                </select>
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">{m.maxRuntime} <span className="font-normal text-gray-400">{m.secondsOptional}</span></label>
                <Input type="number" min={1} max={2592000} value={maxRuntime} onChange={(e) => setMaxRuntime(e.target.value)} placeholder={m.maxRuntimePlaceholder} />
              </div>
            </div>
            <div className="flex justify-end gap-3 border-t bg-gray-50 px-6 py-4">
              <Button variant="secondary" onClick={closeModal} disabled={createM.isPending}>{m.cancel}</Button>
              <Button onClick={() => createM.mutate()} disabled={createM.isPending} loading={createM.isPending}>
                {createM.isPending ? m.creating : m.create}
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
