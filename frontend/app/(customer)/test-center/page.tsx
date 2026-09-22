"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, Play, RefreshCw, ShieldCheck } from "lucide-react";

import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage } from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";
import { createTestRun, dispatchTestRun, exportVerificationRecord, getTestRun, getTestRunArtifacts, listTestDefinitions, listTestRuns, type TestRun } from "@/lib/test-center";

function shortId(value: string) { return `${value.slice(0, 8)}…`; }
function formatDate(value: string | null) { return value ? new Date(value).toLocaleString() : "—"; }
function isActiveStatus(value: string) { return ["queued", "running"].includes(value); }

export default function TestCenterPage() {
  const { t } = useI18n();
  const m = t.testCenter;
  const queryClient = useQueryClient();
  const [workspace, setWorkspace] = useState("");
  const [status, setStatus] = useState("");
  const [selectedRun, setSelectedRun] = useState<TestRun | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const definitionsQuery = useQuery({ queryKey: ["test-center", "definitions", workspace], queryFn: () => listTestDefinitions(workspace || undefined) });
  const runsQuery = useQuery({
    queryKey: ["test-center", "runs", workspace, status],
    queryFn: () => listTestRuns({ workspace_key: workspace || undefined, status: status || undefined }),
    refetchInterval: (query) => query.state.data?.some((run) => isActiveStatus(run.status)) ? 3000 : false,
  });
  const selectedRunQuery = useQuery({
    queryKey: ["test-center", "run", selectedRun?.id],
    queryFn: () => getTestRun(selectedRun!.id),
    enabled: Boolean(selectedRun),
    refetchInterval: (query) => query.state.data && isActiveStatus(query.state.data.status) ? 1500 : false,
  });
  const artifactsQuery = useQuery({ queryKey: ["test-center", "artifacts", selectedRun?.id], queryFn: () => getTestRunArtifacts(selectedRun!.id), enabled: Boolean(selectedRun) });

  const runMutation = useMutation({
    mutationFn: async (definition: { id: string; workspace_key: string | null }) => {
      const run = await createTestRun({ test_definition_id: definition.id, workspace_key: definition.workspace_key });
      const dispatch = await dispatchTestRun(run.id);
      return { run, dispatch };
    },
    onSuccess: ({ run, dispatch }) => {
      setSelectedRun(run);
      setMessage(`${m.dispatched} ${shortId(run.id)} ${m.toWorker} (${shortId(dispatch.task_id)}).`);
      queryClient.invalidateQueries({ queryKey: ["test-center", "runs"] });
      queryClient.invalidateQueries({ queryKey: ["test-center", "run", run.id] });
    },
    onError: (error) => setMessage(getErrorMessage(error)),
  });

  const definitions = useMemo(() => definitionsQuery.data ?? [], [definitionsQuery.data]);
  const runs = runsQuery.data ?? [];
  const liveSelectedRun = selectedRunQuery.data ?? selectedRun;
  const definitionById = useMemo(() => new Map(definitions.map((definition) => [definition.id, definition])), [definitions]);

  async function refreshSelectedRun() {
    if (!selectedRun) return;
    try {
      await Promise.all([selectedRunQuery.refetch(), artifactsQuery.refetch(), runsQuery.refetch()]);
      setMessage(m.refreshed);
    } catch (error) { setMessage(getErrorMessage(error)); }
  }

  async function handleExport(runId: string) {
    try {
      const record = await exportVerificationRecord(runId);
      const blob = new Blob([JSON.stringify(record, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url; anchor.download = `test-run-${runId}-verification.json`; anchor.click(); URL.revokeObjectURL(url);
      setMessage(m.exported);
    } catch (error) { setMessage(getErrorMessage(error)); }
  }

  return (<>
    <Header title={m.title} description={m.description} />
    <div className="space-y-6 p-6">
      <div className="flex flex-col gap-3 rounded-xl border border-gray-200 bg-white p-4 shadow-sm md:flex-row md:items-end">
        <label className="flex-1 text-sm font-medium text-gray-700">{m.workspace}<input value={workspace} onChange={(event) => setWorkspace(event.target.value)} placeholder={m.allWorkspaces} className="mt-1 h-10 w-full rounded-lg border border-gray-300 px-3 text-sm outline-none focus:border-brand-500" /></label>
        <label className="w-full text-sm font-medium text-gray-700 md:w-52">{m.status}<select value={status} onChange={(event) => setStatus(event.target.value)} className="mt-1 h-10 w-full rounded-lg border border-gray-300 bg-white px-3 text-sm"><option value="">{m.allStatuses}</option><option value="queued">{m.queued}</option><option value="running">{m.running}</option><option value="passed">{m.passed}</option><option value="failed">{m.failed}</option><option value="cancelled">{m.cancelled}</option><option value="expired">{m.expired}</option></select></label>
      </div>
      {message && <div className="rounded-lg border border-brand-100 bg-brand-50 px-4 py-3 text-sm text-brand-800">{message}</div>}
      <section className="space-y-3">
        <div className="flex items-center gap-2"><ShieldCheck className="h-5 w-5 text-brand-600" /><h2 className="text-lg font-semibold text-gray-900">{m.availableTests}</h2></div>
        {definitionsQuery.isLoading && <Spinner />}
        {!definitionsQuery.isLoading && definitions.length === 0 && <EmptyState title={m.noDefinitions} description={m.noDefinitionsDescription} />}
        <div className="grid gap-4 lg:grid-cols-2">{definitions.map((definition) => <div key={definition.id} className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-wide text-gray-400">{definition.code}</p><h3 className="mt-1 font-semibold text-gray-900">{definition.name}</h3><p className="mt-1 text-sm text-gray-500">{definition.description || "{m.noDescription}"}</p></div><Badge status={definition.enabled ? "enabled" : "disabled"} /></div><div className="mt-4 flex items-center justify-between text-xs text-gray-500"><span>{definition.edition} · {definition.service_group} · {definition.category} · {definition.test_type}</span><Button size="sm" loading={runMutation.isPending} onClick={() => runMutation.mutate({ id: definition.id, workspace_key: definition.workspace_key })}><Play className="h-3.5 w-3.5" /> {m.run}</Button></div></div>)}</div>
      </section>
      <section className="space-y-3"><h2 className="text-lg font-semibold text-gray-900">{m.runHistory}</h2>{runsQuery.isLoading && <Spinner />}{!runsQuery.isLoading && runs.length === 0 && <EmptyState title={m.noRuns} description={m.noRunsDescription} />}{!runsQuery.isLoading && runs.length > 0 && <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm"><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="border-b border-gray-100 bg-gray-50 text-xs uppercase text-gray-500"><tr><th className="px-4 py-3">{m.testRun}</th><th className="px-4 py-3">{m.test}</th><th className="px-4 py-3">{m.workspaceColumn}</th><th className="px-4 py-3">{m.status}</th><th className="px-4 py-3">{m.created}</th><th className="px-4 py-3 text-right">{m.actions}</th></tr></thead><tbody>{runs.map((run) => <tr key={run.id} className="border-b border-gray-50 hover:bg-gray-50/50"><td className="px-4 py-3"><button className="font-medium text-brand-600 hover:underline" onClick={() => setSelectedRun(run)}>{shortId(run.id)}</button></td><td className="px-4 py-3 text-gray-700">{definitionById.get(run.test_definition_id)?.name || shortId(run.test_definition_id)}</td><td className="px-4 py-3 text-gray-500">{run.workspace_key || "—"}</td><td className="px-4 py-3"><Badge status={run.status} /></td><td className="px-4 py-3 text-gray-500">{formatDate(run.created_at)}</td><td className="px-4 py-3 text-right">{(run.status === "passed" || run.status === "failed") && <Button variant="ghost" size="sm" onClick={() => void handleExport(run.id)}><Download className="h-3.5 w-3.5" /> {m.evidence}</Button>}</td></tr>)}</tbody></table></div></div>}</section>
      {liveSelectedRun && <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm"><div className="flex flex-col justify-between gap-3 md:flex-row md:items-start"><div><p className="text-xs uppercase tracking-wide text-gray-400">{m.selectedRun}</p><div className="mt-1 flex items-center gap-2"><h2 className="font-semibold text-gray-900">{shortId(liveSelectedRun.id)}</h2><Badge status={liveSelectedRun.status} /></div><p className="mt-1 text-xs text-gray-500">{m.correlation}: {liveSelectedRun.correlation_id}</p>{isActiveStatus(liveSelectedRun.status) && <p className="mt-2 text-xs text-brand-600">{m.liveRefresh}</p>}</div><div className="flex gap-2"><Button variant="ghost" size="sm" loading={selectedRunQuery.isFetching || artifactsQuery.isFetching} onClick={() => void refreshSelectedRun()}><RefreshCw className="h-4 w-4" /> {m.refresh}</Button>{(liveSelectedRun.status === "passed" || liveSelectedRun.status === "failed") && <Button size="sm" onClick={() => void handleExport(liveSelectedRun.id)}><Download className="h-4 w-4" /> Export verification record</Button>}</div></div><div className="mt-5 grid gap-4 text-sm md:grid-cols-3"><div><p className="text-xs text-gray-400">{m.queuedAt}</p><p className="mt-1 text-gray-700">{formatDate(liveSelectedRun.queued_at)}</p></div><div><p className="text-xs text-gray-400">{m.started}</p><p className="mt-1 text-gray-700">{formatDate(liveSelectedRun.started_at)}</p></div><div><p className="text-xs text-gray-400">{m.finished}</p><p className="mt-1 text-gray-700">{formatDate(liveSelectedRun.finished_at)}</p></div></div>{liveSelectedRun.error && <div className="mt-5 rounded-lg border border-red-200 bg-red-50 p-4"><p className="text-xs font-semibold uppercase text-red-500">{m.executionError}</p><p className="mt-2 whitespace-pre-wrap text-sm text-red-800">{liveSelectedRun.error}</p></div>}<div className="mt-5 grid gap-4 md:grid-cols-2"><div className="rounded-lg bg-gray-50 p-4"><p className="text-xs font-semibold uppercase text-gray-400">{m.result}</p><pre className="mt-2 overflow-auto text-xs text-gray-700">{JSON.stringify(liveSelectedRun.result || {}, null, 2)}</pre></div><div className="rounded-lg bg-gray-50 p-4"><p className="text-xs font-semibold uppercase text-gray-400">{m.evidence}</p><pre className="mt-2 overflow-auto text-xs text-gray-700">{JSON.stringify(liveSelectedRun.evidence || {}, null, 2)}</pre></div></div><div className="mt-5"><p className="text-xs font-semibold uppercase text-gray-400">{m.artifacts}</p>{artifactsQuery.isLoading && <Spinner />}{!artifactsQuery.isLoading && (artifactsQuery.data ?? []).length === 0 && <p className="mt-2 text-sm text-gray-500">{m.noArtifacts}</p>}<ul className="mt-2 space-y-2">{(artifactsQuery.data ?? []).map((artifact) => <li key={artifact.id} className="rounded-lg border border-gray-100 px-3 py-2 text-sm"><div className="flex flex-wrap items-center justify-between gap-2"><span className="font-medium text-gray-800">{artifact.label}</span><span className="text-xs text-gray-500">{artifact.artifact_type} · {artifact.size_bytes ?? 0} bytes</span></div><p className="mt-1 break-all text-xs text-gray-500">{artifact.reference}</p>{artifact.sha256 && <p className="mt-1 break-all font-mono text-[11px] text-gray-400">SHA-256 {artifact.sha256}</p>}</li>)}</ul></div></section>}
    </div>
  </>);
}
