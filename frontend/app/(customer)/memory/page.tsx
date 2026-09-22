"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { createMemory, deleteMemory, getErrorMessage, listEmployees, searchMemory } from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";
import { Bot, Search } from "lucide-react";
import type { MemorySearchResult } from "@/types";

const MEMORY_TYPES = ["fact", "preference", "instruction", "summary"] as const;

function isPermissionError(error: unknown) {
  const message = getErrorMessage(error).toLowerCase();
  return message.includes("permission") || message.includes("403") || message.includes("forbidden");
}

export default function MemoryPage() {
  const { t: m } = useI18n();
  const [employeeId, setEmployeeId] = useState("");
  const [content, setContent] = useState("");
  const [memoryType, setMemoryType] = useState<(typeof MEMORY_TYPES)[number]>("fact");
  const [importance, setImportance] = useState(3);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<MemorySearchResult[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [permissionDenied, setPermissionDenied] = useState(false);

  const employeesQuery = useQuery({
    queryKey: ["employees"],
    queryFn: listEmployees,
  });

  const employees = useMemo(() => employeesQuery.data ?? [], [employeesQuery.data]);

  const createMutation = useMutation({
    mutationFn: () =>
      createMemory({
        employee_id: employeeId,
        content: content.trim(),
        memory_type: memoryType,
        importance,
      }),
    onSuccess: (memory) => {
      setError(null);
      setPermissionDenied(false);
      setMessage(m.memory.createSuccess.replace("{id}", memory.id).replace("{type}", memory.memory_type));
      setContent("");
    },
    onError: (err) => {
      setMessage(null);
      setPermissionDenied(isPermissionError(err));
      setError(getErrorMessage(err));
    },
  });

  const searchMutation = useMutation({
    mutationFn: () =>
      searchMemory({
        employee_id: employeeId,
        query: query.trim(),
        top_k: 8,
      }),
    onSuccess: (data) => {
      setError(null);
      setPermissionDenied(false);
      setResults(data);
      setMessage(m.memory.searchSuccess.replace("{count}", String(data.length)));
    },
    onError: (err) => {
      setResults([]);
      setMessage(null);
      setPermissionDenied(isPermissionError(err));
      setError(getErrorMessage(err));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteMemory(id),
    onSuccess: (_data, id) => {
      setResults((prev) => prev.filter((item) => item.id !== id));
      setError(null);
      setPermissionDenied(false);
      setMessage(m.memory.deleteSuccess.replace("{id}", id));
    },
    onError: (err) => {
      setPermissionDenied(isPermissionError(err));
      setError(getErrorMessage(err));
    },
  });

  const employeeLoadError = employeesQuery.isError;
  const canCreate = Boolean(employeeId && content.trim().length >= 1 && content.trim().length <= 8000);
  const canSearch = Boolean(employeeId && query.trim().length >= 1 && query.trim().length <= 4000);

  return (
    <>
      <Header title={m.memory.title} description={m.memory.description} />
      <div className="mx-auto max-w-5xl space-y-6 p-4 sm:p-6" dir="auto">
        {permissionDenied ? (
          <EmptyState icon={Bot} title={m.memory.permissionDenied} description={m.memory.permissionDescription} />
        ) : null}

        <Card>
          <CardHeader>
            <CardTitle>{m.memory.employeeScope}</CardTitle>
          </CardHeader>
          <CardContent>
            {employeesQuery.isLoading ? (
              <div className="flex items-center gap-2"><Spinner /><span>{m.memory.loading}</span></div>
            ) : employeeLoadError ? (
              <div className="space-y-3">
                <p className="text-sm text-red-600">{getErrorMessage(employeesQuery.error)}</p>
                <Button variant="outline" onClick={() => employeesQuery.refetch()}>{m.memory.retry}</Button>
              </div>
            ) : employees.length === 0 ? (
              <EmptyState icon={Bot} title={m.memory.noEmployees} description={m.memory.noEmployeesDescription} />
            ) : (
              <label className="block text-sm font-medium">
                {m.memory.employee}
                <select
                  aria-label={m.memory.employee}
                  className="mt-1.5 flex h-10 w-full rounded-lg border border-gray-300 bg-white px-3 text-sm"
                  value={employeeId}
                  onChange={(event) => {
                    setEmployeeId(event.target.value);
                    setResults([]);
                    setMessage(null);
                    setError(null);
                  }}
                >
                  <option value="">{m.memory.selectEmployee}</option>
                  {employees.map((employee) => (
                    <option key={employee.id} value={employee.id}>{employee.name} ({employee.slug})</option>
                  ))}
                </select>
              </label>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>{m.memory.createTitle}</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <Input
              label={m.memory.content}
              placeholder={m.memory.contentPlaceholder}
              value={content}
              onChange={(event) => setContent(event.target.value)}
              maxLength={8000}
            />
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block text-sm font-medium">
                {m.memory.type}
                <select
                  className="mt-1.5 flex h-10 w-full rounded-lg border border-gray-300 bg-white px-3 text-sm"
                  value={memoryType}
                  onChange={(event) => setMemoryType(event.target.value as (typeof MEMORY_TYPES)[number])}
                >
                  {MEMORY_TYPES.map((type) => <option key={type} value={type}>{m.memory.types[type]}</option>)}
                </select>
              </label>
              <label className="block text-sm font-medium">
                {m.memory.importance}
                <input
                  type="number"
                  min={1}
                  max={5}
                  className="mt-1.5 flex h-10 w-full rounded-lg border border-gray-300 bg-white px-3 text-sm"
                  value={importance}
                  onChange={(event) => setImportance(Math.min(5, Math.max(1, Number(event.target.value) || 1)))}
                />
              </label>
            </div>
            <Button disabled={!canCreate || createMutation.isPending} onClick={() => createMutation.mutate()}>
              {createMutation.isPending ? m.memory.saving : m.memory.save}
            </Button>
            {content.trim().length > 8000 ? <p className="text-sm text-red-600">{m.memory.contentTooLong}</p> : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>{m.memory.searchTitle}</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-col gap-2 sm:flex-row">
              <Input
                className="flex-1"
                label={m.memory.query}
                placeholder={m.memory.queryPlaceholder}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                maxLength={4000}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && canSearch && !searchMutation.isPending) searchMutation.mutate();
                }}
              />
              <Button disabled={!canSearch || searchMutation.isPending} onClick={() => searchMutation.mutate()}>
                <Search className="me-2 h-4 w-4" />
                {searchMutation.isPending ? m.memory.searching : m.memory.search}
              </Button>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {message ? <p className="text-sm text-gray-600">{message}</p> : null}
              {error ? <p className="text-sm text-red-600">{error}</p> : null}
            </div>

            {searchMutation.isSuccess && results.length === 0 ? (
              <EmptyState icon={Search} title={m.memory.noResults} description={m.memory.noResultsDescription} />
            ) : results.length > 0 ? (
              <div className="space-y-3">
                {results.map((result) => (
                  <div key={result.id} className="rounded-lg border border-gray-200 bg-white p-4">
                    <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-gray-500">
                      <Badge>{m.memory.types[result.memory_type as keyof typeof m.memory.types] ?? result.memory_type}</Badge>
                      <span>{m.memory.importanceValue.replace("{value}", String(result.importance))}</span>
                      <span>{m.memory.scoreValue.replace("{value}", result.score.toFixed(3))}</span>
                      <span>{m.memory.versionValue.replace("{value}", String(result.version))}</span>
                      <Button
                        variant="ghost"
                        className="ms-auto h-7 px-2 text-xs text-red-600"
                        disabled={deleteMutation.isPending}
                        onClick={() => {
                          if (window.confirm(m.memory.confirmDelete)) deleteMutation.mutate(result.id);
                        }}
                      >
                        {deleteMutation.isPending ? m.memory.deleting : m.memory.delete}
                      </Button>
                    </div>
                    <p className="whitespace-pre-wrap text-sm text-gray-800">{result.content}</p>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState icon={Search} title={m.memory.searchEmptyTitle} description={m.memory.searchEmptyDescription} />
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
