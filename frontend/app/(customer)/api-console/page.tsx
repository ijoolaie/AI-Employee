"use client";

import { useMemo, useState } from "react";
import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { getErrorMessage } from "@/lib/errors";
import { Code2, Play, Terminal } from "lucide-react";

type Method = "GET" | "POST" | "PATCH" | "DELETE";

interface EndpointDef {
  method: Method;
  path: string; // relative to /api/v1, e.g. /employees/{employee_id}
  summary: string;
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
    name: "Employees",
    endpoints: [
      { method: "GET", path: "/employees", summary: "List AI employees for the current tenant" },
      { method: "GET", path: "/employees/available-tools", summary: "List tools an employee can be given" },
      { method: "GET", path: "/employees/{employee_id}", summary: "Get a single employee" },
      {
        method: "POST",
        path: "/employees",
        summary: "Create a new AI employee",
        sampleBody: { name: "Support Agent", role: "customer_support", system_prompt: "You are a helpful support agent." },
      },
    ],
  },
  {
    name: "Runs",
    endpoints: [
      { method: "GET", path: "/runs", summary: "List runs (optionally by employee)" },
      { method: "GET", path: "/runs/{run_id}", summary: "Get a run" },
      { method: "GET", path: "/runs/{run_id}/trace", summary: "Get the full execution trace for a run" },
      {
        method: "POST",
        path: "/runs",
        summary: "Create/execute a run",
        sampleBody: { employee_id: "", input_data: { message: "Hello" } },
      },
    ],
  },
  {
    name: "API Keys",
    endpoints: [
      { method: "GET", path: "/api-keys", summary: "List API keys" },
      { method: "POST", path: "/api-keys", summary: "Create a new API key", sampleBody: { name: "CI key" } },
      { method: "POST", path: "/api-keys/{key_id}/revoke", summary: "Revoke an API key" },
    ],
  },
  {
    name: "Knowledge",
    endpoints: [
      {
        method: "POST",
        path: "/knowledge/search",
        summary: "Semantic search over indexed documents",
        sampleBody: { query: "refund policy", limit: 5 },
      },
      {
        method: "POST",
        path: "/knowledge/index",
        summary: "Index a document",
        sampleBody: { title: "FAQ", content: "..." },
      },
    ],
  },
  {
    name: "Workflows",
    endpoints: [
      { method: "GET", path: "/workflows", summary: "List workflows" },
      { method: "GET", path: "/workflows/{workflow_id}/runs", summary: "List runs for a workflow" },
      { method: "GET", path: "/workflows/{workflow_id}/runs/{run_id}/observability", summary: "Observability for a workflow run" },
      { method: "POST", path: "/workflows/{workflow_id}/runs", summary: "Start a workflow run", sampleBody: { input_data: {} } },
      { method: "POST", path: "/workflows/{workflow_id}/runs/{run_id}/cancel", summary: "Cancel a workflow run" },
    ],
  },
  {
    name: "Operations",
    endpoints: [
      { method: "GET", path: "/operations/metrics", summary: "Outbox / workflow operational metrics" },
      { method: "GET", path: "/operations/audit-logs", summary: "Tenant audit log events" },
      { method: "GET", path: "/operations/dead-letters", summary: "List dead-lettered messages" },
      { method: "POST", path: "/operations/dead-letters/{message_id}/replay", summary: "Replay a dead-lettered message" },
    ],
  },
  {
    name: "Billing",
    endpoints: [
      { method: "GET", path: "/billing/plans", summary: "List available plans" },
      { method: "GET", path: "/billing/subscription", summary: "Current subscription" },
      { method: "GET", path: "/billing/entitlements", summary: "Current plan entitlements" },
      { method: "POST", path: "/billing/checkout", summary: "Create a Stripe checkout session" },
      { method: "POST", path: "/billing/portal", summary: "Create a Stripe billing-portal session" },
    ],
  },
  {
    name: "Usage",
    endpoints: [{ method: "GET", path: "/usage/summary", summary: "Token/run/cost usage summary" }],
  },
  {
    name: "Commerce",
    endpoints: [
      { method: "GET", path: "/customers", summary: "List CRM customers" },
      { method: "GET", path: "/orders", summary: "List orders" },
      { method: "GET", path: "/orders/summary", summary: "Order summary metrics" },
      { method: "GET", path: "/products", summary: "List products" },
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
      setError(`Fill in path parameter(s): ${missing.join(", ")}`);
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
        setError("Request body is not valid JSON.");
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
        title="API Console"
        description="Browse tenant-scoped endpoints and call them live using your current session"
      />
      <div className="grid gap-6 p-6 xl:grid-cols-[280px_minmax(0,1fr)]">
        <Card className="h-fit">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Code2 className="h-4 w-4" /> Endpoints
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
                      className={`flex w-full items-start gap-2 px-4 py-2.5 text-left text-sm transition hover:bg-gray-50 ${
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
              <p className="mt-1 text-sm text-gray-500">{endpoint.summary}</p>
            </CardHeader>
            <CardContent className="space-y-4">
              {params.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Path parameters</p>
                  {params.map((p) => (
                    <div key={p} className="flex items-center gap-3">
                      <label className="w-40 shrink-0 font-mono text-xs text-gray-600">{p}</label>
                      <input
                        value={paramValues[p] ?? ""}
                        onChange={(e) => setParamValues((prev) => ({ ...prev, [p]: e.target.value }))}
                        placeholder={`value for ${p}`}
                        className="flex-1 rounded-lg border px-3 py-2 text-sm font-mono"
                      />
                    </div>
                  ))}
                </div>
              )}

              {["POST", "PATCH"].includes(endpoint.method) && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Request body (JSON)</p>
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
                <Play className="mr-1.5 h-4 w-4" /> Send request
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
                  <Terminal className="h-4 w-4" /> Response
                </CardTitle>
                <div className="mt-1 flex items-center gap-3 text-xs text-gray-500">
                  <Badge status={result.status >= 200 && result.status < 300 ? "completed" : "failed"} />
                  <span>HTTP {result.status || "network error"}</span>
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
            Requests are sent with your current session credentials, scoped to this tenant. For external/CI
            integrations, use a key from the{" "}
            <a href="/api-keys" className="text-brand-600 hover:underline">
              API Keys
            </a>{" "}
            page instead. The full machine-generated OpenAPI schema is served at{" "}
            <code className="rounded bg-gray-100 px-1 py-0.5">/api/v1/openapi.json</code>.
          </p>
        </div>
      </div>
    </>
  );
}
