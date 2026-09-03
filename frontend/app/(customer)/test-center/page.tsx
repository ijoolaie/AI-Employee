"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, Play, ShieldCheck } from "lucide-react";

import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage } from "@/lib/api";
import { createTestRun, exportVerificationRecord, getTestRunArtifacts, listTestDefinitions, listTestRuns, type TestRun } from "@/lib/test-center";

function shortId(value: string) { return `${value.slice(0, 8)}…`; }
function formatDate(value: string | null) { return value ? new Date(value).toLocaleString() : "—"; }

export default function TestCenterPage() {
  const queryClient = useQueryClient();
  const [workspace, setWorkspace] = useState("");
  const [status, setStatus] = useState("");
  const [selectedRun, setSelectedRun] = useState<TestRun | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const definitionsQuery = useQuery({ queryKey: ["test-center", "definitions", workspace], queryFn: () => listTestDefinitions(workspace || undefined) });
  const runsQuery = useQuery({
    queryKey: ["test-center", "runs", workspace, status],
    queryFn: () => listTestRuns({ workspace_key: workspace || undefined, status: status || undefined }),
    refetchInterval: (query) => query.state.data?.some((run) => ["queued", "running"].includes(run.status)) ? 3000 : false,
  });
  const artifactsQuery = useQuery({ queryKey: ["test-center", "artifacts", selectedRun?.id], queryFn: () => getTestRunArtifacts(selectedRun!.id), enabled: Boolean(selectedRun) });
  const runMutation = useMutation({
    mutationFn: (definition: { id: string; workspace_key: string | null }) => createTestRun({ test_definition_id: definition.id, workspace_key: definition.workspace_key }),
    onSuccess: (run) => { setSelectedRun(run); setMessage(`Queued test run ${shortId(run.id)}.`); queryClient.invalidateQueries({ queryKey: ["test-center", "runs"] }); },
    onError: (error) => setMessage(getErrorMessage(error)),
  });

  const definitions = useMemo(() => definitionsQuery.data ?? [], [definitionsQuery.data]);
  const runs = runsQuery.data ?? [];
  const definitionById = useMemo(() => new Map(definitions.map((definition) => [definition.id, definition])), [definitions]);

  async function handleExport(runId: string) {
    try {
      const record = await exportVerificationRecord(runId);
      const blob = new Blob([JSON.stringify(record, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url; anchor.download = `test-run-${runId}-verification.json`; anchor.click(); URL.revokeObjectURL(url);
      setMessage("Verification record exported.");
    } catch (error) { setMessage(getErrorMessage(error)); }
  }

  return (<>
    <Header title="Test Center" description="Run authorized tenant-scoped tests and inspect engineering evidence." />
    <div className="space-y-6 p-6">
      <div className="flex flex-col gap-3 rounded-xl border border-gray-200 bg-white p-4 shadow-sm md:flex-row md:items-end">
        <label className="flex-1 text-sm font-medium text-gray-700">Workspace<input value={workspace} onChange={(event) => setWorkspace(event.target.value)} placeholder="All workspaces" className="mt-1 h-10 w-full rounded-lg border border-gray-300 px-3 text-sm outline-none focus:border-brand-500" /></label>
        <label className="w-full text-sm font-medium text-gray-700 md:w-52">Status<select value={status} onChange={(event) => setStatus(event.target.value)} className="mt-1 h-10 w-full rounded-lg border border-gray-300 bg-white px-3 text-sm"><option value="">All statuses</option><option value="queued">Queued</option><option value="running">Running</option><option value="passed">Passed</option><option value="failed">Failed</option><option value="cancelled">Cancelled</option><option value="expired">Expired</option></select></label>
      </div>
      {message && <div className="rounded-lg border border-brand-100 bg-brand-50 px-4 py-3 text-sm text-brand-800">{message}</div>}
      <section className="space-y-3">
        <div className="flex items-center gap-2"><ShieldCheck className="h-5 w-5 text-brand-600" /><h2 className="text-lg font-semibold text-gray-900">Available tests</h2></div>
        {definitionsQuery.isLoading && <Spinner />}
        {!definitionsQuery.isLoading && definitions.length === 0 && <EmptyState title="No test definitions" description="No enabled Test Center definitions are available for this workspace." />}
        <div className="grid gap-4 lg:grid-cols-2">{definitions.map((definition) => <div key={definition.id} className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-wide text-gray-400">{definition.code}</p><h3 className="mt-1 font-semibold text-gray-900">{definition.name}</h3><p className="mt-1 text-sm text-gray-500">{definition.description || "No description provided."}</p></div><Badge status={definition.enabled ? "enabled" : "disabled"} /></div><div className="mt-4 flex items-center justify-between text-xs text-gray-500"><span>{definition.category} · {definition.test_type}</span><Button size="sm" loading={runMutation.isPending} onClick={() => runMutation.mutate({ id: definition.id, workspace_key: definition.workspace_key })}><Play className="h-3.5 w-3.5" /> Run</Button></div></div>)}</div>
      </section>
      <section className="space-y-3"><h2 className="text-lg font-semibold text-gray-900">Run history</h2>{runsQuery.isLoading && <Spinner />}{!runsQuery.isLoading && runs.length === 0 && <EmptyState title="No test runs" description="Run an available test to create the first evidence record." />}{!runsQuery.isLoading && runs.length > 0 && <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm"><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="border-b border-gray-100 bg-gray-50 text-xs uppercase text-gray-500"><tr><th className="px-4 py-3">Run</th><th className="px-4 py-3">Test</th><th className="px-4 py-3">Workspace</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Created</th><th className="px-4 py-3 text-right">Actions</th></tr></thead><tbody>{runs.map((run) => <tr key={run.id} className="border-b border-gray-50 hover:bg-gray-50/50"><td className="px-4 py-3"><button className="font-medium text-brand-600 hover:underline" onClick={() => setSelectedRun(run)}>{shortId(run.id)}</button></td><td className="px-4 py-3 text-gray-700">{definitionById.get(run.test_definition_id)?.name || shortId(run.test_definition_id)}</td><td className="px-4 py-3 text-gray-500">{run.workspace_key || "—"}</td><td className="px-4 py-3"><Badge status={run.status} /></td><td className="px-4 py-3 text-gray-500">{formatDate(run.created_at)}</td><td className="px-4 py-3 text-right">{(run.status === "passed" || run.status === "failed") && <Button variant="ghost" size="sm" onClick={() => void handleExport(run.id)}><Download className="h-3.5 w-3.5" /> Evidence</Button>}</td></tr>)}</tbody></table></div></div>}</section>
      {selectedRun && <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm"><div className="flex flex-col justify-between gap-3 md:flex-row md:items-start"><div><p className="text-xs uppercase tracking-wide text-gray-400">Selected run</p><h2 className="mt-1 font-semibold text-gray-900">{shortId(selectedRun.id)} · {selectedRun.status}</h2><p className="mt-1 text-xs text-gray-500">Correlation: {selectedRun.correlation_id}</p></div>{(selectedRun.status === "passed" || selectedRun.status === "failed") && <Button size="sm" onClick={() => void handleExport(selectedRun.id)}><Download className="h-4 w-4" /> Export verification record</Button>}</div><div className="mt-5 grid gap-4 text-sm md:grid-cols-3"><div><p className="text-xs text-gray-400">Queued</p><p className="mt-1 text-gray-700">{formatDate(selectedRun.queued_at)}</p></div><div><p className="text-xs text-gray-400">Started</p><p className="mt-1 text-gray-700">{formatDate(selectedRun.started_at)}</p></div><div><p className="text-xs text-gray-400">Finished</p><p className="mt-1 text-gray-700">{formatDate(selectedRun.finished_at)}</p></div></div><div className="mt-5 grid gap-4 md:grid-cols-2"><div className="rounded-lg bg-gray-50 p-4"><p className="text-xs font-semibold uppercase text-gray-400">Result</p><pre className="mt-2 overflow-auto text-xs text-gray-700">{JSON.stringify(selectedRun.result || {}, null, 2)}</pre></div><div className="rounded-lg bg-gray-50 p-4"><p className="text-xs font-semibold uppercase text-gray-400">Evidence</p><pre className="mt-2 overflow-auto text-xs text-gray-700">{JSON.stringify(selectedRun.evidence || {}, null, 2)}</pre></div></div><div className="mt-5"><p className="text-xs font-semibold uppercase text-gray-400">Artifacts</p>{artifactsQuery.isLoading && <Spinner />}{!artifactsQuery.isLoading && (artifactsQuery.data ?? []).length === 0 && <p className="mt-2 text-sm text-gray-500">No artifacts attached.</p>}<ul className="mt-2 space-y-2">{(artifactsQuery.data ?? []).map((artifact) => <li key={artifact.id} className="rounded-lg border border-gray-100 px-3 py-2 text-sm"><div className="flex flex-wrap items-center justify-between gap-2"><span className="font-medium text-gray-800">{artifact.label}</span><span className="text-xs text-gray-500">{artifact.artifact_type} · {artifact.size_bytes ?? 0} bytes</span></div><p className="mt-1 break-all text-xs text-gray-500">{artifact.reference}</p>{artifact.sha256 && <p className="mt-1 break-all font-mono text-[11px] text-gray-400">SHA-256 {artifact.sha256}</p>}</li>)}</ul></div></section>}
    </div>
  </>);
}
