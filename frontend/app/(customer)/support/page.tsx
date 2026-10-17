"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { LifeBuoy, MessageSquareText, Send } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  createCustomerSupportEscalation,
  createCustomerSupportEscalationMessage,
  getErrorMessage,
  listCustomerSupportEscalations,
  listCustomerSupportEscalationMessages,
} from "@/lib/api";
import type { SupportEscalation } from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";

export default function CustomerSupportPage() {
  const { locale } = useI18n();
  const fa = locale === "fa";
  const qc = useQueryClient();
  const m = fa ? {
    title: "پشتیبانی",
    description: "برای دریافت کمک از پشتیبانی ارائه‌دهنده سرویس تیکت ثبت کنید و پاسخ‌ها را همین‌جا دنبال کنید.",
    create: "ثبت تیکت جدید", subject: "موضوع", subjectPlaceholder: "موضوع درخواست",
    descriptionLabel: "شرح درخواست", descriptionPlaceholder: "مشکل را با جزئیات لازم توضیح دهید",
    submit: "ثبت تیکت", submitting: "در حال ثبت…", tickets: "تیکت‌های من",
    empty: "هنوز تیکتی ثبت نکرده‌اید.", thread: "مکاتبات تیکت",
    choose: "برای مشاهده مکاتبات یک تیکت را انتخاب کنید.", reply: "پاسخ",
    replyPlaceholder: "پیام خود را بنویسید…", send: "ارسال پاسخ",
    loading: "در حال بارگذاری…", noMessages: "هنوز پاسخی ثبت نشده است.",
    error: "بارگذاری یا انجام عملیات ناموفق بود.", created: "تیکت ثبت شد.",
    sent: "پاسخ ارسال شد.", resolved: "این تیکت بسته شده است و فعلاً امکان پاسخ وجود ندارد.",
    status: "وضعیت",
  } : {
    title: "Support",
    description: "Create a ticket for your service provider's support team and follow replies here.",
    create: "Create a support ticket", subject: "Subject", subjectPlaceholder: "Request subject",
    descriptionLabel: "Description", descriptionPlaceholder: "Describe the issue and relevant context",
    submit: "Create ticket", submitting: "Creating…", tickets: "My support tickets",
    empty: "You have not created any support tickets yet.", thread: "Ticket thread",
    choose: "Select a ticket to view its messages.", reply: "Reply",
    replyPlaceholder: "Write your message…", send: "Send reply",
    loading: "Loading…", noMessages: "No replies yet.",
    error: "Could not load or complete the operation.", created: "Support ticket created.",
    sent: "Reply sent.", resolved: "This ticket is resolved and cannot currently receive replies.",
    status: "Status",
  };

  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [reply, setReply] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);
  const [feedbackError, setFeedbackError] = useState(false);

  const ticketsQuery = useQuery({
    queryKey: ["customer-support-escalations"],
    queryFn: listCustomerSupportEscalations,
  });
  const tickets: SupportEscalation[] = ticketsQuery.data ?? [];
  const selectedTicket = tickets.find((ticket) => ticket.id === selectedId) ?? tickets[0];

  const messagesQuery = useQuery({
    queryKey: ["customer-support-messages", selectedTicket?.id],
    queryFn: () => listCustomerSupportEscalationMessages(selectedTicket!.id),
    enabled: Boolean(selectedTicket?.id),
  });

  const createMutation = useMutation({
    mutationFn: () => createCustomerSupportEscalation({ subject: subject.trim(), description: description.trim() }),
    onSuccess: async (ticket) => {
      setSelectedId(ticket.id);
      setSubject("");
      setDescription("");
      setFeedback(m.created);
      setFeedbackError(false);
      await qc.invalidateQueries({ queryKey: ["customer-support-escalations"] });
    },
    onError: (error) => { setFeedback(getErrorMessage(error) || m.error); setFeedbackError(true); },
  });

  const replyMutation = useMutation({
    mutationFn: () => createCustomerSupportEscalationMessage(selectedTicket!.id, {
      body: reply.trim(),
      attachment_file_ids: [],
    }),
    onSuccess: async () => {
      setReply("");
      setFeedback(m.sent);
      setFeedbackError(false);
      await qc.invalidateQueries({ queryKey: ["customer-support-messages", selectedTicket?.id] });
    },
    onError: (error) => { setFeedback(getErrorMessage(error) || m.error); setFeedbackError(true); },
  });

  return (
    <div className="space-y-6 p-4 md:p-6">
      <div className="rounded-xl border bg-white p-5">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-primary/10 p-3"><LifeBuoy className="h-6 w-6 text-primary" /></div>
          <div><h1 className="text-xl font-semibold">{m.title}</h1><p className="mt-1 text-sm text-muted-foreground">{m.description}</p></div>
        </div>
      </div>
      <div className="grid gap-4 xl:grid-cols-[minmax(280px,0.8fr)_minmax(0,1.4fr)]">
        <div className="space-y-4">
          <Card>
            <CardHeader><CardTitle>{m.create}</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label htmlFor="customer-support-subject" className="mb-1 block text-sm font-medium">{m.subject}</label>
                <input id="customer-support-subject" value={subject} onChange={(event) => setSubject(event.target.value)} maxLength={255} placeholder={m.subjectPlaceholder} className="w-full rounded-md border px-3 py-2 text-sm" />
              </div>
              <div>
                <label htmlFor="customer-support-description" className="mb-1 block text-sm font-medium">{m.descriptionLabel}</label>
                <textarea id="customer-support-description" value={description} onChange={(event) => setDescription(event.target.value)} maxLength={10000} placeholder={m.descriptionPlaceholder} className="min-h-28 w-full rounded-md border px-3 py-2 text-sm" />
              </div>
              <Button disabled={createMutation.isPending || subject.trim().length < 3 || description.trim().length < 5} onClick={() => createMutation.mutate()}>
                {createMutation.isPending ? m.submitting : m.submit}
              </Button>
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>{m.tickets}</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              {ticketsQuery.isLoading && <p className="text-sm text-muted-foreground">{m.loading}</p>}
              {ticketsQuery.isError && <p role="alert" className="text-sm text-red-600">{m.error}</p>}
              {!ticketsQuery.isLoading && !ticketsQuery.isError && tickets.length === 0 && <p className="text-sm text-muted-foreground">{m.empty}</p>}
              {tickets.map((ticket) => (
                <button key={ticket.id} type="button" onClick={() => { setSelectedId(ticket.id); setFeedback(null); }} className={`w-full rounded-lg border p-3 text-start transition hover:bg-muted/50 ${selectedTicket?.id === ticket.id ? "border-primary bg-muted/40" : "border-border"}`}>
                  <span className="block font-medium">{ticket.subject}</span>
                  <span className="mt-1 flex items-center justify-between gap-2 text-xs text-muted-foreground"><span>{ticket.id.slice(0, 8)}</span><Badge status={ticket.status} /></span>
                </button>
              ))}
            </CardContent>
          </Card>
        </div>
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><MessageSquareText className="h-5 w-5" />{m.thread}</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {feedback && <p role={feedbackError ? "alert" : "status"} className={feedbackError ? "text-sm text-red-600" : "text-sm text-green-700"}>{feedback}</p>}
            {!selectedTicket && <p className="text-sm text-muted-foreground">{m.choose}</p>}
            {selectedTicket && <>
              <div className="rounded-lg bg-muted/40 p-3"><p className="font-medium">{selectedTicket.subject}</p><p className="mt-1 whitespace-pre-wrap text-sm text-muted-foreground">{selectedTicket.description}</p><div className="mt-2"><Badge status={selectedTicket.status} /></div></div>
              {messagesQuery.isLoading && <p className="text-sm text-muted-foreground">{m.loading}</p>}
              {messagesQuery.isError && <p role="alert" className="text-sm text-red-600">{m.error}</p>}
              {!messagesQuery.isLoading && !messagesQuery.isError && (messagesQuery.data ?? []).length === 0 && <p className="text-sm text-muted-foreground">{m.noMessages}</p>}
              <div className="max-h-[420px] space-y-3 overflow-y-auto">
                {(messagesQuery.data ?? []).map((message) => <article key={message.id} className="rounded-lg border p-3"><p className="whitespace-pre-wrap text-sm">{message.body}</p><p className="mt-2 text-xs text-muted-foreground">{new Intl.DateTimeFormat(fa ? "fa-IR" : undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(message.created_at))}</p></article>)}
              </div>
              {selectedTicket.status === "resolved" ? <p className="rounded-md bg-muted/50 p-3 text-sm text-muted-foreground">{m.resolved}</p> : <div className="space-y-3 border-t pt-4">
                <label htmlFor="customer-support-reply" className="block text-sm font-medium">{m.reply}</label>
                <textarea id="customer-support-reply" value={reply} onChange={(event) => setReply(event.target.value)} maxLength={10000} placeholder={m.replyPlaceholder} className="min-h-24 w-full rounded-md border px-3 py-2 text-sm" />
                <Button disabled={replyMutation.isPending || reply.trim().length === 0} onClick={() => replyMutation.mutate()}><Send className="h-4 w-4" />{replyMutation.isPending ? m.submitting : m.send}</Button>
              </div>}
            </>}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
