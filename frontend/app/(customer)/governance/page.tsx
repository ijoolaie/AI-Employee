"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { api, getErrorMessage } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { ShieldCheck, RefreshCw, Plus, CheckCircle2, XCircle, Play, UserCheck } from "lucide-react";

interface RegistryItem {
  agent_instance_id: string;
  agent_definition_id: string;
  agent_template_id: string | null;
  name: string;
  definition: { slug: string; name: string; version: number; enabled: boolean };
  template: { slug: string; name: string; version: number; status: string } | null;
  status: string;
  enabled: boolean;
  risk_tier: number;
  owner_user_id: string | null;
  sponsor_user_id: string | null;
  identity_id: string | null;
  identity_active: boolean;
  identity_expires_at: string | null;
  identity_revoked_at: string | null;
  tools: string[];
  capabilities: string[];
  max_concurrency: number;
  budget_policy: Record<string, unknown>;
  total_cost_usd: number;
  last_run_at: string | null;
}

interface Proposal {
  id: string;
  title: string;
  rationale: string;
  requested_name: string;
  requester_user_id: string;
  sponsor_user_id: string;
  risk_tier: number;
  status: string;
  provisioned_agent_instance_id: string | null;
  created_at: string;
  updated_at: string;
}

async function loadRegistry() {
  const response = await api.get<RegistryItem[]>("/agent-governance/workforce-registry");
  return response.data;
}

async function loadProposals() {
  const response = await api.get<Proposal[]>("/agent-workforce/proposals");
  return response.data;
}

