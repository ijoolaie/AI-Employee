"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { LifeBuoy, MessageSquareText, Send } from "lucide-react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api, getErrorMessage } from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";

interface Escalation {
  id: string;
  from_tenant_id: string;
  to_tenant_id: string;
  status: string;
  subject: string;
  description: string;
}
interface EscalationMessage {
  id: string;
  escalation_id: string;
  author_tenant_id: string;
  body: string;
  created_at: string;
  attachments: { id: string; filename: string; size_bytes: number }[];
}
interface ApiResponse<T> { success: boolean; data: T }

async function listEscalations() {
  const response = await api.get<ApiResponse<Escalation[]>>("/edition/vendor/support/escalations");
  if (!response.data.success) throw new Error("Unable to load support escalations");
  return response.data.data;
}
async function listMessages(id: string) {
  const response = await api.get<ApiResponse<EscalationMessage[]>>(`/edition/vendor/support/escalations/${id}/messages`);
  if (!response.data.success) throw new Error("Unable to load support conversation");
  return response.data.data;
}

export default function VendorSupportPage() {
  const { locale } = useI18n();
  const qc = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [reply, setReply] = useState("");
  const [feedback, setFeedback] = useState("");
  const tickets = useQuery({ queryKey: ["vendor-support-escalations"], queryFn: listEscalations });
  const selected = tickets.data?.find((ticket) => ticket.id === selectedId) ?? tickets.data?.[0];
  const messages = useQuery({ queryKey: ["vendor-support-messages", selected?.id], queryFn: () => listMessages(selected!.id), enabled: Boolean(selected?.id) });
  const send = useMutation({
    mutationFn: async () => {
      const response = await api.post<ApiResponse<EscalationMessage>>(`/edition/vendor/support/escalations/${selected!.id}/messages`, { body: reply.trim(), attachment_file_ids: [] });
      if (!response.data.success) throw new Error("Unable to send reply");
      return response.data.data;
    },
    onSuccess: async () => { setReply(""); setFeedback("Reply sent."); await qc.invalidateQueries({ queryKey: ["vendor-support-messages", selected?.id] }); },
    onError: (error) => setFeedback(getErrorMessage(error)),
  });
  const updateStatus = useMutation({
    mutationFn: async (status: "in_progress" | "resolved") => {
      const response = await api.patch<ApiResponse<Escalation>>(`/edition/vendor/support/escalations/${selected!.id}/status`, { status });
      if (!response.data.success) throw new Error("Unable to update escalation status");
      return response.data.data;
    },
    onSuccess: async () => { setFeedback("Escalation status updated."); await qc.invalidateQueries({ queryKey: ["vendor-support-escalations"] }); },
    onError: (error) => setFeedback(getErrorMessage(error)),
  });

  return <>
    <Header title={"Vendor support inbox"} description={"Review escalations from your reseller and customer network and respond to them."} />
    <main className="grid gap-5 p-5 lg:grid-cols-[minmax(280px,0.85fr)_minmax(0,1.5fr)] md:p-8">
      <Card className="min-h-[520px]">
        <CardHeader><CardTitle className="flex items-center gap-2"><LifeBuoy className="h-5 w-5" />{"Escalation queue"}</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          {tickets.isLoading && <p className="text-sm text-slate-500">{"Loading escalations..."}</p>}
          {tickets.isError && <p role="alert" className="text-sm text-red-600">{getErrorMessage(tickets.error)}</p>}
          {!tickets.isLoading && !tickets.isError && tickets.data?.length === 0 && <p className="rounded-lg bg-slate-50 p-5 text-sm text-slate-500">{"No support escalations have been assigned to this Vendor."}</p>}
          {tickets.data?.map((ticket) => <button key={ticket.id} onClick={() => { setSelectedId(ticket.id); setFeedback(""); }} className={`w-full rounded-xl border p-3 text-start transition ${selected?.id === ticket.id ? "border-brand-400 bg-brand-50" : "border-slate-200 hover:bg-slate-50"}`}>
            <span className="flex items-start justify-between gap-2"><span className="text-sm font-semibold text-slate-900">{ticket.subject}</span><Badge status={ticket.status}>{ticket.status.replace("_", " ")}</Badge></span>
            <span className="mt-2 line-clamp-2 block text-xs text-slate-500">{ticket.description}</span>
          </button>)}
        </CardContent>
      </Card>

      <Card className="min-h-[520px]">
        <CardHeader><CardTitle className="flex items-center gap-2"><MessageSquareText className="h-5 w-5" />{selected?.subject ?? ("Escalation conversation")}</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          {!selected && <p className="text-sm text-slate-500">{"Select an escalation to review its details and conversation."}</p>}
          {selected && <>
            <div className="rounded-xl bg-slate-50 p-4"><div className="mb-2 flex items-center justify-between gap-2"><span className="text-xs font-medium uppercase text-slate-500">{"Request description"}</span><Badge status={selected.status}>{selected.status.replace("_", " ")}</Badge></div><p className="whitespace-pre-wrap text-sm text-slate-700">{selected.description}</p></div>
            {selected.status !== "resolved" && <div className="flex flex-wrap gap-2"><Button size="sm" variant="outline" disabled={updateStatus.isPending || selected.status === "in_progress"} onClick={() => updateStatus.mutate("in_progress")}>{"Mark in progress"}</Button><Button size="sm" disabled={updateStatus.isPending} onClick={() => updateStatus.mutate("resolved")}>{"Resolve escalation"}</Button></div>}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-slate-800">{"Conversation"}</h3>
              {messages.isLoading && <p className="text-sm text-slate-500">{"Loading messages..."}</p>}
              {messages.isError && <p role="alert" className="text-sm text-red-600">{getErrorMessage(messages.error)}</p>}
              {messages.data?.length === 0 && <p className="text-sm text-slate-500">{"No messages yet."}</p>}
              {messages.data?.map((message) => <div key={message.id} className="rounded-xl border border-slate-200 p-3"><p className="whitespace-pre-wrap text-sm text-slate-700">{message.body}</p><p className="mt-2 text-[11px] text-slate-400">{new Date(message.created_at).toLocaleString(locale === "fa" ? "fa-IR" : "en-US")}</p>{message.attachments.length > 0 && <p className="mt-2 text-xs text-slate-500">{message.attachments.map((file) => file.filename).join("، ")}</p>}</div>)}
            </div>
            {selected.status !== "resolved" && <form onSubmit={(event) => { event.preventDefault(); if (reply.trim()) send.mutate(); }} className="space-y-2 border-t border-slate-100 pt-4"><label htmlFor="vendor-support-reply" className="text-sm font-medium text-slate-700">{"Reply"}</label><textarea id="vendor-support-reply" value={reply} onChange={(event) => setReply(event.target.value)} rows={3} maxLength={10000} className="w-full rounded-lg border border-slate-200 p-3 text-sm outline-none focus:border-brand-500" placeholder={"Write a reply..."} /><div className="flex items-center justify-between gap-3"><span role="status" className="text-xs text-slate-500">{feedback}</span><Button type="submit" size="sm" disabled={!reply.trim() || send.isPending}><Send className="me-2 h-4 w-4" />{send.isPending ? ("Sending...") : ("Send reply")}</Button></div></form>}
            {selected.status === "resolved" && <p className="text-sm text-slate-500">{"This escalation is resolved."}</p>}
            {feedback && selected.status !== "resolved" && <p role="status" className="text-xs text-slate-500">{feedback}</p>}
          </>}
        </CardContent>
      </Card>
    </main>
  </>;
}
