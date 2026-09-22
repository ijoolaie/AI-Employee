"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { getErrorMessage, indexKnowledgeFile, listFiles, searchKnowledge } from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";
import { FileText, Search } from "lucide-react";
import type { KnowledgeSearchResult } from "@/types";

function isPermissionError(error: unknown) {
  const message = getErrorMessage(error).toLowerCase();
  return message.includes("permission") || message.includes("403");
}

export default function KnowledgePage() {
  const { t } = useI18n();
  const m = t.knowledge;
  const qc = useQueryClient();
  const [selectedFileId, setSelectedFileId] = useState("");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<KnowledgeSearchResult[]>([]);
  const [indexMessage, setIndexMessage] = useState<string | null>(null);
  const [searchMessage, setSearchMessage] = useState<string | null>(null);
  const [indexError, setIndexError] = useState<string | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  const filesQuery = useQuery({ queryKey: ["files"], queryFn: listFiles });
  const files = useMemo(() => filesQuery.data ?? [], [filesQuery.data]);

  const indexMutation = useMutation({
    mutationFn: () => indexKnowledgeFile(selectedFileId),
    onSuccess: (doc) => {
      setIndexError(null);
      setIndexMessage(m.indexSuccess
        .replace("{status}", doc.status)
        .replace("{chunks}", String(doc.chunk_count)));
      qc.invalidateQueries({ queryKey: ["files"] });
    },
    onError: (err) => {
      setIndexMessage(null);
      setIndexError(isPermissionError(err) ? m.permissionDenied : getErrorMessage(err) || m.indexError);
    },
  });

  const searchMutation = useMutation({
    mutationFn: () => searchKnowledge(query.trim(), 8),
    onSuccess: (data) => {
      setSearchError(null);
      setResults(data);
      setSearchMessage(data.length ? m.searchSuccess.replace("{count}", String(data.length)) : m.noResults);
    },
    onError: (err) => {
      setResults([]);
      setSearchMessage(null);
      setSearchError(isPermissionError(err) ? m.permissionDenied : getErrorMessage(err) || m.searchError);
    },
  });

  const retryFiles = () => { void filesQuery.refetch(); };
  const clearSearch = () => {
    setQuery("");
    setResults([]);
    setSearchMessage(null);
    setSearchError(null);
  };

  return (
    <>
      <Header title={m.title} description={m.description} />
      <div className="mx-auto max-w-5xl space-y-6 p-6">
        <Card>
          <CardHeader>
            <CardTitle>{m.indexTitle}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {filesQuery.isLoading && <div className="flex justify-center py-6" aria-label={m.loading}><Spinner /></div>}
            {filesQuery.error && (
              <div role="alert" className="space-y-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm">
                <p className="text-red-700">{isPermissionError(filesQuery.error) ? m.permissionDenied : m.loadError}</p>
                <Button variant="secondary" onClick={retryFiles}>{m.retry}</Button>
              </div>
            )}
            {!filesQuery.isLoading && !filesQuery.error && files.length === 0 && (
              <EmptyState icon={FileText} title={m.noFiles} description={m.noFilesDescription} />
            )}
            {!filesQuery.isLoading && !filesQuery.error && files.length > 0 && (
              <>
                <label className="block text-sm font-medium text-gray-700">
                  <span className="mb-1.5 block">{m.file}</span>
                  <select
                    className="mt-1.5 flex h-10 w-full rounded-lg border border-gray-300 bg-white px-3 text-sm text-start"
                    value={selectedFileId}
                    onChange={(e) => { setSelectedFileId(e.target.value); setIndexMessage(null); setIndexError(null); }}
                  >
                    <option value="">{m.selectFile}</option>
                    {files.map((f) => <option key={f.id} value={f.id}>{f.filename} ({f.status})</option>)}
                  </select>
                </label>
                {indexMessage && <p role="status" className="text-sm text-emerald-700">{indexMessage}</p>}
                {indexError && <p role="alert" className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{indexError}</p>}
                <Button disabled={!selectedFileId || indexMutation.isPending} loading={indexMutation.isPending} onClick={() => indexMutation.mutate()}>
                  <FileText className="h-4 w-4" />{m.index}
                </Button>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Search className="h-5 w-5" />{m.searchTitle}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label={m.query}
              placeholder={m.queryPlaceholder}
              value={query}
              onChange={(e) => { setQuery(e.target.value); setSearchError(null); setSearchMessage(null); }}
              onKeyDown={(e) => { if (e.key === "Enter" && query.trim()) searchMutation.mutate(); }}
            />
            <div className="flex flex-wrap gap-2">
              <Button disabled={!query.trim() || searchMutation.isPending} loading={searchMutation.isPending} onClick={() => searchMutation.mutate()}>
                <Search className="h-4 w-4" />{m.search}
              </Button>
              {(query || results.length > 0) && <Button variant="secondary" onClick={clearSearch}>{m.clear}</Button>}
            </div>
            {searchMessage && <p role="status" className="text-sm text-gray-600">{searchMessage}</p>}
            {searchError && (
              <div role="alert" className="space-y-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm">
                <p className="text-red-700">{searchError}</p>
                <Button variant="secondary" onClick={() => searchMutation.mutate()} disabled={!query.trim()}>{m.retry}</Button>
              </div>
            )}
            {!searchMutation.isPending && !searchError && results.length === 0 && searchMessage === m.noResults && (
              <EmptyState icon={Search} title={m.noResults} description={m.noResultsDescription} />
            )}
            <div className="space-y-3">
              {results.map((r) => (
                <div key={r.chunk_id} className="rounded-lg border border-gray-200 bg-white p-4">
                  <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-gray-500">
                    <Badge>{r.filename}</Badge><span>{m.chunk} #{r.chunk_index}</span><span>{m.score} {r.score.toFixed(3)}</span>
                  </div>
                  <p className="whitespace-pre-wrap text-sm leading-6 text-gray-800">{r.content}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
