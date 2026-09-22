"use client";

import { use, useState } from "react";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import {
  createRun,
  getEmployee,
  createCustomerChannel,
  listCustomerChannels,
  getErrorMessage,
  listFiles,
  listRuns,
  getEmployeeGuardrails, updateEmployeeGuardrails,
} from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Play, Copy, MessageCircle } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function EmployeeDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const qc = useQueryClient();
  const [inputJson, setInputJson] = useState("{}");
  const [selectedFileId, setSelectedFileId] = useState("");
  const [runError, setRunError] = useState<string | null>(null);
  const [channelName, setChannelName] = useState("Website Sales Assistant");
  const [channelCreated, setChannelCreated] = useState<string | null>(null);
  const [guardrailsJson, setGuardrailsJson] = useState("{}");

  const empQ = useQuery({
    queryKey: ["employees", id],
    queryFn: () => getEmployee(id),
  });
  const guardrailsQ = useQuery({ queryKey: ["guardrails", id], queryFn: () => getEmployeeGuardrails(id) });
  const runsQ = useQuery({
    queryKey: ["runs", { employee_id: id }],
    queryFn: () => listRuns(id),
  });
  const channelsQ = useQuery({ queryKey: ["customer-channels", id], queryFn: () => listCustomerChannels(id) });
  const guardrailMutation = useMutation({ mutationFn: () => updateEmployeeGuardrails(id, { rules: JSON.parse(guardrailsJson || "{}") }), onSuccess: () => guardrailsQ.refetch() });
  const channelMutation = useMutation({ mutationFn: () => createCustomerChannel({ employee_id: id, name: channelName }), onSuccess: (channel) => { setChannelCreated(channel.public_key); qc.invalidateQueries({ queryKey: ["customer-channels", id] }); } });

  // Phase 2/5: the Report Employee and Document Employee both take exactly
  // one input (`file_id`), so they get a plain file picker instead of the
  // generic JSON textarea.
  const isReportEmployee = empQ.data?.slug === "report-employee";
  const isDocumentEmployee = empQ.data?.slug === "document-employee";
  const usesFilePicker = isReportEmployee || isDocumentEmployee;
  const filesQ = useQuery({
    queryKey: ["files"],
    queryFn: listFiles,
    enabled: usesFilePicker,
  });

  const runMutation = useMutation({
    mutationFn: createRun,
    onSuccess: (run) => {
      qc.invalidateQueries({ queryKey: ["runs"] });
      router.push(`/runs/${run.id}`);
    },
    onError: (err) => setRunError(getErrorMessage(err)),
  });

  function handleRun() {
    setRunError(null);
    if (usesFilePicker) {
      if (!selectedFileId) {
        setRunError(
          isDocumentEmployee
            ? "Choose a PDF, image, or DOCX file to analyze first."
            : "Choose a CSV/Excel file to analyze first."
        );
        return;
      }
      runMutation.mutate({ employee_id: id, input_data: { file_id: selectedFileId } });
      return;
    }
    let input_data: Record<string, unknown> = {};
    try {
      input_data = JSON.parse(inputJson || "{}");
    } catch {
      setRunError("Input must be valid JSON");
      return;
    }
    runMutation.mutate({ employee_id: id, input_data });
  }

  if (empQ.isLoading) return <Spinner className="min-h-[50vh]" />;
  if (empQ.error || !empQ.data) {
    return (
      <div className="p-6 text-sm text-red-600">
        {getErrorMessage(empQ.error) || "Employee not found"}
      </div>
    );
  }

  const emp = empQ.data;
  const runs = runsQ.data ?? [];
  const files = filesQ.data ?? [];

  return (
    <>
      <Header
        title={emp.name}
        description={`Slug: ${emp.slug} · ${emp.kind}`}
        actions={<Badge status={emp.is_active ? "active" : "inactive"} />}
      />
      <div className="space-y-6 p-6">
        <Card>
          <CardHeader><CardTitle>Publish to your customers</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-gray-600">Create a public web channel. Your customers can chat with this employee without logging into the AI Employee Platform.</p>
            <div className="flex gap-2"><input value={channelName} onChange={(e) => setChannelName(e.target.value)} className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm" /><Button onClick={() => channelMutation.mutate()} loading={channelMutation.isPending}><MessageCircle className="h-4 w-4" />Publish</Button></div>
            {channelCreated && <div className="rounded-lg border bg-slate-50 p-3 text-sm"><p className="font-medium">Customer chat URL</p><code className="mt-1 block break-all text-xs">{typeof window !== "undefined" ? window.location.origin : ""}/chat/{channelCreated}</code><button onClick={() => navigator.clipboard.writeText(`${window.location.origin}/chat/${channelCreated}`)} className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-brand-600"><Copy className="h-3 w-3" />Copy URL</button><p className="mt-2 text-xs text-gray-500">Embed on a website with: <code>&lt;script src=&quot;{typeof window !== "undefined" ? window.location.origin : ""}/widget.js?channel={channelCreated}&quot;&gt;&lt;/script&gt;</code></p></div>}
            {channelsQ.data && channelsQ.data.length > 0 && <div className="space-y-2">{channelsQ.data.map((channel) => <div key={channel.id} className="rounded-lg border px-3 py-2 text-xs"><div className="flex justify-between"><span className="font-medium">{channel.name}</span><Badge status={channel.is_active ? "active" : "inactive"} /></div><code className="break-all text-gray-500">/chat/{channel.public_key}</code></div>)}</div>}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Guardrails</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-gray-600">Control risky actions, approvals and forbidden operations. Changes publish a new employee version.</p>
            <textarea className="min-h-[140px] w-full rounded-lg border border-gray-300 px-3 py-2 font-mono text-xs" value={guardrailsJson === "{}" && guardrailsQ.data ? JSON.stringify(guardrailsQ.data.rules, null, 2) : guardrailsJson} onChange={e=>setGuardrailsJson(e.target.value)} />
            <Button size="sm" onClick={()=>guardrailMutation.mutate()} loading={guardrailMutation.isPending}>Save guardrails</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Run this employee</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {usesFilePicker ? (
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">
                  {isDocumentEmployee ? "Document file (PDF, image, or DOCX)" : "Dataset file (CSV or Excel)"}
                </label>
                {filesQ.isLoading ? (
                  <Spinner />
                ) : files.length === 0 ? (
                  <p className="text-sm text-gray-500">
                    No files uploaded yet.{" "}
                    <Link href="/files" className="text-brand-600 hover:underline">
                      Upload one on the Files page
                    </Link>{" "}
                    first.
                  </p>
                ) : (
                  <select
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                    value={selectedFileId}
                    onChange={(e) => setSelectedFileId(e.target.value)}
                  >
                    <option value="">Select a file…</option>
                    {files.map((f) => (
                      <option key={f.id} value={f.id}>
                        {f.filename} ({formatDate(f.created_at)})
                      </option>
                    ))}
                  </select>
                )}
              </div>
            ) : (
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">
                  Input (JSON)
                </label>
                <textarea
                  className="min-h-[100px] w-full rounded-lg border border-gray-300 px-3 py-2 font-mono text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                  value={inputJson}
                  onChange={(e) => setInputJson(e.target.value)}
                />
              </div>
            )}
            {runError && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {runError}
              </div>
            )}
            <Button
              onClick={handleRun}
              loading={runMutation.isPending}
              size="sm"
            >
              <Play className="h-4 w-4" />
              Start run
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Run history</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {runsQ.isLoading && <Spinner />}
            {!runsQ.isLoading && runs.length === 0 && (
              <p className="px-5 py-8 text-center text-sm text-gray-500">
                No runs for this employee yet.
              </p>
            )}
            {runs.length > 0 && (
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-gray-100 text-xs uppercase text-gray-500">
                    <th className="px-5 py-3 font-medium">ID</th>
                    <th className="px-5 py-3 font-medium">Status</th>
                    <th className="px-5 py-3 font-medium">Tokens</th>
                    <th className="px-5 py-3 font-medium">Cost</th>
                    <th className="px-5 py-3 font-medium">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map((run) => (
                    <tr
                      key={run.id}
                      className="border-b border-gray-50 hover:bg-gray-50/50"
                    >
                      <td className="px-5 py-3">
                        <Link
                          href={`/runs/${run.id}`}
                          className="font-medium text-brand-600 hover:underline"
                        >
                          {run.id.slice(0, 8)}…
                        </Link>
                      </td>
                      <td className="px-5 py-3">
                        <Badge status={run.status} />
                      </td>
                      <td className="px-5 py-3">
                        {run.total_tokens.toLocaleString()}
                      </td>
                      <td className="px-5 py-3">
                        {formatCurrency(run.total_cost_usd)}
                      </td>
                      <td className="px-5 py-3 text-gray-500">
                        {formatDate(run.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
