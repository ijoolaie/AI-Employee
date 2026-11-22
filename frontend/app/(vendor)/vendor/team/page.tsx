"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api, getErrorMessage } from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";

interface Tenant { id: string; name: string; slug: string; tenant_kind: string; status: string }
interface ManagedUser { id: string; email: string; full_name: string | null; is_active: boolean; roles: string[] }
interface ManagedRole { id: string; name: string; description: string | null; permissions: string[] }
interface Invitation { id: string; user_id: string; email: string; token: string; expires_at: string }
interface ApiResponse<T> { success: boolean; data: T }

export default function VendorTeamPage() {
  const { locale } = useI18n();
  const qc = useQueryClient();
  const [tenantId, setTenantId] = useState("");
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [invitation, setInvitation] = useState<Invitation | null>(null);
  const [feedback, setFeedback] = useState("");
  const tenants = useQuery({ queryKey: ["vendor-license-targets"], queryFn: async () => { const r = await api.get<ApiResponse<Tenant[]>>("/edition/vendor/tenants"); if (!r.data.success) throw new Error("Unable to load managed tenants"); return r.data.data; } });
  const selectedTenant = tenants.data?.find((tenant) => tenant.id === tenantId);
  const base = `/edition/vendor/tenants/${tenantId}/users`;
  const users = useQuery({ queryKey: ["vendor-managed-users", tenantId], enabled: Boolean(tenantId), queryFn: async () => { const r = await api.get<ApiResponse<ManagedUser[]>>(base); if (!r.data.success) throw new Error("Unable to load users"); return r.data.data; } });
  const roles = useQuery({ queryKey: ["vendor-managed-roles", tenantId], enabled: Boolean(tenantId), queryFn: async () => { const r = await api.get<ApiResponse<ManagedRole[]>>(`${base}/roles`); if (!r.data.success) throw new Error("Unable to load assignable roles"); return r.data.data; } });
  const assignableRoles = useMemo(() => roles.data ?? [], [roles.data]);
  const invite = useMutation({
    mutationFn: async () => { const r = await api.post<ApiResponse<Invitation>>(`${base}/invitations`, { email: email.trim(), full_name: fullName.trim() || null, expires_in_days: 7 }); if (!r.data.success) throw new Error("Unable to create invitation"); return r.data.data; },
    onSuccess: async (data) => { setInvitation(data); setEmail(""); setFullName(""); setFeedback("Invitation created. The token is shown only once."); await qc.invalidateQueries({ queryKey: ["vendor-managed-users", tenantId] }); },
    onError: (error) => setFeedback(getErrorMessage(error)),
  });
  const setUserStatus = useMutation({
    mutationFn: async ({ userId, is_active }: { userId: string; is_active: boolean }) => { const r = await api.post<ApiResponse<ManagedUser>>(`${base}/${userId}/status`, { is_active }); if (!r.data.success) throw new Error("Unable to update user status"); return r.data.data; },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["vendor-managed-users", tenantId] }),
    onError: (error) => setFeedback(getErrorMessage(error)),
  });
  const setUserRoles = useMutation({
    mutationFn: async ({ userId, role_ids }: { userId: string; role_ids: string[] }) => { const r = await api.post<ApiResponse<ManagedUser>>(`${base}/${userId}/roles`, { role_ids }); if (!r.data.success) throw new Error("Unable to update user roles"); return r.data.data; },
    onSuccess: () => { setFeedback("User roles updated."); return qc.invalidateQueries({ queryKey: ["vendor-managed-users", tenantId] }); },
    onError: (error) => setFeedback(getErrorMessage(error)),
  });
  const canInvite = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());

  return <>
    <Header title={"Network team access"} description={"Manage users, invitations and assignable roles for tenants in your Vendor hierarchy."} />
    <main className="space-y-6 p-5 md:p-8">
      <Card><CardHeader><CardTitle>{"Select a managed tenant"}</CardTitle></CardHeader><CardContent>
        {tenants.isError && <p role="alert" className="mb-3 text-sm text-red-600">{getErrorMessage(tenants.error)}</p>}
        <label className="grid max-w-2xl gap-2 text-sm font-medium text-slate-700"><span>{"Reseller or direct customer"}</span><select value={tenantId} onChange={(event) => { setTenantId(event.target.value); setInvitation(null); setFeedback(""); }} disabled={tenants.isLoading} className="rounded-lg border border-slate-200 bg-white px-3 py-2.5"><option value="">{"Choose a tenant..."}</option>{(tenants.data ?? []).map((tenant) => <option key={tenant.id} value={tenant.id}>{tenant.name} · {tenant.tenant_kind} · {tenant.status}</option>)}</select></label>
        {!tenants.isLoading && tenants.data?.length === 0 && <p className="mt-3 text-sm text-slate-500">{"Create a reseller or direct customer before managing its team."}</p>}
      </CardContent></Card>

      {selectedTenant && <>
        <Card><CardHeader><CardTitle>{`Invite a user to ${selectedTenant.name}`}</CardTitle></CardHeader><CardContent>
          <p className="mb-4 text-sm text-slate-500">{"Users join through a one-time invitation. Platform administrator roles and Vendor control-plane permissions cannot be delegated."}</p>
          <div className="grid gap-3 md:grid-cols-3"><label className="grid gap-1 text-sm"><span>{"Email"}</span><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} className="rounded-lg border border-slate-200 px-3 py-2" /></label><label className="grid gap-1 text-sm"><span>{"Full name (optional)"}</span><input value={fullName} onChange={(event) => setFullName(event.target.value)} className="rounded-lg border border-slate-200 px-3 py-2" /></label><div className="flex items-end"><Button onClick={() => invite.mutate()} disabled={!canInvite || invite.isPending}>{invite.isPending ? ("Creating...") : ("Create invitation")}</Button></div></div>
          {invitation && <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm"><p className="font-semibold text-emerald-900">{`Invitation ready for ${invitation.email}`}</p><code className="mt-2 block break-all rounded-lg bg-white p-3 text-xs">{invitation.token}</code><p className="mt-2 text-xs text-emerald-800">{"Share this token securely. It will not be shown again."} · {new Date(invitation.expires_at).toLocaleString(locale === "fa" ? "fa-IR" : "en-US")}</p></div>}
        </CardContent></Card>

        <Card><CardHeader><CardTitle>{"Users and roles"}</CardTitle></CardHeader><CardContent className="overflow-x-auto p-0">
          {users.isLoading || roles.isLoading ? <p className="p-6 text-sm text-slate-500">{"Loading users and roles..."}</p> : users.isError || roles.isError ? <p role="alert" className="p-6 text-sm text-red-600">{getErrorMessage(users.error ?? roles.error)}</p> : users.data?.length === 0 ? <p className="p-8 text-center text-sm text-slate-500">{"No users found for this tenant."}</p> : <table className="w-full text-start text-sm"><thead><tr className="border-b bg-slate-50 text-xs uppercase text-slate-500"><th className="px-5 py-3 text-start">{"User"}</th><th className="px-5 py-3 text-start">{"Assignable roles"}</th><th className="px-5 py-3 text-start">{"Status"}</th><th className="px-5 py-3 text-end">{"Actions"}</th></tr></thead><tbody>{users.data?.map((user) => <tr key={user.id} className="border-b border-slate-100"><td className="px-5 py-4"><p className="font-medium text-slate-900">{user.full_name || user.email}</p><p className="text-xs text-slate-500">{user.email}</p></td><td className="px-5 py-4"><select aria-label={`Roles for ${user.email}`} multiple value={user.roles.map((name) => assignableRoles.find((role) => role.name === name)?.id).filter((id): id is string => Boolean(id))} disabled={setUserRoles.isPending} onChange={(event) => setUserRoles.mutate({ userId: user.id, role_ids: Array.from(event.target.selectedOptions, (option) => option.value) })} className="min-h-20 min-w-48 rounded-lg border border-slate-200 px-2 py-1.5 text-xs">{assignableRoles.map((role) => <option key={role.id} value={role.id}>{role.name}</option>)}</select><p className="mt-1 text-[11px] text-slate-400">{"Hold Ctrl/Cmd to select multiple roles."}</p></td><td className="px-5 py-4"><Badge status={user.is_active ? "active" : "inactive"}>{user.is_active ? ("Active") : ("Inactive")}</Badge></td><td className="px-5 py-4 text-end"><Button size="sm" variant="outline" disabled={setUserStatus.isPending} onClick={() => setUserStatus.mutate({ userId: user.id, is_active: !user.is_active })}>{user.is_active ? ("Suspend") : ("Activate")}</Button></td></tr>)}</tbody></table>}
        </CardContent></Card>
        {feedback && <p role="status" className="text-sm text-slate-600">{feedback}</p>}
      </>}
    </main>
  </>;
}
