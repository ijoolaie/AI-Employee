"use client";

import { useMemo, useState } from "react";
import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { getErrorMessage } from "@/lib/errors";
import { Code2, Play, Terminal } from "lucide-react";
import { useI18n } from "@/lib/i18n/provider";

type Method = "GET" | "POST" | "PATCH" | "DELETE";

interface EndpointDef {
  method: Method;
  path: string; // relative to /api/v1, e.g. /employees/{employee_id}
  summary?: string;
  sampleBody?: Record<string, unknown>;
}

interface EndpointGroup {
  name: string;
  endpoints: EndpointDef[];
}

// Curated, tenant-relevant subset of the API surface. Kept in sync with
// backend/app/api/v1/*.py route declarations. The full machine-generated
// spec is always available at {API base}/openapi.json for external tooling.
const CATALOG: EndpointGroup[] = [
  {
    name: "employees",
    endpoints: [
      { method: "GET", path: "/employees" },
      { method: "GET", path: "/employees/available-tools" },
      { method: "GET", path: "/employees/{employee_id}" },
      {
        method: "POST",
        path: "/employees",
        
        sampleBody: { name: "Support Agent", role: "customer_support", system_prompt: "You are a helpful support agent." },
      },
    ],
  },
  {
    name: "runs",
    endpoints: [
      { method: "GET", path: "/runs" },
      { method: "GET", path: "/runs/{run_id}" },
      { method: "GET", path: "/runs/{run_id}/trace" },
      {
        method: "POST",
        path: "/runs",
        
        sampleBody: { employee_id: "", input_data: { message: "Hello" } },
      },
    ],
  },
  {
    name: "apiKeys",
    endpoints: [
      { method: "GET", path: "/api-keys" },
      { method: "POST", path: "/api-keys",  sampleBody: { name: "CI key" } },
      { method: "POST", path: "/api-keys/{key_id}/revoke" },
    ],
  },
  {
    name: "knowledge",
    endpoints: [
      {
        method: "POST",
        path: "/knowledge/search",
        
        sampleBody: { query: "refund policy", limit: 5 },
      },
      {
        method: "POST",
        path: "/knowledge/index",
        
        sampleBody: { title: "FAQ", content: "..." },
      },
    ],
  },
  {
    name: "workflows",
    endpoints: [
      { method: "GET", path: "/workflows" },
      { method: "GET", path: "/workflows/{workflow_id}/runs" },
      { method: "GET", path: "/workflows/{workflow_id}/runs/{run_id}/observability" },
      { method: "POST", path: "/workflows/{workflow_id}/runs",  sampleBody: { input_data: {} } },
      { method: "POST", path: "/workflows/{workflow_id}/runs/{run_id}/cancel" },
    ],
  },
  {
    name: "operations",
    endpoints: [
      { method: "GET", path: "/operations/metrics" },
      { method: "GET", path: "/operations/audit-logs" },
      { method: "GET", path: "/operations/dead-letters" },
      { method: "POST", path: "/operations/dead-letters/{message_id}/replay" },
    ],
  },
  {
    name: "billing",
    endpoints: [
      { method: "GET", path: "/billing/plans" },
      { method: "GET", path: "/billing/subscription" },
      { method: "GET", path: "/billing/entitlements" },
      { method: "POST", path: "/billing/checkout" },
      { method: "POST", path: "/billing/portal" },
    ],
  },
  {
    name: "usage",
    endpoints: [{ method: "GET", path: "/usage/summary" }],
  },
  {
    name: "commerce",
    endpoints: [
      { method: "GET", path: "/customers" },
      { method: "GET", path: "/orders" },
      { method: "GET", path: "/orders/summary" },
      { method: "GET", path: "/products" },
    ],
  },
];

function methodColor(m: Method) {
  switch (m) {
    case "GET":
      return "bg-blue-50 text-blue-700 border-blue-200";
    case "POST":
      return "bg-green-50 text-green-700 border-green-200";
    case "PATCH":
      return "bg-amber-50 text-amber-700 border-amber-200";
    case "DELETE":
      return "bg-red-50 text-red-700 border-red-200";
  }
}

function extractParams(path: string): string[] {
  const matches = path.match(/\{([^}]+)\}/g) ?? [];
  return matches.map((m) => m.slice(1, -1));
}

