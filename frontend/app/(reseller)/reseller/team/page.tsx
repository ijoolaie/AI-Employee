"use client";

import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getErrorMessage, listTenantUsers } from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";
import { resellerMessages } from "@/lib/i18n/reseller";

export default function ResellerTeamPage() {
  const { locale } = useI18n();
  const m = resellerMessages[locale];
  const users = useQuery({ queryKey: ["reseller-team-users"], queryFn: listTenantUsers });
  return <>
    <Header title={m.teamTitle} description={m.teamDescription} />
    <div className="p-6"><Card><CardHeader><CardTitle>{m.serviceTeam}</CardTitle></CardHeader><CardContent className="overflow-x-auto p-0">
      {users.isLoading ? <p className="p-6 text-sm text-gray-500">{m.teamLoading}</p> : users.isError ? <p className="p-6 text-sm text-red-600">{getErrorMessage(users.error)}</p> : <table className="w-full text-start text-sm"><thead><tr className="border-b bg-gray-50 text-xs uppercase text-gray-500"><th className="px-5 py-3 text-start">{m.humanEmployees}</th><th className="px-5 py-3 text-start">{m.roles}</th><th className="px-5 py-3 text-start">{m.status}</th></tr></thead><tbody>{(users.data ?? []).map(u => <tr key={u.id} className="border-b border-gray-50"><td className="px-5 py-4"><p className="font-medium">{u.full_name || u.email}</p><p className="text-xs text-gray-500">{u.email}</p></td><td className="px-5 py-4 text-gray-600">{u.roles.join(", ") || m.noRole}</td><td className="px-5 py-4">{u.is_active ? m.active : m.disabled}</td></tr>)}</tbody></table>}
    </CardContent></Card></div>
  </>;
}
