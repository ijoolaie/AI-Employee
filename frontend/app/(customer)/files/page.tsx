"use client";

import { useRef, useState } from "react";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import {
  deleteFile,
  downloadFile,
  getErrorMessage,
  listFiles,
  uploadFile,
} from "@/lib/api";
import { formatBytes, formatDate } from "@/lib/utils";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, FileText, Trash2, Upload } from "lucide-react";

export default function FilesPage() {
  const qc = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string | null>(null);

  const { data, isLoading, error: loadError } = useQuery({
    queryKey: ["files"],
    queryFn: listFiles,
  });

  const uploadMut = useMutation({
    mutationFn: uploadFile,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["files"] });
      setError(null);
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  const deleteMut = useMutation({
    mutationFn: deleteFile,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["files"] }),
  });

  const files = data ?? [];

  function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      uploadMut.mutate(file);
      e.target.value = "";
    }
  }

  return (
    <>
      <Header
        title="Files"
        description="Tenant-scoped uploads for AI employee inputs"
        actions={
          <>
            <input
              ref={inputRef}
              type="file"
              className="hidden"
              onChange={onFileChange}
            />
            <Button
              size="sm"
              loading={uploadMut.isPending}
              onClick={() => inputRef.current?.click()}
            >
              <Upload className="h-4 w-4" />
              Upload
            </Button>
          </>
        }
      />
      <div className="p-6">
        {(error || loadError) && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error || getErrorMessage(loadError)}
          </div>
        )}
        {isLoading && <Spinner />}
        {!isLoading && files.length === 0 && (
          <EmptyState
            icon={FileText}
            title="No files uploaded"
            description="Upload CSV, Excel, PDF or other files to use as employee inputs."
            action={
              <Button size="sm" onClick={() => inputRef.current?.click()}>
                <Upload className="h-4 w-4" />
                Upload file
              </Button>
            }
          />
        )}
        {!isLoading && files.length > 0 && (
          <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50/50 text-xs uppercase text-gray-500">
                  <th className="px-5 py-3 font-medium">Filename</th>
                  <th className="px-5 py-3 font-medium">Type</th>
                  <th className="px-5 py-3 font-medium">Size</th>
                  <th className="px-5 py-3 font-medium">Status</th>
                  <th className="px-5 py-3 font-medium">Uploaded</th>
                  <th className="px-5 py-3 font-medium" />
                </tr>
              </thead>
              <tbody>
                {files.map((f) => (
                  <tr
                    key={f.id}
                    className="border-b border-gray-50 hover:bg-gray-50/50"
                  >
                    <td className="px-5 py-3 font-medium text-gray-900">
                      {f.filename}
                    </td>
                    <td className="px-5 py-3 text-gray-500">
                      {f.content_type || "—"}
                    </td>
                    <td className="px-5 py-3 text-gray-600">
                      {formatBytes(f.size_bytes)}
                    </td>
                    <td className="px-5 py-3">
                      <Badge status={f.status} />
                    </td>
                    <td className="px-5 py-3 text-gray-500">
                      {formatDate(f.created_at)}
                    </td>
                    <td className="px-5 py-3 text-right">
                      <button
                        onClick={() => downloadFile(f.id, f.filename)}
                        className="rounded p-1.5 text-gray-400 hover:bg-brand-50 hover:text-brand-600"
                        title="Download"
                      >
                        <Download className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => {
                          if (confirm(`Delete ${f.filename}?`)) {
                            deleteMut.mutate(f.id);
                          }
                        }}
                        className="rounded p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-600"
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
