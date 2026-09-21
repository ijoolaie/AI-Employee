"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage, listInboxConversations, setConversationHandoff, getInboxMessages, sendInboxMessage } from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";
import { formatDate } from "@/lib/utils";
import { MessageCircle, UserRound, Send } from "lucide-react";

function isPermissionError(error: unknown) {
  const message = getErrorMessage(error).toLowerCase();
  return message.includes("permission") || message.includes("403") || message.includes("forbidden");
}

export default function InboxPage() {
  const { t } = useI18n();
  const m = t.inbox;
  const qc = useQueryClient();
  const [selected, setSelected] = useState<string | null>(null);
  const [text, setText] = useState("");

  const q = useQuery({ queryKey: ["inbox"], queryFn: listInboxConversations, refetchInterval: 10000 });
  const activeId = selected ?? q.data?.[0]?.id ?? null;
  const messages = useQuery({
    queryKey: ["inbox-messages", activeId],
    queryFn: () => getInboxMessages(activeId!),
    enabled: !!activeId,
    refetchInterval: 4000,
  });
  const handoff = useMutation({
    mutationFn: (x: { id: string; requested: boolean }) => setConversationHandoff(x.id, x.requested),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["inbox"] }),
  });
  const send = useMutation({
    mutationFn: () => sendInboxMessage(activeId!, text.trim()),
    onSuccess: () => {
      setText("");
      void messages.refetch();
      void qc.invalidateQueries({ queryKey: ["inbox"] });
    },
  });

  const active = q.data?.find((c) => c.id === activeId);
  const actionError = handoff.error ?? send.error;
  const busy = handoff.isPending || send.isPending;

  return (
    <>
      <Header title={m.title} description={m.description} />
      <div className="grid h-[calc(100vh-88px)] min-h-[620px] grid-cols-1 gap-4 p-4 lg:grid-cols-[360px_1fr]">
        <Card className="overflow-hidden">
          <CardHeader><CardTitle>{m.conversations}</CardTitle></CardHeader>
          <CardContent className="p-0">
            {q.isLoading ? <div className="p-8"><Spinner /></div> : q.isError ? (
              <div role="alert" className="p-6 text-sm">
                <p className={isPermissionError(q.error) ? "text-amber-700" : "text-red-600"}>{isPermissionError(q.error) ? m.permissionDenied : m.error}</p>
                <Button type="button" variant="outline" className="mt-3" onClick={() => void q.refetch()}>{m.retry}</Button>
              </div>
            ) : (q.data ?? []).length === 0 ? (
              <EmptyState title={m.emptyTitle} description={m.emptyDescription} />
            ) : (
              <div className="divide-y">
                {(q.data ?? []).map((c) => (
                  <button key={c.id} type="button" onClick={() => setSelected(c.id)} className={"w-full p-4 text-start hover:bg-slate-50 " + (activeId === c.id ? "bg-brand-50" : "")}>
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="font-medium">{c.customer_name || m.anonymous}</p>
                        <p className="mt-1 line-clamp-2 text-xs text-slate-500">{c.last_message || m.noMessages}</p>
                      </div>
                      {c.handoff_requested && <span className="rounded-full bg-amber-100 px-2 py-1 text-[10px] font-semibold text-amber-700">{m.human}</span>}
                    </div>
                    <p className="mt-2 text-[11px] text-slate-400">{c.message_count} {m.messagesCount} · {c.channel_id.slice(0, 8)}</p>
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="flex min-h-0 flex-col overflow-hidden">
          <CardHeader className="border-b">
            <div className="flex items-center justify-between gap-4">
              <div className="min-w-0">
                <CardTitle>{active?.customer_name || m.customerConversation}</CardTitle>
                <p className="mt-1 text-xs text-slate-500">{active?.customer_email || active?.customer_phone || m.anonymous}</p>
              </div>
              {active && (
                <Button size="sm" variant="outline" loading={handoff.isPending} onClick={() => handoff.mutate({ id: active.id, requested: !active.handoff_requested })}>
                  <UserRound className="me-1 h-4 w-4" />
                  {active.handoff_requested ? m.returnToAi : m.takeOver}
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="flex min-h-0 flex-1 flex-col p-0">
            {actionError && <div role="alert" className="border-b border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{getErrorMessage(actionError)}</div>}
            <div className="flex-1 space-y-3 overflow-y-auto p-5">
              {!activeId ? (
                <div className="flex h-full items-center justify-center"><EmptyState title={m.selectConversation} description={m.selectConversationDescription} /></div>
              ) : messages.isLoading ? (
                <div className="flex h-full items-center justify-center"><Spinner /></div>
              ) : messages.isError ? (
                <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
                  <MessageCircle className="h-8 w-8 text-slate-300" />
                  <p className="text-sm text-red-600">{isPermissionError(messages.error) ? m.permissionDenied : m.messageError}</p>
                  <Button type="button" variant="outline" onClick={() => void messages.refetch()}>{m.retry}</Button>
                </div>
              ) : (messages.data ?? []).length === 0 ? (
                <div className="flex h-full items-center justify-center"><EmptyState title={m.noMessagesTitle} description={m.noMessagesDescription} /></div>
              ) : (
                (messages.data ?? []).map((message) => (
                  <div key={message.id} className={"max-w-[78%] rounded-2xl px-4 py-3 text-sm " + (message.role === "user" ? "bg-slate-100 text-slate-800" : message.role === "human" ? "ms-auto bg-brand-600 text-white" : "bg-brand-50 text-slate-800")}>
                    <div className="mb-1 text-[10px] font-semibold uppercase opacity-60">{message.role}</div>
                    <p>{message.content}</p>
                    <div className="mt-2 text-[10px] opacity-60">{formatDate(message.created_at)}</div>
                  </div>
                ))
              )}
            </div>
            <div className="border-t p-4">
              <div className="flex gap-2">
                <Input
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey && text.trim() && activeId && !busy) {
                      e.preventDefault();
                      send.mutate();
                    }
                  }}
                  placeholder={active?.handoff_requested ? m.humanReply : m.takeOverToReply}
                  disabled={!activeId || busy}
                />
                <Button type="button" disabled={!activeId || !text.trim() || busy} loading={send.isPending} onClick={() => send.mutate()}>
                  <Send className="h-4 w-4" />{m.send}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
