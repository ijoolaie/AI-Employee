"use client";

import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { listEmployees, setEmployeeStatus, getErrorMessage } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bot, Plus } from "lucide-react";
import { useI18n } from "@/lib/i18n/provider";
import Link from "next/link";

export default function EmployeesPage() {
  const { t } = useI18n();
  const tx = t.employee;\n  const qc = useQueryClient();\n  const status = useMutation({ mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) => setEmployeeStatus(id, is_active), onSuccess: () => void qc.invalidateQueries({ queryKey: ["employees"] }) });
  const { data, isLoading, error } = useQuery({
    queryKey: ["employees"],
    queryFn: listEmployees,
  });

  const employees = data ?? [];

  return (
    <>
      <Header
        title={tx.title}
        description={tx.description}
        actions={
          <Link href="/employees/new">
            <Button size="sm">
              <Plus className="h-4 w-4" />
              {tx.newEmployee}
            </Button>
          </Link>
        }
      />
      <div className="p-6">
        {isLoading && <Spinner />}
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {getErrorMessage(error)}
          </div>
        )}
        {!isLoading && !error && employees.length === 0 && (
          <EmptyState
            icon={Bot}
            title={tx.noEmployees}
            description={tx.noEmployeesDescription}
            action={
              <Link href="/employees/new">
                <Button size="sm">
                  <Plus className="h-4 w-4" />
                  {tx.createEmployee}
                </Button>
              </Link>
            }
          />
        )}
        {!isLoading && employees.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {employees.map((emp) => (
              <div key={emp.id} className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
                <Link href={`/employees/${emp.id}`} className="group block">
                  <div className="flex items-start justify-between">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-50">
                      <Bot className="h-5 w-5 text-brand-600" />
                    </div>
                    <Badge status={emp.is_active ? "active" : "inactive"} />
                  </div>
                  <h3 className="mt-3 font-semibold text-gray-900 group-hover:text-brand-700">{emp.name}</h3>
                  <p className="mt-0.5 text-sm text-gray-500">
                    <code className="rounded bg-gray-100 px-1.5 py-0.5 text-xs">{emp.slug}</code>
                    <span className="mx-1.5 text-gray-300">·</span>{emp.kind}
                  </p>
                  <p className="mt-3 text-xs text-gray-400">{tx.created} {formatDate(emp.created_at)}</p>
                </Link>
                <Button size="sm" variant="outline" className="mt-4 w-full" loading={status.isPending} disabled={status.isPending} onClick={() => status.mutate({ id: emp.id, is_active: !emp.is_active })}>
                  {emp.is_active ? tx.disable : tx.enable}
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