export default function ApiConsolePage() {
  const { t } = useI18n();
  const m = t.developerSurfaces.apiConsole;
  const [groupIdx, setGroupIdx] = useState(0);
  const [endpointIdx, setEndpointIdx] = useState(0);
  const endpoint = CATALOG[groupIdx].endpoints[endpointIdx];
  const params = useMemo(() => extractParams(endpoint.path), [endpoint.path]);

  const [paramValues, setParamValues] = useState<Record<string, string>>({});
  const [bodyText, setBodyText] = useState<string>(
    endpoint.sampleBody ? JSON.stringify(endpoint.sampleBody, null, 2) : ""
  );
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState<{ status: number; ms: number; data: unknown } | null>(null);
  const [error, setError] = useState<string | null>(null);

  function selectEndpoint(g: number, e: number) {
    setGroupIdx(g);
    setEndpointIdx(e);
    const next = CATALOG[g].endpoints[e];
    setParamValues({});
    setBodyText(next.sampleBody ? JSON.stringify(next.sampleBody, null, 2) : "");
    setResult(null);
    setError(null);
  }

  async function send() {
    setSending(true);
    setError(null);
    setResult(null);
    const missing = params.filter((p) => !paramValues[p]?.trim());
    if (missing.length) {
      setError(`${m.fillParams}: ${missing.join(", ")}`);
      setSending(false);
      return;
    }
    let url = endpoint.path;
    for (const p of params) url = url.replace(`{${p}}`, encodeURIComponent(paramValues[p]));

    let data: unknown = undefined;
    if (["POST", "PATCH"].includes(endpoint.method) && bodyText.trim()) {
      try {
        data = JSON.parse(bodyText);
      } catch {
        setError(m.invalidJson);
        setSending(false);
        return;
      }
    }

    const started = performance.now();
    try {
      const res = await api.request({ method: endpoint.method, url, data });
      setResult({ status: res.status, ms: Math.round(performance.now() - started), data: res.data });
    } catch (err) {
      setResult({
        status:
          (err as { response?: { status?: number } })?.response?.status ?? 0,
        ms: Math.round(performance.now() - started),
        data: (err as { response?: { data?: unknown } })?.response?.data ?? null,
      });
      setError(getErrorMessage(err));
    } finally {
      setSending(false);
    }
  }

  return (
    <>
      <Header
        title={m.title}
        description={m.description}
      />
      <div className="grid gap-6 p-6 xl:grid-cols-[280px_minmax(0,1fr)]" dir="auto">
        <Card className="h-fit">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Code2 className="h-4 w-4" /> {m.endpoints}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="max-h-[720px] overflow-y-auto">
              {CATALOG.map((group, g) => (
                <div key={group.name} className="border-b last:border-0">
                  <p className="bg-gray-50 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                    {group.name}
                  </p>
                  {group.endpoints.map((ep, e) => (
                    <button
                      key={`${ep.method}-${ep.path}`}
                      onClick={() => selectEndpoint(g, e)}
                      className={`flex w-full items-start gap-2 px-4 py-2.5 text-start text-sm transition hover:bg-gray-50 ${
                        g === groupIdx && e === endpointIdx ? "bg-brand-50" : ""
                      }`}
                    >
                      <span
                        className={`mt-0.5 shrink-0 rounded border px-1.5 py-0.5 text-[10px] font-semibold ${methodColor(
                          ep.method
                        )}`}
                      >
                        {ep.method}
                      </span>
                      <span className="min-w-0 truncate font-mono text-xs text-gray-700">{ep.path}</span>
                    </button>
                  ))}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <span className={`rounded border px-2 py-0.5 text-xs font-semibold ${methodColor(endpoint.method)}`}>
                  {endpoint.method}
                </span>
                <span className="font-mono text-sm text-gray-900">/api/v1{endpoint.path}</span>
              </CardTitle>
              <p className="mt-1 text-sm text-gray-500">{m.catalogDescriptions[CATALOG[groupIdx].name as keyof typeof m.catalogDescriptions]}</p>
            </CardHeader>
            <CardContent className="space-y-4">
              {params.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">{m.pathParams}</p>
                  {params.map((p) => (
                    <div key={p} className="flex items-center gap-3">
                      <label className="w-40 shrink-0 font-mono text-xs text-gray-600">{p}</label>
                      <input
                        value={paramValues[p] ?? ""}
                        onChange={(e) => setParamValues((prev) => ({ ...prev, [p]: e.target.value }))}
                        placeholder={`${m.valueFor} ${p}`}
                        className="flex-1 rounded-lg border px-3 py-2 text-sm font-mono"
                      />
                    </div>
                  ))}
                </div>
              )}

              {["POST", "PATCH"].includes(endpoint.method) && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">{m.requestBody} (JSON)</p>
                  <textarea
                    value={bodyText}
                    onChange={(e) => setBodyText(e.target.value)}
                    rows={8}
                    className="w-full rounded-lg border bg-gray-950 px-3 py-2 font-mono text-xs text-gray-100"
                    spellCheck={false}
                  />
                </div>
              )}

              <Button onClick={send} loading={sending} disabled={sending}>
                <Play className="me-1.5 h-4 w-4" /> {m.send}
              </Button>

              {error && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
              )}
            </CardContent>
          </Card>

          {result && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Terminal className="h-4 w-4" /> {m.response}
                </CardTitle>
                <div className="mt-1 flex items-center gap-3 text-xs text-gray-500">
                  <Badge status={result.status >= 200 && result.status < 300 ? "completed" : "failed"} />
                  <span>HTTP {result.status || m.networkError}</span>
                  <span>{result.ms} ms</span>
                </div>
              </CardHeader>
              <CardContent>
                <pre className="max-h-[420px] overflow-auto rounded-lg bg-gray-950 p-4 text-xs text-gray-100">
                  {JSON.stringify(result.data, null, 2)}
                </pre>
              </CardContent>
            </Card>
          )}

          <p className="text-xs text-gray-400">
            {m.technical} For external/CI
            integrations, use a key from the{" "}
            <a href="/api-keys" className="text-brand-600 hover:underline">
              API Keys
            </a>{" "}
            page instead. {m.openapi}{" "}
            <code className="rounded bg-gray-100 px-1 py-0.5">/api/v1/openapi.json</code>.
          </p>
        </div>
      </div>
    </>
  );
}
