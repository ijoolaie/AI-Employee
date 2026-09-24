"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getErrorMessage, listTenantRoles, listTenantUsers, updateTenantUserRoles, updateTenantUserStatus } from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";
import { resellerMessages } from "@/lib/i18n/reseller";

export default function ResellerTeamPage() {
  const { locale } = useI18n();
  const m = resellerMessages[locale];
  const qc = useQueryClient();
  const users = useQuery({ queryKey: ["reseller-team-users"], queryFn: listTenantUsers });
  const roles = useQuery({ queryKey: ["reseller-team-roles"], queryFn: listTenantRoles });
  const status = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) => updateTenantUserStatus(id, is_active),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reseller-team-users"] }),
  });
  const roleUpdate = useMutation({
    mutationFn: ({ id, roleIds }: { id: string; roleIds: string[] }) => updateTenantUserRoles(id, roleIds),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reseller-team-users"] }),
  });

  return <>
    <Header title={m.teamTitle} description={m.teamDescription} />
    <div className="p-6"><Card><CardHeader><CardTitle>{m.serviceTeam}</CardTitle></CardHeader><CardContent className="overflow-x-auto p-0">
      {users.isLoading ? <p className="p-6 text-sm text-gray-500">{m.teamLoading}</p> :
       users.isError ? <p className="p-6 text-sm text-red-600">{getErrorMessage(users.error)}</p> :
       <table className="w-full text-start text-sm"><thead><tr className="border-b bg-gray-50 text-xs uppercase text-gray-500">
         <th className="px-5 py-3 text-start">{m.humanEmployees}</th><th className="px-5 py-3 text-start">{m.roles}</th><th className="px-5 py-3 text-start">{m.status}</th><th className="px-5 py-3 text-end">{m.action}</th>
       </tr></thead><tbody>{(users.data ?? []).map(u => <tr key={u.id} className="border-b border-gray-50">
         <td className="px-5 py-4"><p className="font-medium">{u.full_name || u.email}</p><p className="text-xs text-gray-500">{u.email}</p></td>
         <td className="px-5 py-4"><select aria-label={m.roles} multiple value={u.roles.map(name => roles.data?.find(r => r.name === name)?.id).filter((id): id is string => Boolean(id))} disabled={roleUpdate.isPending || roles.isLoading} onChange={e => roleUpdate.mutate({ id: u.id, roleIds: Array.from(e.target.selectedOptions, option => option.value) })} className="min-w-48 rounded-lg border px-2 py-1.5 text-xs">{(roles.data ?? []).map(r => <option key={r.id} value={r.id}>{r.name}</option>)}</select></td>
         <td className="px-5 py-4">{u.is_active ? m.active : m.disabled}</td>
         <td className="px-5 py-4 text-end"><button disabled={status.isPending} onClick={() => status.mutate({ id: u.id, is_active: !u.is_active })} className="rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium hover:bg-gray-50 disabled:opacity-50">{u.is_active ? m.suspend : m.activate}</button></td>
       </tr>)}</tbody></table>}
    </CardContent></Card></div>
  </>;
}
