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
import {
  getErrorMessage,
  indexKnowledgeFile,
  listFiles,
  searchKnowledge,
} from "@/lib/api";
import { FileText } from "lucide-react";
import type { KnowledgeSearchResult } from "@/types";

export default function KnowledgePage() {
  const qc = useQueryClient();
  const [selectedFileId, setSelectedFileId] = useState("");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<KnowledgeSearchResult[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const filesQuery = useQuery({
    queryKey: ["files"],
    queryFn: listFiles,
  });

  const files = useMemo(() => filesQuery.data ?? [], [filesQuery.data]);

  const indexMutation = useMutation({
    mutationFn: () => indexKnowledgeFile(selectedFileId),
    onSuccess: (doc) => {
      setError(null);
      setMessage(
        `Indexed file → document ${doc.id} (status: ${doc.status}, chunks: ${doc.chunk_count})`
      );
      qc.invalidateQueries({ queryKey: ["files"] });
    },
    onError: (err) => {
      setMessage(null);
      setError(getErrorMessage(err));
    },
  });

  const searchMutation = useMutation({
    mutationFn: () => searchKnowledge(query.trim(), 8),
    onSuccess: (data) => {
      setError(null);
      setResults(data);
      if (data.length === 0) setMessage("No matching chunks found.");
      else setMessage(`Found ${data.length} chunk(s).`);
    },
    onError: (err) => {
      setResults([]);
      setMessage(null);
      setError(getErrorMessage(err));
    },
  });

  return (
    <>
      <Header
        title="Knowledge"
        description="Index uploaded files into the tenant RAG store and search chunks"
      />
      <div className="mx-auto max-w-5xl space-y-6 p-6">
        <Card>
          <CardHeader>
            <CardTitle>Index a file</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {filesQuery.isLoading ? (
              <Spinner />
            ) : files.length === 0 ? (
              <EmptyState
                icon={FileText}
                title="No files yet"
                description="Upload a file on the Files page, then index it here for RAG."
              />
            ) : (
              <>
                <label className="block text-sm font-medium text-gray-700">
                  File
                  <select
                    className="mt-1.5 flex h-10 w-full rounded-lg border border-gray-300 bg-white px-3 text-sm"
                    value={selectedFileId}
                    onChange={(e) => setSelectedFileId(e.target.value)}
                  >
                    <option value="">Select a file…</option>
                    {files.map((f) => (
                      <option key={f.id} value={f.id}>
                        {f.filename} ({f.status})
                      </option>
                    ))}
                  </select>
                </label>
                <Button
                  disabled={!selectedFileId || indexMutation.isPending}
                  onClick={() => indexMutation.mutate()}
                >
                  {indexMutation.isPending ? "Indexing…" : "Index for RAG"}
                </Button>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Search knowledge</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label="Query"
              placeholder="What should we retrieve?"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <Button
              disabled={query.trim().length < 1 || searchMutation.isPending}
              onClick={() => searchMutation.mutate()}
            >
              {searchMutation.isPending ? "Searching…" : "Search"}
            </Button>

            {message && (
              <p className="text-sm text-gray-600">{message}</p>
            )}
            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {error}
              </div>
            )}

            <div className="space-y-3">
              {results.map((r) => (
                <div
                  key={r.chunk_id}
                  className="rounded-lg border border-gray-200 bg-white p-4"
                >
                  <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-gray-500">
                    <Badge>{r.filename}</Badge>
                    <span>chunk #{r.chunk_index}</span>
                    <span>score {r.score.toFixed(3)}</span>
                  </div>
                  <p className="whitespace-pre-wrap text-sm text-gray-800">
                    {r.content}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
