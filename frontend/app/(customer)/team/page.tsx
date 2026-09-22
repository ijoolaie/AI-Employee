"use client";

import { useState } from "react";
import { useMutation,useQuery,useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card,CardContent,CardHeader,CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage,listTenantRoles,listTenantUsers,updateTenantUserRoles,updateTenantUserStatus } from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";
import { Users } from "lucide-react";

function isPermissionError(error:unknown){const message=getErrorMessage(error).toLowerCase();return message.includes("permission")||message.includes("403")||message.includes("forbidden")||message.includes("administrator access");}
export default function TeamPage(){
  const {t}=useI18n();const m=t.team;const qc=useQueryClient();const [msg,setMsg]=useState<string|null>(null);
  const users=useQuery({queryKey:["tenant-users"],queryFn:listTenantUsers});const roles=useQuery({queryKey:["tenant-roles"],queryFn:listTenantRoles});
  const status=useMutation({mutationFn:({id,v}:{id:string;v:boolean})=>updateTenantUserStatus(id,v),onSuccess:()=>{setMsg(m.statusUpdated);void qc.invalidateQueries({queryKey:["tenant-users"]});},onError:e=>setMsg(isPermissionError(e)?m.permissionDenied:getErrorMessage(e)||m.updateError)});
  const role=useMutation({mutationFn:({id,ids}:{id:string;ids:string[]})=>updateTenantUserRoles(id,ids),onSuccess:()=>{setMsg(m.rolesUpdated);void qc.invalidateQueries({queryKey:["tenant-users"]});},onError:e=>setMsg(isPermissionError(e)?m.permissionDenied:getErrorMessage(e)||m.updateError)});
  const retry=()=>{void users.refetch();void roles.refetch();};
  const loadError=users.error||roles.error;
  return <><Header title={m.title} description={m.description}/><div className="space-y-6 p-6">
    {(users.isLoading||roles.isLoading)&&<div className="flex justify-center py-8" aria-label={m.loading}><Spinner/></div>}
    {loadError&&<div role="alert" className="space-y-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700"><p>{isPermissionError(loadError)?m.permissionDenied:m.loadError}</p><Button variant="secondary" onClick={retry}>{m.retry}</Button></div>}
    {msg&&<div role="status" className="rounded-lg border border-gray-200 bg-white px-4 py-3 text-sm text-gray-700">{msg}</div>}
    {!loadError&&!users.isLoading&&(users.data??[]).length===0&&<EmptyState icon={Users} title={m.emptyTitle} description={m.emptyDescription}/>}
    {!loadError&&!users.isLoading&&(users.data??[]).length>0&&<Card><CardHeader><CardTitle>{m.users}</CardTitle></CardHeader><CardContent className="p-0 overflow-x-auto"><table className="w-full min-w-[760px] text-start text-sm"><thead><tr className="border-b text-xs uppercase text-gray-500"><th className="px-4 py-3 text-start">{m.user}</th><th className="px-4 py-3 text-start">{m.status}</th><th className="px-4 py-3 text-start">{m.roles}</th><th className="px-4 py-3 text-end">{m.actions}</th></tr></thead><tbody>
      {(users.data??[]).map(u=><tr key={u.id} className="border-b border-gray-50"><td className="px-4 py-3"><p className="font-medium">{u.full_name||u.email}</p><p className="text-xs text-gray-500">{u.email}</p></td><td className="px-4 py-3">{u.is_active?m.active:m.disabled}</td><td className="px-4 py-3"><select multiple aria-label={m.roleSelector} className="min-w-48 rounded border px-2 py-1 text-xs text-start" value={(roles.data??[]).filter(r=>u.roles.includes(r.name)).map(r=>r.id)} onChange={e=>role.mutate({id:u.id,ids:Array.from(e.target.selectedOptions).map(o=>o.value)})}>{(roles.data??[]).map(r=><option key={r.id} value={r.id}>{r.name}</option>)}</select><div className="text-xs text-gray-500">{m.currentRoles}: {u.roles.join(", ")||m.none}</div></td><td className="px-4 py-3 text-end"><Button size="sm" variant="outline" loading={status.isPending} disabled={status.isPending||role.isPending} onClick={()=>status.mutate({id:u.id,v:!u.is_active})}>{u.is_active?m.disable:m.enable}</Button></td></tr>)}
    </tbody></table></CardContent></Card>}
    <p className="text-xs text-gray-400">{m.invitationNote}</p>
  </div></>;
}
