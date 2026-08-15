"use client";

import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { getAuditLogs, getErrorMessage } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function LogsPage() {
  const q = useQuery({ queryKey: ["logs"], queryFn: () => getAuditLogs({ limit: 100 }), refetchInterval: 10000 });
  return <><Header title="Logs" description="Tenant-scoped audit and operational events" /><div className="p-6"><Card><CardHeader><CardTitle>Recent events</CardTitle></CardHeader><CardContent>{q.isLoading ? <Spinner/> : q.error ? <p className="text-sm text-red-600">{getErrorMessage(q.error)}</p> : <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr className="border-b text-xs uppercase text-gray-500"><th className="p-3">Time</th><th className="p-3">Action</th><th className="p-3">Status</th><th className="p-3">Request</th></tr></thead><tbody>{(q.data ?? []).map(l=><tr key={l.id} className="border-b last:border-0"><td className="p-3 text-gray-500">{formatDate(l.created_at)}</td><td className="p-3 font-medium">{l.action}</td><td className="p-3"><Badge status={l.status}/></td><td className="p-3 font-mono text-xs text-gray-500">{l.request_id ? `${l.request_id.slice(0,16)}…` : "—"}</td></tr>)}</tbody></table></div>}</CardContent></Card></div></>;
}
