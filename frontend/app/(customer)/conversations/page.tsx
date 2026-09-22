"use client";

import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage, listCustomerConversations } from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";
import { formatDate } from "@/lib/utils";
import { MessageCircle } from "lucide-react";

function isPermissionError(error: unknown) {
  const message = getErrorMessage(error).toLowerCase();
  return message.includes("permission") || message.includes("403");
}

export default function ConversationsPage() {
  const { t } = useI18n();
  const m = t.conversations;
  const q = useQuery({
    queryKey: ["customer-conversations"],
    queryFn: () => listCustomerConversations(),
  });

  const conversations = q.data ?? [];

  return (
    <>
      <Header title={m.title} description={m.description} />
      <div className="space-y-4 p-6">
        {q.isLoading && (
          <div className="flex justify-center py-12" aria-label={m.loading}>
            <Spinner />
          </div>
        )}

        {q.error && (
          <div role="alert" className="space-y-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm">
            <p className="text-red-700">{isPermissionError(q.error) ? m.permissionDenied : m.error}</p>
            <Button variant="secondary" onClick={() => q.refetch()}>{m.retry}</Button>
          </div>
        )}

        {!q.isLoading && !q.error && conversations.length === 0 && (
          <EmptyState
            icon={MessageCircle}
            title={m.emptyTitle}
            description={m.emptyDescription}
          />
        )}

        {!q.isLoading && !q.error && conversations.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>{m.directory}</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-start text-xs uppercase text-gray-500">
                      <th className="px-5 py-3 text-start">{m.customer}</th>
                      <th className="px-5 py-3 text-start">{m.status}</th>
                      <th className="px-5 py-3 text-start">{m.messages}</th>
                      <th className="px-5 py-3 text-start">{m.lastMessage}</th>
                      <th className="px-5 py-3 text-start">{m.updated}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {conversations.map((conversation) => (
                      <tr key={conversation.id} className="border-b border-gray-50 last:border-0">
                        <td className="px-5 py-4">
                          <div className="font-medium text-gray-900">
                            {conversation.customer_name || m.anonymous}
                          </div>
                          <div className="mt-1 text-xs text-gray-400">
                            {conversation.customer_email ||
                              conversation.customer_phone ||
                              conversation.id.slice(0, 8)}
                          </div>
                        </td>
                        <td className="px-5 py-4">
                          <Badge status={conversation.status} />
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap">
                          {conversation.message_count}
                        </td>
                        <td className="max-w-md px-5 py-4 text-gray-600">
                          <div className="truncate" title={conversation.last_message || undefined}>
                            {conversation.last_message || m.noLastMessage}
                          </div>
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap text-gray-500">
                          {formatDate(conversation.updated_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </>
  );
}
