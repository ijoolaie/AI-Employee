"use client";

import { useEffect, useState, type FormEvent } from "react";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { api, getErrorMessage } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { ShieldCheck, RefreshCw, Plus, UserCheck, ClipboardCheck } from "lucide-react";

interface RegistryItem {
  agent_instance_id: string; agent_definition_id: string; agent_template_id: string | null; name: string;
  definition: { slug: string; name: string; version: number; enabled: boolean };
  template: { slug: string; name: string; version: number; status: string } | null;
  status: string; enabled: boolean; risk_tier: number; owner_user_id: string | null; sponsor_user_id: string | null;
  identity_id: string | null; identity_active: boolean; identity_expires_at: string | null; identity_revoked_at: string | null;
  tools: string[]; capabilities: string[]; max_concurrency: number; budget_policy: Record<string, unknown>; total_cost_usd: number; last_run_at: string | null;
}
interface Proposal {
  id: string; title: string; rationale: string; requested_name: string; requester_user_id: string; sponsor_user_id: string;
  risk_tier: number; status: string; provisioned_agent_instance_id: string | null; created_at: string; updated_at: string;
}
interface AgentEvaluation {
  id: string; tenant_id: string; agent_template_id: string; suite_id: string; status: string; score: number | null;
  evidence: Record<string, unknown>; evidence_hash: string | null; evaluator_user_id: string | null; notes: string | null; created_at: string;
}
const PERMISSIONS = {
  read: "agent_template.read", evaluate: "agent_template.evaluate", lifecycle: "agent_instance.lifecycle",
  propose: "agent_workforce.propose", board: "agent_workforce.board_review", ceo: "agent_workforce.ceo_approve",
  provision: "agent_workforce.provision", activate: "agent_workforce.activate",
} as const;

async function loadRegistry() { return (await api.get<RegistryItem[]>("/agent-governance/workforce-registry")).data; }
async function loadProposals() { return (await api.get<Proposal[]>("/agent-workforce/proposals")).data; }
async function loadEvaluations(id: string) { return (await api.get<AgentEvaluation[]>(`/agent-governance/templates/${id}/evaluations`)).data; }

