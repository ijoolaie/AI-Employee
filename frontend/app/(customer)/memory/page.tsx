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
import {
  createMemory,
  deleteMemory,
  getErrorMessage,
  listEmployees,
  searchMemory,
} from "@/lib/api";
import { Bot } from "lucide-react";
import type { MemorySearchResult } from "@/types";

const MEMORY_TYPES = ["fact", "preference", "instruction", "summary"] as const;

export default function MemoryPage() {
  const [employeeId, setEmployeeId] = useState("");
  const [content, setContent] = useState("");
  const [memoryType, setMemoryType] = useState<string>("fact");
  const [importance, setImportance] = useState(3);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<MemorySearchResult[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const employeesQuery = useQuery({
    queryKey: ["employees"],
    queryFn: listEmployees,
  });
  const employees = useMemo(
    () => employeesQuery.data ?? [],
    [employeesQuery.data]
  );

  const createMutation = useMutation({
    mutationFn: () =>
      createMemory({
        employee_id: employeeId,
        content: content.trim(),
        memory_type: memoryType,
        importance,
      }),
    onSuccess: (mem) => {
      setError(null);
      setMessage(`Memory created: ${mem.id} (${mem.memory_type})`);
      setContent("");
    },
    onError: (err) => {
      setMessage(null);
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
      setResults(data);
      setMessage(
        data.length ? `Found ${data.length} memor(ies).` : "No memories matched."
      );
    },
    onError: (err) => {
      setResults([]);
      setMessage(null);
      setError(getErrorMessage(err));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteMemory(id),
    onSuccess: (_data, id) => {
      setResults((prev) => prev.filter((r) => r.id !== id));
      setMessage(`Deleted memory ${id}`);
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  return (
    <>
      <Header
        title="Memory"
        description="Create and search long-term memories scoped to an employee"
      />
      <div className="mx-auto max-w-5xl space-y-6 p-6">
        <Card>
          <CardHeader>
            <CardTitle>Employee scope</CardTitle>
          </CardHeader>
          <CardContent>
            {employeesQuery.isLoading ? (
              <Spinner />
            ) : employees.length === 0 ? (
              <EmptyState
                icon={Bot}
                title="No employees"
                description="Create or seed an employee first."
              />
            ) : (
              <label className="block text-sm font-medium text-gray-700">
                Employee
                <select
                  className="mt-1.5 flex h-10 w-full rounded-lg border border-gray-300 bg-white px-3 text-sm"
                  value={employeeId}
                  onChange={(e) => setEmployeeId(e.target.value)}
                >
                  <option value="">Select…</option>
                  {employees.map((e) => (
                    <option key={e.id} value={e.id}>
                      {e.name} ({e.slug})
                    </option>
                  ))}
                </select>
              </label>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Create memory</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label="Content"
              placeholder="Remember that the preferred report currency is IRR"
              value={content}
              onChange={(e) => setContent(e.target.value)}
            />
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block text-sm font-medium text-gray-700">
                Type
                <select
                  className="mt-1.5 flex h-10 w-full rounded-lg border border-gray-300 bg-white px-3 text-sm"
                  value={memoryType}
                  onChange={(e) => setMemoryType(e.target.value)}
                >
                  {MEMORY_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-sm font-medium text-gray-700">
                Importance (1–5)
                <input
                  type="number"
                  min={1}
                  max={5}
                  className="mt-1.5 flex h-10 w-full rounded-lg border border-gray-300 bg-white px-3 text-sm"
                  value={importance}
                  onChange={(e) => setImportance(Number(e.target.value) || 3)}
                />
              </label>
            </div>
            <Button
              disabled={
                !employeeId || content.trim().length < 1 || createMutation.isPending
              }
              onClick={() => createMutation.mutate()}
            >
              {createMutation.isPending ? "Saving…" : "Save memory"}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Search memories</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label="Query"
              placeholder="preferred currency"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <Button
              disabled={
                !employeeId || query.trim().length < 1 || searchMutation.isPending
              }
              onClick={() => searchMutation.mutate()}
            >
              {searchMutation.isPending ? "Searching…" : "Search"}
            </Button>

            {message && <p className="text-sm text-gray-600">{message}</p>}
            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {error}
              </div>
            )}

            <div className="space-y-3">
              {results.map((r) => (
                <div
                  key={r.id}
                  className="rounded-lg border border-gray-200 bg-white p-4"
                >
                  <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-gray-500">
                    <Badge>{r.memory_type}</Badge>
                    <span>importance {r.importance}</span>
                    <span>score {r.score.toFixed(3)}</span>
                    <span>v{r.version}</span>
                    <Button
                      variant="ghost"
                      className="ml-auto h-7 px-2 text-xs text-red-600"
                      disabled={deleteMutation.isPending}
                      onClick={() => deleteMutation.mutate(r.id)}
                    >
                      Delete
                    </Button>
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
