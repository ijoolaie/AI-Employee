"use client";

import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getErrorMessage, listTenantUsers } from "@/lib/api";

export default function ResellerTeamPage() {
  const users = useQuery({ queryKey: ["reseller-team-users"], queryFn: listTenantUsers });
  return <>
    <Header title="Human Employees" description="People operating the reseller service desk and client success function." />
    <div className="p-6"><Card><CardHeader><CardTitle>Service team</CardTitle></CardHeader><CardContent className="p-0 overflow-x-auto">{users.isLoading ? <p className="p-6 text-sm text-gray-500">Loading…</p> : users.isError ? <p className="p-6 text-sm text-red-600">{getErrorMessage(users.error)}</p> : <table className="w-full text-left text-sm"><thead><tr className="border-b bg-gray-50 text-xs uppercase text-gray-500"><th className="px-5 py-3">Employee</th><th className="px-5 py-3">Roles</th><th className="px-5 py-3">Status</th></tr></thead><tbody>{(users.data ?? []).map(u => <tr key={u.id} className="border-b border-gray-50"><td className="px-5 py-4"><p className="font-medium">{u.full_name || u.email}</p><p className="text-xs text-gray-500">{u.email}</p></td><td className="px-5 py-4 text-gray-600">{u.roles.join(", ") || "No role"}</td><td className="px-5 py-4">{u.is_active ? "Active" : "Disabled"}</td></tr>)}</tbody></table>}</CardContent></Card></div>
  </>;
}
