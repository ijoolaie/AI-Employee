"use client";

import { use, useCallback, useMemo, useState, useSyncExternalStore } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { createPublicConversation, getPublicChannel, getPublicConversation, getErrorMessage, sendPublicMessage, requestPublicEmailVerification, confirmPublicEmailVerification, getPublicCustomerOrders } from "@/lib/api";
import type { PublicConversation, PublicCustomerOrders } from "@/types";
import { useI18n } from "@/lib/i18n/provider";
import { Bot, Send } from "lucide-react";

const CHAT_STORAGE_EVENT = "aiep-chat-storage";
function subscribeChatStorage(callback: () => void) {
  window.addEventListener("storage", callback);
  window.addEventListener(CHAT_STORAGE_EVENT, callback);
  return () => { window.removeEventListener("storage", callback); window.removeEventListener(CHAT_STORAGE_EVENT, callback); };
}

export default function PublicChatPage({ params }: { params: Promise<{ publicKey: string }> }) {
  const { publicKey } = use(params);
  const { locale, t } = useI18n();
  const m = t.publicChat;
  const channel = useQuery({ queryKey: ["public-channel", publicKey], queryFn: () => getPublicChannel(publicKey) });
  const getStoredChat = useCallback(() => typeof window === "undefined" ? null : window.localStorage.getItem(`aiep-chat-${publicKey}`), [publicKey]);
  const storedChat = useSyncExternalStore(subscribeChatStorage, getStoredChat, () => null);
  const savedChat = useMemo(() => {
    if (!storedChat) return null;
    try { return JSON.parse(storedChat) as { id: string; token: string }; } catch { return null; }
  }, [storedChat]);
  const conversationQuery = useQuery({
    queryKey: ["public-conversation", savedChat?.id, savedChat?.token],
    queryFn: () => getPublicConversation(savedChat!.id, savedChat!.token),
    enabled: Boolean(savedChat),
    refetchInterval: savedChat ? 1200 : false,
  });
  const conversation = conversationQuery.data as PublicConversation | undefined;
  const token = savedChat?.token ?? null;
  const [message, setMessage] = useState("");
  const [email, setEmail] = useState("");
  const [verificationCode, setVerificationCode] = useState("");
  const [verificationMessage, setVerificationMessage] = useState<string | null>(null);
  const [orders, setOrders] = useState<PublicCustomerOrders | null>(null);
  const [error, setError] = useState<string | null>(null);

  const start = useMutation({
    mutationFn: () => createPublicConversation(publicKey, { customer_email: email.trim() }),
    onSuccess: (data) => {
      const t = data.customer_token ?? "";
      window.localStorage.setItem(`aiep-chat-${publicKey}`, JSON.stringify({ id: data.id, token: t }));
      window.dispatchEvent(new Event(CHAT_STORAGE_EVENT));
      setError(null);
    },
    onError: (e) => setError(getErrorMessage(e)),
  });

  const requestVerification = useMutation({
    mutationFn: () => requestPublicEmailVerification(conversation!.id, token!),
    onSuccess: () => setVerificationMessage(locale === "fa" ? "اگر امکان تأیید ایمیل فراهم باشد، کد برای شما ارسال می‌شود." : "If email verification is available, a code has been sent."),
    onError: (e) => setError(getErrorMessage(e)),
  });

  const confirmVerification = useMutation({
    mutationFn: () => confirmPublicEmailVerification(conversation!.id, token!, verificationCode.trim()),
    onSuccess: async (result) => {
      setVerificationMessage(result.verified ? (locale === "fa" ? "ایمیل تأیید شد." : "Email verified.") : (locale === "fa" ? "کد نامعتبر است یا اعتبار آن تمام شده." : "The code is invalid or expired."));
      setVerificationCode("");
      if (result.verified) await conversationQuery.refetch();
    },
    onError: (e) => setError(getErrorMessage(e)),
  });

  const loadOrders = useMutation({
    mutationFn: () => getPublicCustomerOrders(conversation!.id, token!),
    onSuccess: (result) => setOrders(result),
    onError: (e) => setError(getErrorMessage(e)),
  });

  const send = useMutation({
    mutationFn: () => sendPublicMessage(conversation!.id, token!, message.trim()),
    onSuccess: () => setMessage(""),
    onError: (e) => setError(getErrorMessage(e)),
  });

  if (channel.isLoading) return <main className="flex min-h-screen items-center justify-center bg-slate-50 text-sm text-slate-500">{m.loading}</main>;
  if (channel.error || !channel.data) return <main className="flex min-h-screen items-center justify-center bg-slate-50 p-6 text-sm text-red-600">{m.unavailable}</main>;
  const c = channel.data;
  return <main dir={locale === "fa" ? "rtl" : "ltr"} className="flex min-h-screen items-center justify-center bg-slate-100 p-4">
    <section className="flex h-[min(760px,calc(100vh-32px))] w-full max-w-md flex-col overflow-hidden rounded-2xl bg-white shadow-xl ring-1 ring-slate-200">
      <header className="flex items-center gap-3 border-b px-5 py-4"><div className="rounded-full bg-slate-900 p-2 text-white"><Bot className="h-5 w-5" /></div><div><h1 className="font-semibold text-slate-900">{c.employee_name}</h1><p className="text-xs text-slate-500">{c.channel_name}</p></div></header>
      <div className="flex-1 space-y-3 overflow-y-auto bg-slate-50 p-4">
        {!conversation && <div className="flex h-full flex-col items-center justify-center text-center"><Bot className="h-10 w-10 text-slate-400" /><h2 className="mt-4 font-semibold">{m.greeting}</h2><p className="mt-2 max-w-xs text-sm text-slate-500">{m.greetingDescription}</p><form onSubmit={(e) => { e.preventDefault(); if (email.trim()) start.mutate(); }} className="mt-5 flex w-full max-w-xs flex-col gap-3"><label className="text-start text-xs text-slate-600">{locale === "fa" ? "ایمیل برای تأیید مالکیت" : "Email for ownership verification"}</label><input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" className="rounded-xl border px-3 py-2 text-sm" /><button disabled={start.isPending} className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-40">{m.start}</button></form></div>}
        {conversation && !conversation.email_verified && <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-slate-700"><p>{locale === "fa" ? "برای تأیید مالکیت ایمیل، کد شش‌رقمی ارسال کنید." : "Verify that you own this email address."}</p><button type="button" disabled={requestVerification.isPending} onClick={() => requestVerification.mutate()} className="mt-2 rounded-lg bg-slate-900 px-3 py-2 text-xs text-white disabled:opacity-40">{locale === "fa" ? "ارسال کد تأیید" : "Send verification code"}</button><form onSubmit={(e) => { e.preventDefault(); if (/^\\d{6}$/.test(verificationCode)) confirmVerification.mutate(); }} className="mt-2 flex gap-2"><input inputMode="numeric" maxLength={6} value={verificationCode} onChange={(e) => setVerificationCode(e.target.value.replace(/\\D/g, "").slice(0, 6))} placeholder="000000" className="min-w-0 flex-1 rounded-lg border px-3 py-2 text-sm" /><button disabled={verificationCode.length !== 6 || confirmVerification.isPending} className="rounded-lg bg-slate-700 px-3 py-2 text-xs text-white disabled:opacity-40">{locale === "fa" ? "تأیید" : "Verify"}</button></form>{verificationMessage && <p className="mt-2 text-xs">{verificationMessage}</p>}</div>}{conversation?.email_verified && <div className="rounded-xl border bg-white p-3"><button type="button" disabled={loadOrders.isPending} onClick={() => loadOrders.mutate()} className="rounded-lg bg-slate-900 px-3 py-2 text-xs text-white disabled:opacity-40">{locale === "fa" ? "نمایش سفارش‌های من" : "Show my orders"}</button>{orders && <div className="mt-2 space-y-2 text-xs text-slate-700"><p>{orders.message}</p>{orders.available && orders.orders.map((order) => <div key={order.number} className="rounded-lg border p-2"><strong>{order.number}</strong><span className="ms-2">{order.status}</span><p>{order.order_date} · {order.total} {order.currency}</p></div>)}</div>}</div>}{conversation?.messages.map((m) => <div key={m.id} className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${m.role === "user" ? "ms-auto bg-slate-900 text-white" : "bg-white text-slate-800 shadow-sm ring-1 ring-slate-200"}`}>{m.content}</div>)}
      </div>
      {error && <div className="border-t bg-red-50 px-4 py-2 text-xs text-red-700">{error}</div>}
      <form className="flex gap-2 border-t p-3" onSubmit={(e) => { e.preventDefault(); if (conversation && token && message.trim()) send.mutate(); }}><textarea value={message} onChange={(e) => setMessage(e.target.value)} disabled={!conversation || send.isPending} rows={2} placeholder={conversation ? m.placeholder : m.startFirst} className="flex-1 resize-none rounded-xl border px-3 py-2 text-sm outline-none focus:border-slate-500" /><button disabled={!conversation || !message.trim() || send.isPending} className="self-end rounded-xl bg-slate-900 p-3 text-white disabled:opacity-40"><Send className="h-4 w-4" /></button></form>
    </section>
  </main>;
}
