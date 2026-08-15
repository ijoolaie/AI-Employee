"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { api, getErrorMessage } from "@/lib/api";
import type { APIResponse, Workflow } from "@/types";

async function listWorkflows() {
  const res = await api.get<APIResponse<Workflow[]>>("/workflows");
  if (!res.data.success || !res.data.data) throw new Error("Unable to load workflows");
  return res.data.data;
}

export default function WorkflowsPage() {
  const q = useQuery({ queryKey: ["workflows"], queryFn: listWorkflows });
  return <><Header title="Workflows" description="Create, inspect and execute versioned workflows." /><div className="p-6 space-y-6">
    {q.isLoading && <Spinner />}
    {q.error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{getErrorMessage(q.error)}</div>}
    {!q.isLoading && !q.error && <Card><CardHeader><CardTitle>Workflow catalog</CardTitle></CardHeader><CardContent className="p-0">
      {q.data?.length ? <table className="w-full text-sm"><thead><tr className="border-b text-left text-xs uppercase text-gray-500"><th className="px-5 py-3">Name</th><th className="px-5 py-3">Slug</th><th className="px-5 py-3">Status</th><th className="px-5 py-3">Version</th><th className="px-5 py-3">Builder</th></tr></thead><tbody>{q.data.map(w=><tr key={w.id} className="border-b hover:bg-gray-50"><td className="px-5 py-3"><Link className="font-medium text-brand-600 hover:underline" href={`/workflows/${w.id}`}>{w.name}</Link></td><td className="px-5 py-3 text-gray-600">{w.slug}</td><td className="px-5 py-3">{w.is_active ? "Active" : "Disabled"}</td><td className="px-5 py-3 text-gray-600">{w.current_version_id?.slice(0,8) ?? "—"}</td><td className="px-5 py-3"><Link className="text-brand-600 hover:underline" href={`/workflows/${w.id}/builder`}>Open builder</Link></td></tr>)}</tbody></table> : <div className="px-5 py-10 text-center text-sm text-gray-500">No workflows yet.</div>}
    </CardContent></Card>}
  </div></>;
}