export default function GovernancePage() {
  const { user } = useAuthStore();
  const permissions = new Set((user as (typeof user & { permissions?: string[] }) | null)?.permissions ?? []);
  const can = (permission: string) => Boolean(user?.is_platform_admin || permissions.has("*") || permissions.has(permission));
  const [registry, setRegistry] = useState<RegistryItem[]>([]);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [evaluations, setEvaluations] = useState<Record<string, AgentEvaluation[]>>({});
  const [loading, setLoading] = useState(true); const [busy, setBusy] = useState<string | null>(null); const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false); const [showEvaluate, setShowEvaluate] = useState<string | null>(null);
  const [form, setForm] = useState({ title: "", rationale: "", requested_name: "", sponsor_user_id: "", risk_tier: "0" });
  const [evaluationForm, setEvaluationForm] = useState({ suite_id: "", status: "passed", score: "", evidence: "{}", notes: "" });

  async function refresh() {
    setLoading(true); setError(null);
    try {
      const [workforce, proposalItems] = await Promise.all([loadRegistry(), loadProposals()]);
      setRegistry(workforce); setProposals(proposalItems);
      if (can(PERMISSIONS.read)) {
        const entries = await Promise.all(workforce.filter((item) => item.agent_template_id).map(async (item) => {
          const id = item.agent_template_id as string;
          try { return [id, await loadEvaluations(id)] as const; } catch { return [id, []] as const; }
        }));
        setEvaluations(Object.fromEntries(entries));
      } else setEvaluations({});
    } catch (err) { setError(getErrorMessage(err)); } finally { setLoading(false); }
  }
  useEffect(() => { void refresh(); }, [user?.id]);

  async function action(path: string, key: string, body?: object) {
    setBusy(key); setError(null);
    try { await api.post(path, body); await refresh(); return true; }
    catch (err) { setError(getErrorMessage(err)); return false; }
    finally { setBusy(null); }
  }
  async function createProposal(event: FormEvent) {
    event.preventDefault();
    const ok = await action("/agent-workforce/proposals", "create", { ...form, risk_tier: Number(form.risk_tier), sponsor_user_id: form.sponsor_user_id.trim() });
    if (ok) { setShowCreate(false); setForm({ title: "", rationale: "", requested_name: "", sponsor_user_id: "", risk_tier: "0" }); }
  }
  async function createEvaluation(event: FormEvent, templateId: string) {
    event.preventDefault(); let evidence: Record<string, unknown>;
    try { evidence = JSON.parse(evaluationForm.evidence) as Record<string, unknown>; } catch { setError("Evaluation evidence must be valid JSON."); return; }
    const ok = await action(`/agent-governance/templates/${templateId}/evaluate`, `evaluate-${templateId}`, {
      suite_id: evaluationForm.suite_id.trim(), status: evaluationForm.status, score: evaluationForm.score === "" ? null : Number(evaluationForm.score), evidence, notes: evaluationForm.notes.trim() || null,
    });
    if (ok) { setShowEvaluate(null); setEvaluationForm({ suite_id: "", status: "passed", score: "", evidence: "{}", notes: "" }); }
  }
  const status = (value: string) => <Badge status={value.toLowerCase().includes("approved") || value === "ENABLED" || value === "approved" || value === "passed" ? "active" : value.toLowerCase().includes("rejected") || value === "REVOKED" || value === "failed" ? "inactive" : "pending"}>{value.replaceAll("_", " ")}</Badge>;

  return <>
    <Header title="Workforce Governance" description="Governed AI workforce, identity controls, evaluations, and approval lifecycle" actions={<div className="flex gap-2"><Button size="sm" variant="outline" onClick={() => void refresh()} disabled={loading}><RefreshCw className="h-4 w-4" />Refresh</Button>{can(PERMISSIONS.propose) && <Button size="sm" onClick={() => setShowCreate((v) => !v)}><Plus className="h-4 w-4" />New proposal</Button>}</div>} />
    <div className="space-y-6 p-6">
      {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
      {showCreate && can(PERMISSIONS.propose) && <form onSubmit={createProposal} className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm"><div className="mb-4 flex items-center gap-2"><ShieldCheck className="h-5 w-5" /><h2 className="font-semibold">Submit workforce proposal</h2></div><div className="grid gap-4 md:grid-cols-2"><input required placeholder="Proposal title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="rounded-lg border px-3 py-2 text-sm" /><input required placeholder="Requested agent name" value={form.requested_name} onChange={(e) => setForm({ ...form, requested_name: e.target.value })} className="rounded-lg border px-3 py-2 text-sm" /><input required placeholder="Sponsor user UUID" value={form.sponsor_user_id} onChange={(e) => setForm({ ...form, sponsor_user_id: e.target.value })} className="rounded-lg border px-3 py-2 text-sm" /><select value={form.risk_tier} onChange={(e) => setForm({ ...form, risk_tier: e.target.value })} className="rounded-lg border px-3 py-2 text-sm"><option value="0">Risk tier 0</option><option value="1">Risk tier 1</option><option value="2">Risk tier 2</option><option value="3">Risk tier 3</option><option value="4">Risk tier 4</option></select><textarea required placeholder="Rationale" value={form.rationale} onChange={(e) => setForm({ ...form, rationale: e.target.value })} className="min-h-24 rounded-lg border px-3 py-2 text-sm md:col-span-2" /></div><div className="mt-4 flex justify-end gap-2"><Button type="button" variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button><Button type="submit" disabled={busy === "create"}>{busy === "create" ? "Submitting…" : "Submit proposal"}</Button></div></form>}

      <section><div className="mb-3 flex items-center justify-between"><div><h2 className="text-lg font-semibold text-gray-900">Workforce Registry</h2><p className="text-sm text-gray-500">Tenant-scoped projection of AgentDefinition → AgentTemplate → AgentInstance.</p></div><span className="text-sm text-gray-500">{registry.length} agents</span></div>{loading ? <Spinner /> : registry.length === 0 ? <div className="rounded-xl border border-dashed border-gray-300 bg-white p-8 text-center text-sm text-gray-500">No governed Agent instances yet.</div> : <div className="grid gap-4 lg:grid-cols-2">{registry.map((item) => { const latest = item.agent_template_id ? evaluations[item.agent_template_id]?.[0] : undefined; return <article key={item.agent_instance_id} className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm"><div className="flex items-start justify-between gap-3"><div><h3 className="font-semibold text-gray-900">{item.name}</h3><p className="mt-1 text-xs text-gray-500">{item.definition.name} · v{item.definition.version}</p></div>{status(item.status)}</div><div className="mt-4 grid grid-cols-2 gap-3 text-sm"><div><p className="text-xs text-gray-400">Risk</p><p>Tier {item.risk_tier}</p></div><div><p className="text-xs text-gray-400">Identity</p><p>{item.identity_active ? "Active" : "Not active"}</p></div><div><p className="text-xs text-gray-400">Attributed cost</p><p>${item.total_cost_usd.toFixed(4)}</p></div><div><p className="text-xs text-gray-400">Concurrency</p><p>{item.max_concurrency}</p></div></div><div className="mt-4"><p className="mb-1 text-xs text-gray-400">Tools</p><div className="flex flex-wrap gap-1">{item.tools.length ? item.tools.map((tool) => <span key={tool} className="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600">{tool}</span>) : <span className="text-xs text-gray-400">None</span>}</div></div><div className="mt-4 rounded-lg border bg-gray-50 p-3"><div className="flex items-center justify-between"><div className="flex items-center gap-2"><ClipboardCheck className="h-4 w-4" /><span className="text-sm font-medium">Evaluation evidence</span></div>{latest ? status(latest.status) : <span className="text-xs text-gray-400">No evidence</span>}</div>{latest && <><div className="mt-2 grid grid-cols-2 gap-2 text-xs text-gray-600"><span>Suite: {latest.suite_id}</span><span>Score: {latest.score ?? "—"}</span><span>Hash: {latest.evidence_hash ? `${latest.evidence_hash.slice(0, 16)}…` : "—"}</span><span>{new Date(latest.created_at).toLocaleString()}</span></div>{latest.notes && <p className="mt-2 text-xs text-gray-500">{latest.notes}</p>}<details className="mt-2"><summary className="cursor-pointer text-xs text-gray-500">View evidence JSON</summary><pre className="mt-2 max-h-48 overflow-auto rounded bg-white p-2 text-[11px]">{JSON.stringify(latest.evidence, null, 2)}</pre></details></>}{can(PERMISSIONS.evaluate) && item.agent_template_id && <Button size="sm" variant="outline" className="mt-3" onClick={() => setShowEvaluate(showEvaluate === item.agent_template_id ? null : item.agent_template_id)}><ClipboardCheck className="h-4 w-4" />Record evaluation</Button>}{showEvaluate === item.agent_template_id && item.agent_template_id && <form onSubmit={(e) => void createEvaluation(e, item.agent_template_id as string)} className="mt-3 space-y-2 border-t pt-3"><input required placeholder="Evaluation suite ID" value={evaluationForm.suite_id} onChange={(e) => setEvaluationForm({ ...evaluationForm, suite_id: e.target.value })} className="w-full rounded border px-2 py-1.5 text-xs" /><div className="grid grid-cols-2 gap-2"><select value={evaluationForm.status} onChange={(e) => setEvaluationForm({ ...evaluationForm, status: e.target.value })} className="rounded border px-2 py-1.5 text-xs"><option value="passed">Passed</option><option value="failed">Failed</option><option value="blocked">Blocked</option></select><input type="number" min="0" max="100" placeholder="Score" value={evaluationForm.score} onChange={(e) => setEvaluationForm({ ...evaluationForm, score: e.target.value })} className="rounded border px-2 py-1.5 text-xs" /></div><textarea required value={evaluationForm.evidence} onChange={(e) => setEvaluationForm({ ...evaluationForm, evidence: e.target.value })} className="min-h-20 w-full rounded border px-2 py-1.5 font-mono text-xs" aria-label="Evaluation evidence JSON" /><textarea placeholder="Notes" value={evaluationForm.notes} onChange={(e) => setEvaluationForm({ ...evaluationForm, notes: e.target.value })} className="min-h-16 w-full rounded border px-2 py-1.5 text-xs" /><div className="flex justify-end gap-2"><Button type="button" size="sm" variant="outline" onClick={() => setShowEvaluate(null)}>Cancel</Button><Button type="submit" size="sm" disabled={busy === `evaluate-${item.agent_template_id}`}>{busy === `evaluate-${item.agent_template_id}` ? "Saving…" : "Save evidence"}</Button></div></form>}</div>{item.identity_id && can(PERMISSIONS.lifecycle) && <Button size="sm" variant="outline" className="mt-4" onClick={() => void action(`/agent-governance/identities/${item.identity_id}/access-review`, `review-${item.identity_id}`, { decision: "approved" })} disabled={busy === `review-${item.identity_id}`}><UserCheck className="h-4 w-4" />{busy === `review-${item.identity_id}` ? "Reviewing…" : "Approve access"}</Button>}</article>; })}</div>}</section>

      <section><div className="mb-3 flex items-center justify-between"><div><h2 className="text-lg font-semibold text-gray-900">Proposal Queue</h2><p className="text-sm text-gray-500">Requester → Board → CEO → Provision → Access Review → Activate.</p></div><span className="text-sm text-gray-500">{proposals.length} proposals</span></div>{proposals.length === 0 ? <div className="rounded-xl border border-dashed border-gray-300 bg-white p-8 text-center text-sm text-gray-500">No workforce proposals.</div> : <div className="space-y-3">{proposals.map((proposal) => { const identityId = proposal.provisioned_agent_instance_id ? registry.find((item) => item.agent_instance_id === proposal.provisioned_agent_instance_id)?.identity_id : null; return <article key={proposal.id} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm"><div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between"><div><div className="flex items-center gap-2"><h3 className="font-semibold">{proposal.title}</h3>{status(proposal.status)}</div><p className="mt-1 text-sm text-gray-600">{proposal.requested_name} · Risk tier {proposal.risk_tier}</p><p className="mt-1 text-xs text-gray-400">{proposal.rationale}</p></div><div className="flex flex-wrap gap-2">{proposal.status === "SUBMITTED" && can(PERMISSIONS.board) && <><Button size="sm" onClick={() => void action(`/agent-workforce/proposals/${proposal.id}/board-decision`, `board-${proposal.id}`, { approve: true })}>Board approve</Button><Button size="sm" variant="outline" onClick={() => void action(`/agent-workforce/proposals/${proposal.id}/board-decision`, `board-reject-${proposal.id}`, { approve: false })}>Reject</Button></>}{proposal.status === "BOARD_APPROVED" && can(PERMISSIONS.ceo) && <Button size="sm" onClick={() => void action(`/agent-workforce/proposals/${proposal.id}/ceo-decision`, `ceo-${proposal.id}`, { approve: true })}>CEO approve</Button>}{proposal.status === "CEO_APPROVED" && can(PERMISSIONS.provision) && <Button size="sm" onClick={() => void action(`/agent-workforce/proposals/${proposal.id}/provision`, `provision-${proposal.id}`)}>Provision</Button>}{proposal.status === "PROVISIONED" && identityId && can(PERMISSIONS.lifecycle) && <Button size="sm" variant="outline" onClick={() => void action(`/agent-governance/identities/${identityId}/access-review`, `proposal-review-${proposal.id}`, { decision: "approved" })}>Access review</Button>}{proposal.status === "PROVISIONED" && proposal.provisioned_agent_instance_id && can(PERMISSIONS.activate) && <Button size="sm" onClick={() => void action(`/agent-workforce/proposals/${proposal.id}/activate`, `activate-${proposal.id}`)}>Activate</Button>}</div></div></article>; })}</div>}</section>
    </div>
  </>;
}
