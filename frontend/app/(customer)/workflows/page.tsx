"use client";

import Link from "next/link";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Workflow as WorkflowIcon } from "lucide-react";

import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { api, createWorkflow, getErrorMessage } from "@/lib/api";
import type { APIResponse, Workflow } from "@/types";

async function listWorkflows() {
  const res = await api.get<APIResponse<Workflow[]>>("/workflows");

  if (!res.data.success || !res.data.data) {
    throw new Error("Unable to load workflows");
  }

  return res.data.data;
}

function slugify(value: string) {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 100);
}

export default function WorkflowsPage() {
  const qc = useQueryClient();

  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [slugTouched, setSlugTouched] = useState(false);
  const [triggerType, setTriggerType] = useState<
    "manual" | "schedule" | "event"
  >("manual");
  const [maxRuntime, setMaxRuntime] = useState("");

  const q = useQuery({
    queryKey: ["workflows"],
    queryFn: listWorkflows,
  });

  const createM = useMutation({
    mutationFn: () =>
      createWorkflow({
        name: name.trim(),
        slug: slug.trim(),
        trigger_type: triggerType,
        max_runtime_seconds: maxRuntime
          ? Number(maxRuntime)
          : null,

        // Backend requires at least one step.
        // This temporary condition can be replaced in the Builder.
        steps: [
          {
            key: "initial_step",
            type: "condition",
            retry_max: 0,
            timeout_seconds: 86400,
            condition_ref: "context.ready",
            condition_value: true,
            metadata: {},
          },
        ],
      }),

    onSuccess: async (workflow) => {
      await qc.invalidateQueries({ queryKey: ["workflows"] });

      setShowCreate(false);
      setName("");
      setSlug("");
      setSlugTouched(false);
      setTriggerType("manual");
      setMaxRuntime("");

      window.location.href = `/workflows/${workflow.id}/builder`;
    },
  });

  const canCreate =
    name.trim().length >= 1 &&
    slug.trim().length >= 1 &&
    !createM.isPending;

  const handleNameChange = (value: string) => {
    setName(value);

    if (!slugTouched) {
      setSlug(slugify(value));
    }
  };

  const closeModal = () => {
    if (createM.isPending) return;

    setShowCreate(false);
    createM.reset();
  };

  return (
    <>
      <Header
        title="Workflows"
        description="Create, inspect and execute versioned workflows."
      />

      <div className="space-y-6 p-6">
        {/* Page actions */}
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Workflow catalog
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              Build automated processes using AI employees, conditions,
              approvals and parallel branches.
            </p>
          </div>

          <Button
            onClick={() => {
              createM.reset();
              setShowCreate(true);
            }}
          >
            <Plus className="h-4 w-4" />
            Create Workflow
          </Button>
        </div>

        {/* Loading */}
        {q.isLoading && (
          <Card>
            <CardContent className="flex justify-center py-12">
              <Spinner />
            </CardContent>
          </Card>
        )}

        {/* Error */}
        {q.error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {getErrorMessage(q.error)}
          </div>
        )}

        {/* Catalog */}
        {!q.isLoading && !q.error && (
          <Card>
            <CardContent className="p-0">
              {q.data?.length ? (
                <div className="overflow-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left text-xs uppercase text-gray-500">
                        <th className="px-5 py-3">Name</th>
                        <th className="px-5 py-3">Slug</th>
                        <th className="px-5 py-3">Status</th>
                        <th className="px-5 py-3">Version</th>
                        <th className="px-5 py-3">Builder</th>
                      </tr>
                    </thead>

                    <tbody>
                      {q.data.map((w) => (
                        <tr
                          key={w.id}
                          className="border-b hover:bg-gray-50"
                        >
                          <td className="px-5 py-3">
                            <Link
                              className="font-medium text-brand-600 hover:underline"
                              href={`/workflows/${w.id}`}
                            >
                              {w.name}
                            </Link>
                          </td>

                          <td className="px-5 py-3 text-gray-600">
                            {w.slug}
                          </td>

                          <td className="px-5 py-3">
                            {w.is_active ? "Active" : "Disabled"}
                          </td>

                          <td className="px-5 py-3 text-gray-600">
                            {w.current_version_id?.slice(0, 8) ?? "—"}
                          </td>

                          <td className="px-5 py-3">
                            <Link
                              className="text-brand-600 hover:underline"
                              href={`/workflows/${w.id}/builder`}
                            >
                              Open builder
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center px-5 py-16 text-center">
                  <div className="mb-4 rounded-2xl bg-gray-100 p-4">
                    <WorkflowIcon className="h-8 w-8 text-gray-500" />
                  </div>

                  <h3 className="text-base font-semibold text-gray-900">
                    No workflows yet
                  </h3>

                  <p className="mt-2 max-w-md text-sm text-gray-500">
                    Create your first workflow and start building an automated
                    execution process.
                  </p>

                  <Button
                    className="mt-5"
                    onClick={() => {
                      createM.reset();
                      setShowCreate(true);
                    }}
                  >
                    <Plus className="h-4 w-4" />
                    Create Workflow
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Create Workflow Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white shadow-2xl">
            <div className="border-b px-6 py-5">
              <h2 className="text-lg font-semibold text-gray-900">
                Create Workflow
              </h2>

              <p className="mt-1 text-sm text-gray-500">
                Create the workflow container, then design its execution path
                in the Visual Builder.
              </p>
            </div>

            <div className="space-y-5 px-6 py-6">
              {createM.error && (
                <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {getErrorMessage(createM.error)}
                </div>
              )}

              {/* Name */}
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">
                  Workflow name
                </label>

                <Input
                  value={name}
                  onChange={(e) => handleNameChange(e.target.value)}
                  placeholder="Customer Support Automation"
                  autoFocus
                />
              </div>

              {/* Slug */}
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">
                  Slug
                </label>

                <Input
                  value={slug}
                  onChange={(e) => {
                    setSlugTouched(true);
                    setSlug(slugify(e.target.value));
                  }}
                  placeholder="customer-support-automation"
                />

                <p className="mt-1 text-xs text-gray-500">
                  Used as the unique workflow identifier.
                </p>
              </div>

              {/* Trigger */}
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">
                  Trigger
                </label>

                <select
                  value={triggerType}
                  onChange={(e) =>
                    setTriggerType(
                      e.target.value as
                        | "manual"
                        | "schedule"
                        | "event"
                    )
                  }
                  className="h-10 w-full rounded-lg border border-gray-300 bg-white px-3 text-sm"
                >
                  <option value="manual">Manual</option>
                  <option value="schedule">Schedule</option>
                  <option value="event">Event / Webhook</option>
                </select>
              </div>

              {/* Max runtime */}
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">
                  Maximum runtime
                  <span className="ml-1 font-normal text-gray-400">
                    (optional, seconds)
                  </span>
                </label>

                <Input
                  type="number"
                  min={1}
                  max={2592000}
                  value={maxRuntime}
                  onChange={(e) => setMaxRuntime(e.target.value)}
                  placeholder="86400"
                />
              </div>
            </div>

            {/* Footer */}
            <div className="flex justify-end gap-3 border-t bg-gray-50 px-6 py-4">
              <Button
                variant="secondary"
                onClick={closeModal}
                disabled={createM.isPending}
              >
                Cancel
              </Button>

              <Button
                onClick={() => createM.mutate()}
                disabled={!canCreate}
                loading={createM.isPending}
              >
                Create Workflow
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}