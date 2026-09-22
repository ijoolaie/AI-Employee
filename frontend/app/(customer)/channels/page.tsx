"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { createCustomerChannel, listCustomerChannels, listEmployees, getErrorMessage } from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";
import { Bot, Check, Copy, ExternalLink, Globe2, MessageCircle, Plus, Radio, X } from "lucide-react";

function isPermissionError(error: unknown) {
  const message = getErrorMessage(error).toLowerCase();
  return message.includes("permission") || message.includes("403");
}

export default function ChannelsPage() {
  const { t } = useI18n();
  const m = t.channels;
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [employeeId, setEmployeeId] = useState("");
  const [name, setName] = useState("");
  const [webhookSecret, setWebhookSecret] = useState("");
  const [type, setType] = useState<"web_widget" | "public_chat" | "whatsapp">("web_widget");
  const [copied, setCopied] = useState<string | null>(null);

  const employeesQ = useQuery({ queryKey: ["employees"], queryFn: listEmployees });
  const channelsQ = useQuery({ queryKey: ["customer-channels"], queryFn: () => listCustomerChannels() });
  const employees = useMemo(() => employeesQ.data ?? [], [employeesQ.data]);
  const channels = channelsQ.data ?? [];
  const origin = typeof window !== "undefined" ? window.location.origin : "";
  const employeeName = useMemo(
    () => employees.find((employee) => employee.id === employeeId)?.name ?? "",
    [employees, employeeId]
  );

  const create = useMutation({
    mutationFn: () =>
      createCustomerChannel({
        employee_id: employeeId,
        name: name.trim(),
        channel_type: type,
        config: type === "whatsapp" && webhookSecret.trim()
          ? { webhook_secret: webhookSecret.trim() }
          : {},
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["customer-channels"] });
      setOpen(false);
      setEmployeeId("");
      setName("");
      setWebhookSecret("");
      setType("web_widget");
    },
  });

  async function copy(value: string) {
    await navigator.clipboard.writeText(value);
    setCopied(value);
    window.setTimeout(() => setCopied(null), 1400);
  }

  function openCreate() {
    setEmployeeId(employees[0]?.id ?? "");
    setName(m.defaultName);
    setWebhookSecret("");
    setType("web_widget");
    create.reset();
    setOpen(true);
  }

  const canCreate = Boolean(employeeId && employeeName && name.trim());

  return (
    <>
      <Header
        title={m.title}
        description={m.description}
        actions={
          <Button size="sm" onClick={openCreate} disabled={employeesQ.isLoading || employees.length === 0}>
            <Plus className="h-4 w-4" />
            {m.newChannel}
          </Button>
        }
      />
      <div className="space-y-6 p-6">
        <Card className="overflow-hidden border-brand-100 bg-gradient-to-br from-brand-50 to-white">
          <CardContent className="grid gap-5 p-6 md:grid-cols-[1fr_auto] md:items-center">
            <div>
              <div className="mb-2 flex items-center gap-2 text-brand-700">
                <Radio className="h-4 w-4" />
                <span className="text-xs font-semibold uppercase tracking-wider">{m.customerExperience}</span>
              </div>
              <h2 className="text-xl font-semibold text-slate-900">{m.heroTitle}</h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">{m.heroDescription}</p>
            </div>
            <div className="flex gap-3">
              <div className="rounded-xl bg-white p-4 text-center shadow-sm ring-1 ring-slate-200">
                <Globe2 className="mx-auto h-5 w-5 text-brand-600" />
                <p className="mt-1 text-xs font-medium">{m.web}</p>
              </div>
              <div className="rounded-xl bg-white p-4 text-center shadow-sm ring-1 ring-slate-200">
                <MessageCircle className="mx-auto h-5 w-5 text-brand-600" />
                <p className="mt-1 text-xs font-medium">{m.chat}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {channelsQ.isLoading && (
          <div className="flex justify-center py-12" aria-label={m.loading}>
            <Spinner />
          </div>
        )}

        {channelsQ.error && (
          <div role="alert" className="space-y-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm">
            <p className="text-red-700">{isPermissionError(channelsQ.error) ? m.permissionDenied : m.error}</p>
            <Button variant="secondary" onClick={() => channelsQ.refetch()}>{m.retry}</Button>
          </div>
        )}

        {!channelsQ.isLoading && !channelsQ.error && channels.length === 0 && (
          <EmptyState
            icon={Radio}
            title={m.emptyTitle}
            description={employees.length === 0 ? m.emptyNoEmployees : m.emptyDescription}
            action={
              employees.length > 0 ? (
                <Button size="sm" onClick={openCreate}>
                  <Plus className="h-4 w-4" />
                  {m.createChannel}
                </Button>
              ) : undefined
            }
          />
        )}

        {!channelsQ.isLoading && !channelsQ.error && channels.length > 0 && (
          <div className="grid gap-4 lg:grid-cols-2">
            {channels.map((channel) => {
              const chatUrl = `${origin}/chat/${channel.public_key}`;
              const embed = `<script src="${origin}/widget.js?channel=${channel.public_key}"></script>`;
              const webhook = `${origin}/api/v1/webhooks/channels/whatsapp/${channel.id}`;
              const label = channel.channel_type === "web_widget"
                ? m.websiteWidget
                : channel.channel_type === "whatsapp" ? m.whatsapp : m.publicChat;
              return (
                <Card key={channel.id}>
                  <CardHeader className="flex flex-row items-start justify-between gap-4">
                    <div className="flex items-start gap-3">
                      <div className="rounded-lg bg-brand-50 p-2.5">
                        <Bot className="h-5 w-5 text-brand-600" />
                      </div>
                      <div>
                        <CardTitle className="text-base">{channel.name}</CardTitle>
                        <p className="mt-1 text-xs text-slate-500">
                          {employees.find((employee) => employee.id === channel.employee_id)?.name ?? m.aiEmployee} · {label}
                        </p>
                      </div>
                    </div>
                    <Badge status={channel.is_active ? "active" : "inactive"} />
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">{m.customerChatUrl}</p>
                      <div className="flex gap-2">
                        <input readOnly value={chatUrl} className="min-w-0 flex-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600" />
                        <Button size="sm" variant="outline" aria-label={m.copy} onClick={() => copy(chatUrl)}>
                          {copied === chatUrl ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                        </Button>
                        <a href={chatUrl} target="_blank" rel="noreferrer" aria-label={m.openChat} className="inline-flex h-9 items-center rounded-lg border border-slate-200 px-3 text-slate-600 hover:bg-slate-50">
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      </div>
                    </div>

                    {channel.channel_type === "whatsapp" ? (
                      <div>
                        <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">{m.whatsappWebhook}</p>
                        <div className="flex gap-2">
                          <code className="min-w-0 flex-1 overflow-hidden rounded-lg bg-slate-950 px-3 py-2 text-[11px] text-slate-200">{webhook}</code>
                          <Button size="sm" variant="outline" aria-label={m.copy} onClick={() => copy(webhook)}>
                            {copied === webhook ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                          </Button>
                        </div>
                        <p className="mt-2 text-xs text-slate-500">{m.whatsappHelp}</p>
                      </div>
                    ) : (
                      <div>
                        <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">{m.websiteEmbed}</p>
                        <div className="flex gap-2">
                          <code className="min-w-0 flex-1 overflow-hidden rounded-lg bg-slate-950 px-3 py-2 text-[11px] text-slate-200">{embed}</code>
                          <Button size="sm" variant="outline" aria-label={m.copy} onClick={() => copy(embed)}>
                            {copied === embed ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                          </Button>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4"
          role="dialog"
          aria-modal="true"
          onMouseDown={(event) => { if (event.target === event.currentTarget) setOpen(false); }}
        >
          <Card className="w-full max-w-lg shadow-2xl">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>{m.createTitle}</CardTitle>
                <p className="mt-1 text-sm text-slate-500">{m.createDescription}</p>
              </div>
              <button aria-label={m.close} onClick={() => setOpen(false)} className="rounded-lg p-2 text-slate-400 hover:bg-slate-100">
                <X className="h-5 w-5" />
              </button>
            </CardHeader>
            <CardContent className="space-y-4">
              <label className="block">
                <span className="mb-1.5 block text-sm font-medium text-slate-700">{m.aiEmployee}</span>
                <select value={employeeId} onChange={(event) => setEmployeeId(event.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm">
                  <option value="">{m.selectEmployee}</option>
                  {employees.map((employee) => <option key={employee.id} value={employee.id}>{employee.name} · {employee.kind}</option>)}
                </select>
              </label>
              <label className="block">
                <span className="mb-1.5 block text-sm font-medium text-slate-700">{m.channelName}</span>
                <input value={name} onChange={(event) => setName(event.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm" placeholder={m.defaultName} />
              </label>
              <div>
                <span className="mb-1.5 block text-sm font-medium text-slate-700">{m.experience}</span>
                <div className="grid gap-3 sm:grid-cols-3">
                  {(["web_widget", "public_chat", "whatsapp"] as const).map((value) => (
                    <button
                      type="button"
                      key={value}
                      onClick={() => setType(value)}
                      className={`rounded-xl border p-3 text-start ${type === value ? "border-brand-500 bg-brand-50" : "border-slate-200 hover:bg-slate-50"}`}
                    >
                      <p className="text-sm font-medium">
                        {value === "web_widget" ? m.websiteWidget : value === "whatsapp" ? m.whatsapp : m.publicChat}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">
                        {value === "web_widget" ? m.widgetDescription : value === "whatsapp" ? m.whatsappDescription : m.publicChatDescription}
                      </p>
                    </button>
                  ))}
                </div>
              </div>
              {type === "whatsapp" && (
                <label className="block">
                  <span className="mb-1.5 block text-sm font-medium text-slate-700">
                    {m.webhookSecret} <span className="font-normal text-slate-400">{m.optional}</span>
                  </span>
                  <input type="password" value={webhookSecret} onChange={(event) => setWebhookSecret(event.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm" placeholder={m.webhookSecretPlaceholder} />
                </label>
              )}
              {create.error && (
                <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                  {isPermissionError(create.error) ? m.permissionDenied : getErrorMessage(create.error) || m.createError}
                </div>
              )}
              <Button className="w-full" disabled={!canCreate} loading={create.isPending} onClick={() => create.mutate()}>
                {m.publish}
              </Button>
            </CardContent>
          </Card>
        </div>
      )}
    </>
  );
}
