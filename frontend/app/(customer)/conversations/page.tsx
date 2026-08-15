"use client";

import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { listCustomerConversations, getErrorMessage } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { MessageCircle } from "lucide-react";

export default function ConversationsPage() {
  const q = useQuery({ queryKey: ["customer-conversations"], queryFn: () => listCustomerConversations() });
  return <>
    <Header title="Customer Conversations" description="See how your customers are talking to your AI Employees." />
    <div className="p-6"><Card><CardHeader><CardTitle>Recent customer conversations</CardTitle></CardHeader><CardContent className="p-0">
      {q.isLoading && <div className="p-6"><Spinner /></div>}
      {q.error && <p className="p-6 text-sm text-red-600">{getErrorMessage(q.error)}</p>}
      {!q.isLoading && !q.error && (q.data ?? []).length === 0 && <div className="flex flex-col items-center gap-2 p-12 text-center"><MessageCircle className="h-8 w-8 text-gray-300" /><p className="text-sm font-medium text-gray-700">No customer conversations yet</p><p className="text-xs text-gray-500">Publish an Employee to a customer channel and share its chat link.</p></div>}
      {(q.data ?? []).length > 0 && <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr className="border-b text-xs uppercase text-gray-500"><th className="px-5 py-3">Customer</th><th className="px-5 py-3">Messages</th><th className="px-5 py-3">Last message</th><th className="px-5 py-3">Updated</th></tr></thead><tbody>{q.data!.map((c) => <tr key={c.id} className="border-b border-gray-50"><td className="px-5 py-3"><div className="font-medium">{c.customer_name || "Anonymous customer"}</div><div className="text-xs text-gray-400">{c.customer_email || c.customer_phone || c.id.slice(0, 8)}</div></td><td className="px-5 py-3">{c.message_count}</td><td className="max-w-md truncate px-5 py-3 text-gray-600">{c.last_message || "—"}</td><td className="px-5 py-3 text-gray-500">{formatDate(c.updated_at)}</td></tr>)}</tbody></table></div>}
    </CardContent></Card></div>
  </>;
}
