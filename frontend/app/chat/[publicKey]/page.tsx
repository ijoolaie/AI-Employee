"use client";

import { use, useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { createPublicConversation, getPublicChannel, getPublicConversation, getErrorMessage, sendPublicMessage } from "@/lib/api";
import type { PublicConversation } from "@/types";
import { Bot, Send } from "lucide-react";

export default function PublicChatPage({ params }: { params: Promise<{ publicKey: string }> }) {
  const { publicKey } = use(params);
  const channel = useQuery({ queryKey: ["public-channel", publicKey], queryFn: () => getPublicChannel(publicKey) });
  const [conversation, setConversation] = useState<PublicConversation | null>(null);
  const [message, setMessage] = useState("");
  const [token, setToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const saved = window.localStorage.getItem(`aiep-chat-${publicKey}`);
    if (!saved) return;
    try { const parsed = JSON.parse(saved) as { id: string; token: string }; setToken(parsed.token); getPublicConversation(parsed.id, parsed.token).then(setConversation).catch(() => window.localStorage.removeItem(`aiep-chat-${publicKey}`)); } catch { /* ignore corrupt local state */ }
  }, [publicKey]);

  const start = useMutation({
    mutationFn: () => createPublicConversation(publicKey),
    onSuccess: (data) => { const t = data.customer_token ?? ""; setToken(t); setConversation(data); window.localStorage.setItem(`aiep-chat-${publicKey}`, JSON.stringify({ id: data.id, token: t })); },
    onError: (e) => setError(getErrorMessage(e)),
  });

  const send = useMutation({
    mutationFn: () => sendPublicMessage(conversation!.id, token!, message.trim()),
    onSuccess: () => setMessage(""),
    onError: (e) => setError(getErrorMessage(e)),
  });

  const conversationId = conversation?.id;
  useEffect(() => {
    if (!conversationId || !token) return;
    const timer = window.setInterval(async () => { try { setConversation(await getPublicConversation(conversationId, token)); } catch { /* transient polling failure */ } }, 1200);
    return () => window.clearInterval(timer);
  }, [conversationId, token]);

  if (channel.isLoading) return <main className="flex min-h-screen items-center justify-center bg-slate-50 text-sm text-slate-500">Loading assistant…</main>;
  if (channel.error || !channel.data) return <main className="flex min-h-screen items-center justify-center bg-slate-50 p-6 text-sm text-red-600">This assistant link is not available.</main>;
  const c = channel.data;
  return <main className="flex min-h-screen items-center justify-center bg-slate-100 p-4">
    <section className="flex h-[min(760px,calc(100vh-32px))] w-full max-w-md flex-col overflow-hidden rounded-2xl bg-white shadow-xl ring-1 ring-slate-200">
      <header className="flex items-center gap-3 border-b px-5 py-4"><div className="rounded-full bg-slate-900 p-2 text-white"><Bot className="h-5 w-5" /></div><div><h1 className="font-semibold text-slate-900">{c.employee_name}</h1><p className="text-xs text-slate-500">{c.channel_name}</p></div></header>
      <div className="flex-1 space-y-3 overflow-y-auto bg-slate-50 p-4">
        {!conversation && <div className="flex h-full flex-col items-center justify-center text-center"><Bot className="h-10 w-10 text-slate-400" /><h2 className="mt-4 font-semibold">Hi! How can I help?</h2><p className="mt-2 max-w-xs text-sm text-slate-500">Ask about products, sizes, availability, orders, or anything this store has configured me to help with.</p><button onClick={() => start.mutate()} className="mt-5 rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white">Start chat</button></div>}
        {conversation?.messages.map((m) => <div key={m.id} className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${m.role === "user" ? "ml-auto bg-slate-900 text-white" : "bg-white text-slate-800 shadow-sm ring-1 ring-slate-200"}`}>{m.content}</div>)}
      </div>
      {error && <div className="border-t bg-red-50 px-4 py-2 text-xs text-red-700">{error}</div>}
      <form className="flex gap-2 border-t p-3" onSubmit={(e) => { e.preventDefault(); if (conversation && token && message.trim()) send.mutate(); }}><textarea value={message} onChange={(e) => setMessage(e.target.value)} disabled={!conversation || send.isPending} rows={2} placeholder={conversation ? "Type your question…" : "Start the chat first"} className="flex-1 resize-none rounded-xl border px-3 py-2 text-sm outline-none focus:border-slate-500" /><button disabled={!conversation || !message.trim() || send.isPending} className="self-end rounded-xl bg-slate-900 p-3 text-white disabled:opacity-40"><Send className="h-4 w-4" /></button></form>
    </section>
  </main>;
}
