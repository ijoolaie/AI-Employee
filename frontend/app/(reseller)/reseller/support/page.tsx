"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { LifeBuoy, Paperclip, Send, MessageSquareText, Download } from "lucide-react";
import { ResellerSurface } from "@/components/reseller/reseller-surface";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  createResellerSupportEscalation,
  createResellerSupportEscalationMessage,
  downloadResellerSupportAttachment,
  getErrorMessage,
  listFiles,
  listResellerSupportEscalations,
  listResellerSentSupportEscalations,
  listResellerSupportEscalationMessages,
  type SupportEscalation,
} from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";

export default function ResellerSupportPage() {
  const { locale } = useI18n();
  const fa = locale === "fa";
  const qc = useQueryClient();
  const m = fa
    ? {
        title: "مرکز پشتیبانی مشتری",
        description: "ارجاع مسئله به پشتیبانی پلتفرم و پیگیری مکاتبات در همان تیکت.",
        form: "ارجاع به پشتیبانی پلتفرم",
        subject: "موضوع",
        subjectPlaceholder: "موضوع مسئله",
        descriptionLabel: "شرح",
        descriptionPlaceholder: "شرح مسئله و زمینه لازم برای بررسی",
        submit: "ثبت ارجاع",
        submitting: "در حال ثبت…",
        created: "ارجاع با موفقیت ثبت شد.",
        error: "عملیات انجام نشد.",
        tickets: "تیکت‌های پشتیبانی",
        emptyTickets: "هنوز تیکت پشتیبانی وجود ندارد.",
        thread: "گفت‌وگو",
        chooseTicket: "برای مشاهده گفت‌وگو یک تیکت انتخاب کنید.",
        reply: "پاسخ شما",
        replyPlaceholder: "پیام خود را بنویسید…",
        send: "ارسال پیام",
        sending: "در حال ارسال…",
        files: "پیوست از فایل‌های موجود",
        noFiles: "فایل فعالی در فضای فایل شما وجود ندارد.",
        maxFiles: "حداکثر ۵ فایل برای هر پیام قابل انتخاب است.",
        noMessages: "هنوز پیامی ثبت نشده است.",
        attachment: "پیوست",
        loading: "در حال بارگذاری…",
        status: "وضعیت",
        loadError: "بارگذاری اطلاعات پشتیبانی ناموفق بود.",
      }
    : {
        title: "Client Support",
        description: "Escalate an issue to platform support and continue the conversation in its ticket.",
        form: "Escalate to Platform Support",
        subject: "Subject",
        subjectPlaceholder: "Issue subject",
        descriptionLabel: "Description",
        descriptionPlaceholder: "Describe the issue and relevant context",
        submit: "Create escalation",
        submitting: "Creating…",
        created: "Escalation created successfully.",
        error: "The operation could not be completed.",
        tickets: "Support tickets",
        emptyTickets: "There are no support tickets yet.",
        thread: "Conversation",
        chooseTicket: "Select a ticket to view its conversation.",
        reply: "Your reply",
        replyPlaceholder: "Write a message…",
        send: "Send message",
        sending: "Sending…",
        files: "Attach existing files",
        noFiles: "No active files are available in your file space.",
        maxFiles: "Choose up to five files per message.",
        noMessages: "No messages yet.",
        attachment: "Attachment",
        loading: "Loading…",
        status: "Status",
        loadError: "Could not load support data.",
      };

  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [createdTickets, setCreatedTickets] = useState<SupportEscalation[]>([]);
  const [reply, setReply] = useState("");
  const [selectedFileIds, setSelectedFileIds] = useState<string[]>([]);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [feedbackIsError, setFeedbackIsError] = useState(false);

  const ticketsQuery = useQuery({
    queryKey: ["reseller-support-escalations"],
    queryFn: listResellerSupportEscalations,
  });
  const sentTicketsQuery = useQuery({
    queryKey: ["reseller-support-escalations-sent"],
    queryFn: listResellerSentSupportEscalations,
  });
  const tickets = [
    ...createdTickets,
    ...(ticketsQuery.data ?? []),
    ...(sentTicketsQuery.data ?? []),
  ].filter((ticket, index, all) => all.findIndex((candidate) => candidate.id === ticket.id) === index);
  const selectedTicket = tickets.find((ticket) => ticket.id === selectedId) ?? tickets[0];

  const messagesQuery = useQuery({
    queryKey: ["reseller-support-messages", selectedTicket?.id],
    queryFn: () => listResellerSupportEscalationMessages(selectedTicket!.id),
    enabled: Boolean(selectedTicket?.id),
  });
  const filesQuery = useQuery({ queryKey: ["files"], queryFn: listFiles });
  const activeFiles = (filesQuery.data ?? []).filter((file) => file.status === "active");

  const createMutation = useMutation({
    mutationFn: () => createResellerSupportEscalation({ subject: subject.trim(), description: description.trim() }),
    onSuccess: (ticket) => {
      setCreatedTickets((current) => [ticket, ...current.filter((item) => item.id !== ticket.id)]);
      setSelectedId(ticket.id);
      setSubject("");
      setDescription("");
      setFeedback(m.created);
      setFeedbackIsError(false);
      void qc.invalidateQueries({ queryKey: ["reseller-support-escalations"] });
      void qc.invalidateQueries({ queryKey: ["reseller-support-escalations-sent"] });
    },
    onError: (error) => {
      setFeedback(getErrorMessage(error) || m.error);
      setFeedbackIsError(true);
    },
  });

  const replyMutation = useMutation({
    mutationFn: () => createResellerSupportEscalationMessage(selectedTicket!.id, {
      body: reply.trim(),
      attachment_file_ids: selectedFileIds,
    }),
    onSuccess: () => {
      setReply("");
      setSelectedFileIds([]);
      setFeedback(fa ? "پیام ارسال شد." : "Message sent.");
      setFeedbackIsError(false);
      void qc.invalidateQueries({ queryKey: ["reseller-support-messages", selectedTicket?.id] });
    },
    onError: (error) => {
      setFeedback(getErrorMessage(error) || m.error);
      setFeedbackIsError(true);
    },
  });

  function toggleFile(id: string, checked: boolean) {
    setSelectedFileIds((current) => {
      if (!checked) return current.filter((item) => item !== id);
      if (current.includes(id) || current.length >= 5) return current;
      return [...current, id];
    });
  }

  return (
    <>
      <ResellerSurface
        title={m.title}
        description={m.description}
        capabilities={fa
          ? ["ثبت ارجاع پشتیبانی پلتفرم", "گفت‌وگوی پیوسته در تیکت", "پیوست امن فایل‌های موجود"]
          : ["Platform support escalation", "Ticket message threads", "Secure attachments from existing files"]}
      />
      <div className="grid gap-4 p-6 pt-0 xl:grid-cols-[minmax(280px,0.8fr)_minmax(0,1.4fr)]">
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <LifeBuoy className="h-5 w-5" />
                {m.form}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="reseller-support-subject">{m.subject}</label>
                <input
                  id="reseller-support-subject"
                  value={subject}
                  onChange={(event) => setSubject(event.target.value)}
                  placeholder={m.subjectPlaceholder}
                  className="w-full rounded-md border px-3 py-2 text-sm"
                  maxLength={255}
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="reseller-support-description">{m.descriptionLabel}</label>
                <textarea
                  id="reseller-support-description"
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                  placeholder={m.descriptionPlaceholder}
                  className="min-h-28 w-full rounded-md border px-3 py-2 text-sm"
                  maxLength={10000}
                />
              </div>
              <Button
                disabled={createMutation.isPending || subject.trim().length < 3 || description.trim().length < 5}
                onClick={() => createMutation.mutate()}
              >
                {createMutation.isPending ? m.submitting : m.submit}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>{m.tickets}</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              {ticketsQuery.isLoading && <p className="text-sm text-muted-foreground">{m.loading}</p>}
              {ticketsQuery.isError && <p role="alert" className="text-sm text-red-600">{m.loadError}</p>}
              {!ticketsQuery.isLoading && !ticketsQuery.isError && tickets.length === 0 && (
                <p className="text-sm text-muted-foreground">{m.emptyTickets}</p>
              )}
              {tickets.map((ticket) => (
                <button
                  key={ticket.id}
                  type="button"
                  onClick={() => { setSelectedId(ticket.id); setFeedback(null); }}
                  className={`w-full rounded-lg border p-3 text-start transition hover:bg-muted/50 ${selectedTicket?.id === ticket.id ? "border-primary bg-muted/40" : "border-border"}`}
                >
                  <span className="block font-medium">{ticket.subject}</span>
                  <span className="mt-1 flex items-center justify-between gap-2 text-xs text-muted-foreground">
                    <span>{ticket.id.slice(0, 8)}</span>
                    <Badge status={ticket.status} />
                  </span>
                </button>
              ))}
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquareText className="h-5 w-5" />
              {m.thread}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {feedback && (
              <p role={feedbackIsError ? "alert" : "status"} className={feedbackIsError ? "text-sm text-red-600" : "text-sm text-green-700"}>
                {feedback}
              </p>
            )}
            {!selectedTicket && <p className="text-sm text-muted-foreground">{m.chooseTicket}</p>}
            {selectedTicket && (
              <>
                <div className="rounded-lg bg-muted/40 p-3">
                  <p className="font-medium">{selectedTicket.subject}</p>
                  <p className="mt-1 whitespace-pre-wrap text-sm text-muted-foreground">{selectedTicket.description}</p>
                  <div className="mt-2"><Badge status={selectedTicket.status} /></div>
                </div>

                {messagesQuery.isLoading && <p className="text-sm text-muted-foreground">{m.loading}</p>}
                {messagesQuery.isError && <p role="alert" className="text-sm text-red-600">{m.loadError}</p>}
                {!messagesQuery.isLoading && !messagesQuery.isError && (messagesQuery.data ?? []).length === 0 && (
                  <p className="text-sm text-muted-foreground">{m.noMessages}</p>
                )}
                <div className="max-h-[420px] space-y-3 overflow-y-auto">
                  {(messagesQuery.data ?? []).map((message) => (
                    <article key={message.id} className="rounded-lg border p-3">
                      <p className="whitespace-pre-wrap text-sm">{message.body}</p>
                      <p className="mt-2 text-xs text-muted-foreground">{new Intl.DateTimeFormat(fa ? "fa-IR" : undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(message.created_at))}</p>
                      {message.attachments.length > 0 && (
                        <div className="mt-3 space-y-2">
                          {message.attachments.map((attachment) => (
                            <div key={attachment.id} className="flex flex-wrap items-center justify-between gap-2 rounded-md bg-muted/40 px-3 py-2 text-sm">
                              <span className="flex min-w-0 items-center gap-2"><Paperclip className="h-4 w-4 shrink-0" /><span className="truncate">{attachment.filename}</span></span>
                              <Button
                                size="sm"
                                variant="secondary"
                                onClick={() => downloadResellerSupportAttachment(selectedTicket.id, message.id, attachment.id, attachment.filename)}
                              >
                                <Download className="h-4 w-4" />
                                {m.attachment}
                              </Button>
                            </div>
                          ))}
                        </div>
                      )}
                    </article>
                  ))}
                </div>

                {selectedTicket.status === "resolved" ? (
                  <p className="rounded-md bg-muted/50 p-3 text-sm text-muted-foreground">
                    {fa ? "این تیکت بسته شده است؛ برای پاسخ، ابتدا باید دوباره باز شود." : "This ticket is resolved. It must be reopened before replying."}
                  </p>
                ) : (
                  <div className="space-y-3 border-t pt-4">
                    <label htmlFor="reseller-support-reply" className="block text-sm font-medium">{m.reply}</label>
                    <textarea
                      id="reseller-support-reply"
                      value={reply}
                      onChange={(event) => setReply(event.target.value)}
                      placeholder={m.replyPlaceholder}
                      className="min-h-24 w-full rounded-md border px-3 py-2 text-sm"
                      maxLength={10000}
                    />
                    <div className="space-y-2 rounded-lg border p-3">
                      <p className="text-sm font-medium">{m.files}</p>
                      <p className="text-xs text-muted-foreground">{m.maxFiles}</p>
                      {filesQuery.isLoading && <p className="text-sm text-muted-foreground">{m.loading}</p>}
                      {!filesQuery.isLoading && activeFiles.length === 0 && <p className="text-sm text-muted-foreground">{m.noFiles}</p>}
                      {activeFiles.slice(0, 30).map((file) => (
                        <label key={file.id} className="flex items-center gap-2 text-sm">
                          <input
                            type="checkbox"
                            checked={selectedFileIds.includes(file.id)}
                            disabled={!selectedFileIds.includes(file.id) && selectedFileIds.length >= 5}
                            onChange={(event) => toggleFile(file.id, event.target.checked)}
                          />
                          <span className="min-w-0 flex-1 truncate">{file.filename}</span>
                          <span className="shrink-0 text-xs text-muted-foreground">{formatBytes(file.size_bytes)}</span>
                        </label>
                      ))}
                    </div>
                    <Button
                      disabled={replyMutation.isPending || (reply.trim().length === 0 && selectedFileIds.length === 0)}
                      onClick={() => replyMutation.mutate()}
                    >
                      <Send className="h-4 w-4" />
                      {replyMutation.isPending ? m.sending : m.send}
                    </Button>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
