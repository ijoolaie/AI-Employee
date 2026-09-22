"use client";

import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { deleteFile, downloadFile, getErrorMessage, listFiles, uploadFile } from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";
import { Download, FileText, Trash2, Upload } from "lucide-react";

function isPermissionError(error: unknown) {
  const message = getErrorMessage(error).toLowerCase();
  return message.includes("permission") || message.includes("403") || message.includes("forbidden");
}

export default function FilesPage() {
  const { t } = useI18n();
  const m = t.files;
  const qc = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [mutationError, setMutationError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [actionId, setActionId] = useState<string | null>(null);

  const filesQuery = useQuery({ queryKey: ["files"], queryFn: listFiles });
  const files = filesQuery.data ?? [];

  const uploadMutation = useMutation({
    mutationFn: uploadFile,
    onMutate: () => {
      setMutationError(null);
      setSuccessMessage(null);
      setActionId("upload");
    },
    onSuccess: (file) => {
      setMutationError(null);
      setSuccessMessage(m.uploadSuccess.replace("{filename}", file.filename));
      void qc.invalidateQueries({ queryKey: ["files"] });
    },
    onError: (error) => {
      setSuccessMessage(null);
      setMutationError(isPermissionError(error) ? m.permissionDenied : getErrorMessage(error) || m.uploadError);
    },
    onSettled: () => setActionId(null),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteFile,
    onMutate: (id) => {
      setMutationError(null);
      setSuccessMessage(null);
      setActionId(id);
    },
    onSuccess: (_, id) => {
      setMutationError(null);
      setSuccessMessage(m.deleteSuccess);
      void qc.invalidateQueries({ queryKey: ["files"] });
      if (inputRef.current) inputRef.current.value = "";
      setActionId(null);
      void id;
    },
    onError: (error) => {
      setSuccessMessage(null);
      setMutationError(isPermissionError(error) ? m.permissionDenied : getErrorMessage(error) || m.deleteError);
    },
    onSettled: () => setActionId(null),
  });

  const downloadMutation = useMutation({
    mutationFn: ({ id, filename }: { id: string; filename: string }) => downloadFile(id, filename),
    onMutate: ({ id }) => {
      setMutationError(null);
      setSuccessMessage(null);
      setActionId(id);
    },
    onError: (error) => {
      setSuccessMessage(null);
      setMutationError(isPermissionError(error) ? m.permissionDenied : getErrorMessage(error) || m.downloadError);
    },
    onSettled: () => setActionId(null),
  });

  function onFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (file) uploadMutation.mutate(file);
  }

  function retry() {
    setMutationError(null);
    setSuccessMessage(null);
    void filesQuery.refetch();
  }

  function confirmDelete(id: string, filename: string) {
    if (window.confirm(m.confirmDelete.replace("{filename}", filename))) {
      deleteMutation.mutate(id);
    }
  }

  return (
    <>
      <Header
        title={m.title}
        description={m.description}
        actions={
          <>
            <input
              ref={inputRef}
              type="file"
              className="hidden"
              accept=".txt,.csv,.pdf,.json,.docx,.xlsx,.xls,.png,.jpg,.jpeg"
              onChange={onFileChange}
            />
            <Button size="sm" loading={actionId === "upload"} onClick={() => inputRef.current?.click()}>
              <Upload className="h-4 w-4" />
              {m.upload}
            </Button>
          </>
        }
      />

      <div className="space-y-4 p-6">
        {filesQuery.isLoading && (
          <div className="flex justify-center py-12" aria-label={m.loading}>
            <Spinner />
          </div>
        )}

        {filesQuery.error && !filesQuery.isLoading && (
          <div role="alert" className="space-y-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm">
            <p className="text-red-700">{isPermissionError(filesQuery.error) ? m.permissionDenied : m.loadError}</p>
            <Button variant="secondary" onClick={retry}>{m.retry}</Button>
          </div>
        )}

        {!filesQuery.isLoading && !filesQuery.error && (mutationError || successMessage) && (
          <div
            role={mutationError ? "alert" : "status"}
            className={mutationError
              ? "rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
              : "rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700"}
          >
            {mutationError || successMessage}
          </div>
        )}

        {!filesQuery.isLoading && !filesQuery.error && files.length === 0 && (
          <EmptyState
            icon={FileText}
            title={m.emptyTitle}
            description={m.emptyDescription}
            action={
              <Button size="sm" onClick={() => inputRef.current?.click()}>
                <Upload className="h-4 w-4" />
                {m.upload}
              </Button>
            }
          />
        )}

        {!filesQuery.isLoading && !filesQuery.error && files.length > 0 && (
          <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
            <table className="w-full min-w-[760px] text-start text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50/60 text-xs text-gray-500">
                  <th className="px-5 py-3 text-start font-medium">{m.filename}</th>
                  <th className="px-5 py-3 text-start font-medium">{m.type}</th>
                  <th className="px-5 py-3 text-start font-medium">{m.size}</th>
                  <th className="px-5 py-3 text-start font-medium">{m.status}</th>
                  <th className="px-5 py-3 text-start font-medium">{m.uploaded}</th>
                  <th className="px-5 py-3 text-end font-medium">{m.actions}</th>
                </tr>
              </thead>
              <tbody>
                {files.map((file) => {
                  const busy = actionId === file.id;
                  return (
                    <tr key={file.id} className="border-b border-gray-50 last:border-0 hover:bg-gray-50/50">
                      <td className="px-5 py-3 font-medium text-gray-900">{file.filename}</td>
                      <td className="px-5 py-3 text-gray-500">{file.content_type || m.unknown}</td>
                      <td className="px-5 py-3 text-gray-600">{formatBytes(file.size_bytes)}</td>
                      <td className="px-5 py-3"><Badge status={file.status} /></td>
                      <td className="px-5 py-3 text-gray-500">{formatDate(file.created_at)}</td>
                      <td className="px-5 py-3 text-end">
                        <div className="flex justify-end gap-1">
                          <Button
                            size="sm"
                            variant="ghost"
                            disabled={busy || deleteMutation.isPending}
                            aria-label={m.download}
                            title={m.download}
                            onClick={() => downloadMutation.mutate({ id: file.id, filename: file.filename })}
                          >
                            <Download className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            disabled={busy || deleteMutation.isPending}
                            aria-label={m.delete}
                            title={m.delete}
                            onClick={() => confirmDelete(file.id, file.filename)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}