export default function GovernancePage() {
  const { user } = useAuthStore();
  const [registry, setRegistry] = useState<RegistryItem[]>([]);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ title: "", rationale: "", requested_name: "", sponsor_user_id: "", risk_tier: "0" });

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const [workforce, proposalItems] = await Promise.all([loadRegistry(), loadProposals()]);
      setRegistry(workforce);
      setProposals(proposalItems);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void refresh(); }, []);

  async function action(path: string, key: string, body?: object) {
    setBusy(key);
    setError(null);
    try {
      await api.post(path, body);
      await refresh();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  async function createProposal(event: React.FormEvent) {
    event.preventDefault();
    await action("/agent-workforce/proposals", "create", {
      ...form,
      risk_tier: Number(form.risk_tier),
      sponsor_user_id: form.sponsor_user_id.trim(),
    });
    setShowCreate(false);
    setForm({ title: "", rationale: "", requested_name: "", sponsor_user_id: "", risk_tier: "0" });
  }

  const status = (value: string) => <Badge status={value.toLowerCase().includes("approved") || value === "ENABLED" || value === "approved" ? "active" : value.toLowerCase().includes("rejected") || value === "REVOKED" ? "inactive" : "pending"}>{value.replaceAll("_", " ")}</Badge>;

  return (
    <>
      <Header
        title="Workforce Governance"
        description="Governed AI workforce, identity controls, evaluations, and approval lifecycle"
        actions={<div className="flex gap-2"><Button size="sm" variant="outline" onClick={() => void refresh()} disabled={loading}><RefreshCw className="h-4 w-4" />Refresh</Button><Button size="sm" onClick={() => setShowCreate((value) => !value)}><Plus className="h-4 w-4" />New proposal</Button></div>}
      />
      <div className="space-y-6 p-6">
        {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

        {showCreate && <form onSubmit={createProposal} className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center gap-2"><ShieldCheck className="h-5 w-5 text-brand-600" /><h2 className="font-semibold">Submit workforce proposal</h2></div>
          <div className="grid gap-4 md:grid-cols-2">
            <input required placeholder="Proposal title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="rounded-lg border px-3 py-2 text-sm" />
            <input required placeholder="Requested agent name" value={form.requested_name} onChange={(e) => setForm({ ...form, requested_name: e.target.value })} className="rounded-lg border px-3 py-2 text-sm" />
            <input required placeholder="Sponsor user UUID" value={form.sponsor_user_id} onChange={(e) => setForm({ ...form, sponsor_user_id: e.target.value })} className="rounded-lg border px-3 py-2 text-sm" />
            <select value={form.risk_tier} onChange={(e) => setForm({ ...form, risk_tier: e.target.value })} className="rounded-lg border px-3 py-2 text-sm"><option value="0">Risk tier 0</option><option value="1">Risk tier 1</option><option value="2">Risk tier 2</option><option value="3">Risk tier 3</option><option value="4">Risk tier 4</option></select>
            <textarea required placeholder="Rationale" value={form.rationale} onChange={(e) => setForm({ ...form, rationale: e.target.value })} className="min-h-24 rounded-lg border px-3 py-2 text-sm md:col-span-2" />
          </div>
          <div className="mt-4 flex justify-end gap-2"><Button type="button" variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button><Button type="submit" disabled={busy === "create"}>{busy === "create" ? "Submitting…" : "Submit proposal"}</Button></div>
          {user?.id && <p className="mt-2 text-xs text-gray-400">Requester: {user.id}</p>}
        </form>}

        <section>
          <div className="mb-3 flex items-center justify-between"><div><h2 className="text-lg font-semibold text-gray-900">Workforce Registry</h2><p className="text-sm text-gray-500">Tenant-scoped projection of AgentDefinition → AgentTemplate → AgentInstance.</p></div><span className="text-sm text-gray-500">{registry.length} agents</span></div>
          {loading ? <Spinner /> : registry.length === 0 ? <div className="rounded-xl border border-dashed border-gray-300 bg-white p-8 text-center text-sm text-gray-500">No governed Agent instances yet.</div> : <div className="grid gap-4 lg:grid-cols-2">{registry.map((item) => <article key={item.agent_instance_id} className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <div className="flex items-start justify-between gap-3"><div><h3 className="font-semibold text-gray-900">{item.name}</h3><p className="mt-1 text-xs text-gray-500">{item.definition.name} · v{item.definition.version}</p></div>{status(item.status)}</div>
            <div className="mt-4 grid grid-cols-2 gap-3 text-sm"><div><p className="text-xs text-gray-400">Risk</p><p>Tier {item.risk_tier}</p></div><div><p className="text-xs text-gray-400">Identity</p><p>{item.identity_active ? "Active" : "Not active"}</p></div><div><p className="text-xs text-gray-400">Attributed cost</p><p>${item.total_cost_usd.toFixed(4)}</p></div><div><p className="text-xs text-gray-400">Concurrency</p><p>{item.max_concurrency}</p></div></div>
            <div className="mt-4"><p className="mb-1 text-xs text-gray-400">Tools</p><div className="flex flex-wrap gap-1">{item.tools.length ? item.tools.map((tool) => <span key={tool} className="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600">{tool}</span>) : <span className="text-xs text-gray-400">None</span>}</div></div>
            {item.identity_id && <Button size="sm" variant="outline" className="mt-4" onClick={() => void action(`/agent-governance/identities/${item.identity_id}/access-review`, `review-${item.identity_id}`, { decision: "approved" })} disabled={busy === `review-${item.identity_id}`}><UserCheck className="h-4 w-4" />{busy === `review-${item.identity_id}` ? "Reviewing…" : "Approve access"}</Button>}
          </article>)}</div>}
        </section>

        <section>
          <div className="mb-3 flex items-center justify-between"><div><h2 className="text-lg font-semibold text-gray-900">Proposal Queue</h2><p className="text-sm text-gray-500">Controlled lifecycle: Board Review → CEO Approval → Provision → Access Review → Activate.</p></div><span className="text-sm text-gray-500">{proposals.length} proposals</span></div>
          <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm"><table className="min-w-full text-sm"><thead className="border-b bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-500"><tr><th className="px-4 py-3">Proposal</th><th className="px-4 py-3">Risk</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Actions</th></tr></thead><tbody className="divide-y">{proposals.map((item) => <tr key={item.id}><td className="px-4 py-3"><div className="font-medium">{item.title}</div><div className="text-xs text-gray-400">{item.requested_name}</div></td><td className="px-4 py-3">Tier {item.risk_tier}</td><td className="px-4 py-3">{status(item.status)}</td><td className="px-4 py-3"><div className="flex flex-wrap gap-2">
            {item.status === "SUBMITTED" && <><Button size="sm" variant="outline" onClick={() => void action(`/agent-workforce/proposals/${item.id}/board-decision`, `board-${item.id}`, { approve: true })} disabled={!!busy}><CheckCircle2 className="h-4 w-4" />Board approve</Button><Button size="sm" variant="outline" onClick={() => void action(`/agent-workforce/proposals/${item.id}/board-decision`, `board-reject-${item.id}`, { approve: false, reason: "Rejected from Governance UI" })} disabled={!!busy}><XCircle className="h-4 w-4" />Reject</Button></>}
            {item.status === "BOARD_APPROVED" && <Button size="sm" onClick={() => void action(`/agent-workforce/proposals/${item.id}/ceo-decision`, `ceo-${item.id}`, { approve: true })} disabled={!!busy}><CheckCircle2 className="h-4 w-4" />CEO approve</Button>}
            {item.status === "CEO_APPROVED" && <Button size="sm" onClick={() => void action(`/agent-workforce/proposals/${item.id}/provision`, `provision-${item.id}`)} disabled={!!busy}><Play className="h-4 w-4" />Provision</Button>}
            {item.status === "PROVISIONED" && item.provisioned_agent_instance_id && <Button size="sm" variant="outline" onClick={() => void action(`/agent-workforce/proposals/${item.id}/activate`, `activate-${item.id}`)} disabled={!!busy}><Play className="h-4 w-4" />Activate</Button>}
          </div></td></tr>)}{!loading && proposals.length === 0 && <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-500">No workforce proposals.</td></tr>}</tbody></table></div>
        </section>
      </div>
    </>
  );
}
