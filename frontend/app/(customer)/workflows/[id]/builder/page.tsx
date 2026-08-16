"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  Check,
  Copy,
  GripVertical,
  Plus,
  Save,
  Trash2,
  X,
} from "lucide-react";

import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  createWorkflowVersion,
  getErrorMessage,
  getWorkflow,
  listEmployees,
  listWorkflowVersions,
} from "@/lib/api";

import type {
  Employee,
  WorkflowStepDefinition,
  WorkflowStepType,
  WorkflowVersion,
} from "@/types";

const palette: Array<{
  type: WorkflowStepType;
  label: string;
  hint: string;
}> = [
  {
    type: "employee",
    label: "Employee",
    hint: "Run an AI employee",
  },
  {
    type: "condition",
    label: "Condition",
    hint: "Branch on context",
  },
  {
    type: "approval",
    label: "Approval",
    hint: "Pause for a human decision",
  },
  {
    type: "parallel",
    label: "Parallel",
    hint: "Fan out into branches",
  },
];

function makeStep(
  type: WorkflowStepType,
  index: number
): WorkflowStepDefinition {
  const step: WorkflowStepDefinition = {
    key: `${type}_${index + 1}`,
    type,
    retry_max: 0,
    timeout_seconds: 86400,
    metadata: {},
  };

  if (type === "parallel") {
    step.branches = [
      {
        key: "branch_1",
        steps: [
          {
            key: "branch_step_1",
            type: "condition",
          },
        ],
      },
    ];
  }

  if (type === "condition") {
    step.condition_value = true;
  }

  return step;
}

function cloneStep(step: WorkflowStepDefinition) {
  return JSON.parse(JSON.stringify(step)) as WorkflowStepDefinition;
}

export default function WorkflowBuilderPage() {
  const params = useParams<{ id: string }>();

  const [draft, setDraft] = useState<WorkflowStepDefinition[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [triggerType, setTriggerType] = useState<
    "manual" | "schedule" | "event"
  >("manual");
  const [activate, setActivate] = useState(true);
  const [dragIndex, setDragIndex] = useState<number | null>(null);

  const workflowQ = useQuery({
    queryKey: ["workflow", params.id],
    queryFn: () => getWorkflow(params.id),
  });

  const versionsQ = useQuery({
    queryKey: ["workflow-versions", params.id],
    queryFn: () => listWorkflowVersions(params.id),
  });

  const employeesQ = useQuery({
    queryKey: ["employees"],
    queryFn: listEmployees,
  });

  const employees = useMemo<Employee[]>(
    () => employeesQ.data ?? [],
    [employeesQ.data]
  );

  const activeEmployees = useMemo(
    () => employees.filter((employee) => employee.is_active),
    [employees]
  );

  const employeeMap = useMemo(() => {
    return new Map(employees.map((employee) => [employee.id, employee]));
  }, [employees]);

  const current = useMemo(
    () =>
      versionsQ.data?.find((v) => v.is_current) ??
      versionsQ.data?.[0] ??
      null,
    [versionsQ.data]
  );

  const currentSteps = () =>
    current
      ? (
          (current.config?.steps ??
            current.execution_contract?.steps ??
            []) as WorkflowStepDefinition[]
        ).map(cloneStep)
      : [];

  const loadCurrent = () => {
    if (!current || draft.length) return;

    setDraft(currentSteps());

    setTriggerType(
      (current.trigger_type as "manual" | "schedule" | "event") || "manual"
    );
  };

  const validationErrors = useMemo(() => {
    const errors: string[] = [];

    draft.forEach((step, index) => {
      if (!step.key?.trim()) {
        errors.push(`Step ${index + 1}: step key is required.`);
      }

      if (step.type === "employee" && !step.employee_id) {
        errors.push(
          `Step ${index + 1} (${step.key || "employee"}): select an employee.`
        );
      }

      if (
        step.type === "employee" &&
        step.employee_id &&
        !employeeMap.has(step.employee_id)
      ) {
        errors.push(
          `Step ${index + 1} (${step.key}): selected employee is not available.`
        );
      }
    });

    return errors;
  }, [draft, employeeMap]);

  const saveM = useMutation({
    mutationFn: () =>
      createWorkflowVersion(params.id, {
        steps: draft,
        trigger_type: triggerType,
        activate,
      }),

    onSuccess: () => {
      versionsQ.refetch();
      setSelected(null);
    },
  });

  const addStep = (type: WorkflowStepType) => {
    const base = draft.length ? draft : currentSteps();

    if (!draft.length) {
      setDraft(base);

      setTriggerType(
        (current?.trigger_type as "manual" | "schedule" | "event") || "manual"
      );
    }

    const index = base.length;
    const nextStep = makeStep(type, index);

    setDraft([...base, nextStep]);
    setSelected(index);
  };

  const updateSelected = (
    patch: Partial<WorkflowStepDefinition>
  ) => {
    if (selected === null) return;

    setDraft((prev) =>
      prev.map((step, index) =>
        index === selected
          ? {
              ...step,
              ...patch,
            }
          : step
      )
    );
  };

  const move = (from: number, to: number) => {
    if (
      from === to ||
      to < 0 ||
      to >= draft.length
    ) {
      return;
    }

    setDraft((prev) => {
      const next = [...prev];
      const [item] = next.splice(from, 1);

      next.splice(to, 0, item);

      return next;
    });

    setSelected(to);
  };

  const duplicate = (index: number) => {
    const copy = cloneStep(draft[index]);

    copy.key = `${copy.key}_copy`;

    setDraft((prev) => [
      ...prev.slice(0, index + 1),
      copy,
      ...prev.slice(index + 1),
    ]);

    setSelected(index + 1);
  };

  const remove = (index: number) => {
    setDraft((prev) =>
      prev.filter((_, currentIndex) => currentIndex !== index)
    );

    setSelected((current) => {
      if (current === null) return null;

      if (current === index) return null;

      if (current > index) return current - 1;

      return current;
    });
  };

  const active =
    selected === null ? null : draft[selected];

  const isLoading =
    workflowQ.isLoading ||
    versionsQ.isLoading ||
    employeesQ.isLoading;

  if (isLoading) {
    return (
      <>
        <Header title="Workflow Builder" />

        <div className="p-6 text-sm text-gray-500">
          Loading workflow...
        </div>
      </>
    );
  }

  if (
    workflowQ.error ||
    versionsQ.error ||
    employeesQ.error
  ) {
    return (
      <>
        <Header title="Workflow Builder" />

        <div className="p-6">
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {getErrorMessage(
              workflowQ.error ??
                versionsQ.error ??
                employeesQ.error ??
                new Error("Unable to load workflow builder data.")
            )}
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Header
        title="Visual Workflow Builder"
        description={
          workflowQ.data?.name ??
          "Design a versioned workflow"
        }
      />

      <div className="space-y-4 p-6">

        {/* Top toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-3">

          <Link
            href={`/workflows/${params.id}`}
            className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to workflow
          </Link>

          <div className="flex flex-wrap items-center gap-2">

            <label className="text-xs text-gray-500">
              Trigger
            </label>

            <select
              value={triggerType}
              onChange={(event) =>
                setTriggerType(
                  event.target.value as typeof triggerType
                )
              }
              className="h-10 rounded-lg border border-gray-300 bg-white px-3 text-sm"
            >
              <option value="manual">
                Manual
              </option>

              <option value="schedule">
                Schedule
              </option>

              <option value="event">
                Event/Webhook
              </option>
            </select>

            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={activate}
                onChange={(event) =>
                  setActivate(event.target.checked)
                }
              />

              Activate
            </label>

            <Button
              onClick={() => saveM.mutate()}
              loading={saveM.isPending}
              disabled={
                !draft.length ||
                validationErrors.length > 0
              }
            >
              <Save className="h-4 w-4" />
              Save new version
            </Button>
          </div>
        </div>

        {/* Validation */}
        {validationErrors.length > 0 && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
            <div className="font-semibold">
              Workflow needs attention
            </div>

            <ul className="mt-2 list-disc space-y-1 pl-5">
              {validationErrors.map((error) => (
                <li key={error}>
                  {error}
                </li>
              ))}
            </ul>
          </div>
        )}

        {activeEmployees.length === 0 && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
            No active AI Employees are available.
            Create or activate an Employee before adding
            an Employee node to this workflow.
          </div>
        )}

        {saveM.error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {getErrorMessage(saveM.error)}
          </div>
        )}

        {saveM.isSuccess && (
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
            <Check className="mr-2 inline h-4 w-4" />
            New immutable workflow version created.
          </div>
        )}

        <div className="grid min-h-[620px] grid-cols-12 gap-4">

          {/* Node palette */}
          <Card className="col-span-12 lg:col-span-3">
            <CardHeader>
              <CardTitle>
                Nodes
              </CardTitle>
            </CardHeader>

            <CardContent className="space-y-2">

              {palette.map((item) => (
                <button
                  key={item.type}
                  onClick={() => addStep(item.type)}
                  disabled={
                    item.type === "employee" &&
                    activeEmployees.length === 0
                  }
                  className="w-full rounded-xl border border-gray-200 bg-white p-3 text-left hover:border-brand-400 hover:bg-brand-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <div className="flex items-center gap-2 font-medium">
                    <Plus className="h-4 w-4 text-brand-600" />

                    {item.label}
                  </div>

                  <p className="mt-1 text-xs text-gray-500">
                    {item.hint}
                  </p>
                </button>
              ))}

              <div className="mt-4 rounded-xl bg-gray-50 p-3 text-xs text-gray-500">
                Drag nodes to reorder the execution path.
                Every save creates an immutable backend
                version.
              </div>
            </CardContent>
          </Card>

          {/* Canvas */}
          <Card className="col-span-12 lg:col-span-6">
            <CardHeader>
              <CardTitle>
                Execution canvas
              </CardTitle>
            </CardHeader>

            <CardContent className="space-y-2">

              {!draft.length && (
                <button
                  onClick={loadCurrent}
                  className="w-full rounded-xl border border-dashed border-gray-300 p-10 text-center text-sm text-gray-500 hover:bg-gray-50"
                >
                  {current
                    ? "Load current version into the canvas"
                    : "Add a node to start building"}
                </button>
              )}

              {draft.map((step, index) => {
                const employee =
                  step.employee_id
                    ? employeeMap.get(step.employee_id)
                    : undefined;

                return (
                  <div
                    key={`${step.key}-${index}`}
                    draggable
                    onDragStart={() =>
                      setDragIndex(index)
                    }
                    onDragOver={(event) =>
                      event.preventDefault()
                    }
                    onDrop={() => {
                      if (dragIndex !== null) {
                        move(
                          dragIndex,
                          index
                        );
                      }

                      setDragIndex(null);
                    }}
                    onClick={() =>
                      setSelected(index)
                    }
                    className={`cursor-pointer rounded-xl border p-3 ${
                      selected === index
                        ? "border-brand-500 bg-brand-50"
                        : "border-gray-200 bg-white"
                    }`}
                  >
                    <div className="flex items-center gap-3">

                      <GripVertical className="h-4 w-4 text-gray-400" />

                      <div className="min-w-0 flex-1">

                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold uppercase text-brand-700">
                            {step.type}
                          </span>

                          <span className="truncate font-medium">
                            {step.key}
                          </span>
                        </div>

                        <p className="text-xs text-gray-500">
                          {step.type === "employee"
                            ? employee
                              ? employee.name
                              : "Select an employee"
                            : step.type === "parallel"
                              ? `${step.branches?.length ?? 0} branch(es)`
                              : step.type === "approval"
                                ? step.message ||
                                  "Human approval"
                                : "Context condition"}
                        </p>
                      </div>

                      <div className="flex items-center gap-1">

                        <button
                          title="Duplicate"
                          onClick={(event) => {
                            event.stopPropagation();
                            duplicate(index);
                          }}
                          className="rounded p-1.5 hover:bg-gray-100"
                        >
                          <Copy className="h-4 w-4" />
                        </button>

                        <button
                          title="Move up"
                          onClick={(event) => {
                            event.stopPropagation();
                            move(
                              index,
                              index - 1
                            );
                          }}
                          className="rounded p-1.5 hover:bg-gray-100"
                        >
                          ↑
                        </button>

                        <button
                          title="Move down"
                          onClick={(event) => {
                            event.stopPropagation();
                            move(
                              index,
                              index + 1
                            );
                          }}
                          className="rounded p-1.5 hover:bg-gray-100"
                        >
                          ↓
                        </button>

                        <button
                          title="Delete"
                          onClick={(event) => {
                            event.stopPropagation();
                            remove(index);
                          }}
                          className="rounded p-1.5 text-red-600 hover:bg-red-50"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>

                      </div>
                    </div>

                    {index <
                      draft.length - 1 && (
                      <div className="ml-7 mt-2 h-3 border-l border-dashed border-gray-300" />
                    )}
                  </div>
                );
              })}
            </CardContent>
          </Card>

          {/* Properties */}
          <Card className="col-span-12 lg:col-span-3">
            <CardHeader>
              <CardTitle>
                Properties
              </CardTitle>
            </CardHeader>

            <CardContent>

              {active ? (
                <div className="space-y-4">

                  {/* Key */}
                  <div>
                    <label className="text-xs font-medium text-gray-600">
                      Step key
                    </label>

                    <Input
                      value={active.key}
                      onChange={(event) =>
                        updateSelected({
                          key: event.target.value,
                        })
                      }
                    />
                  </div>

                  {/* Type */}
                  <div>
                    <label className="text-xs font-medium text-gray-600">
                      Type
                    </label>

                    <div className="mt-1 rounded-lg bg-gray-50 px-3 py-2 text-sm font-medium">
                      {active.type}
                    </div>
                  </div>

                  {/* Employee */}
                  {active.type === "employee" && (
                    <div>
                      <label className="text-xs font-medium text-gray-600">
                        AI Employee
                      </label>

                      <select
                        value={
                          active.employee_id ?? ""
                        }
                        onChange={(event) =>
                          updateSelected({
                            employee_id:
                              event.target.value ||
                              null,
                          })
                        }
                        className="mt-1 h-10 w-full rounded-lg border border-gray-300 bg-white px-3 text-sm"
                      >
                        <option value="">
                          Select an employee...
                        </option>

                        {activeEmployees.map(
                          (employee) => (
                            <option
                              key={employee.id}
                              value={employee.id}
                            >
                              {employee.name}{" "}
                              ({employee.slug})
                            </option>
                          )
                        )}
                      </select>

                      {active.employee_id &&
                        employeeMap.has(
                          active.employee_id
                        ) && (
                          <div className="mt-2 rounded-lg bg-emerald-50 p-2 text-xs text-emerald-700">
                            Selected:{" "}
                            {
                              employeeMap.get(
                                active.employee_id
                              )?.name
                            }
                          </div>
                        )}

                      {!active.employee_id && (
                        <div className="mt-2 rounded-lg bg-amber-50 p-2 text-xs text-amber-700">
                          An AI Employee is required
                          before this workflow can
                          be saved.
                        </div>
                      )}
                    </div>
                  )}

                  {/* Approval */}
                  {active.type === "approval" && (
                    <div>
                      <label className="text-xs font-medium text-gray-600">
                        Message
                      </label>

                      <textarea
                        value={
                          active.message ?? ""
                        }
                        onChange={(event) =>
                          updateSelected({
                            message:
                              event.target.value,
                          })
                        }
                        className="mt-1 min-h-24 w-full rounded-lg border border-gray-300 p-3"
                        placeholder="What should the approver decide?"
                      />
                    </div>
                  )}

                  {/* Condition */}
                  {active.type === "condition" && (
                    <div>
                      <label className="text-xs font-medium text-gray-600">
                        Condition reference
                      </label>

                      <Input
                        value={
                          active.condition_ref ??
                          ""
                        }
                        onChange={(event) =>
                          updateSelected({
                            condition_ref:
                              event.target.value ||
                              null,
                          })
                        }
                        placeholder="context.field"
                      />

                      <label className="mt-3 flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={
                            active.condition_value !==
                            false
                          }
                          onChange={(event) =>
                            updateSelected({
                              condition_value:
                                event.target.checked,
                            })
                          }
                        />

                        Expected truthy
                      </label>
                    </div>
                  )}

                  {/* Retry */}
                  <div>
                    <label className="text-xs font-medium text-gray-600">
                      Retry attempts
                    </label>

                    <Input
                      type="number"
                      min={0}
                      max={5}
                      value={
                        active.retry_max ?? 0
                      }
                      onChange={(event) =>
                        updateSelected({
                          retry_max:
                            Number(
                              event.target.value
                            ),
                        })
                      }
                    />
                  </div>

                  {/* Timeout */}
                  <div>
                    <label className="text-xs font-medium text-gray-600">
                      Timeout (seconds)
                    </label>

                    <Input
                      type="number"
                      min={1}
                      value={
                        active.timeout_seconds ??
                        86400
                      }
                      onChange={(event) =>
                        updateSelected({
                          timeout_seconds:
                            Number(
                              event.target.value
                            ),
                        })
                      }
                    />
                  </div>

                  {/* Parallel */}
                  {active.type === "parallel" && (
                    <div className="rounded-lg border border-gray-200 p-3 text-xs text-gray-600">
                      <div className="font-semibold text-gray-900">
                        Parallel branches
                      </div>

                      <div className="mt-2 space-y-1">
                        {(active.branches ?? []).map(
                          (branch) => (
                            <div
                              key={branch.key}
                              className="flex justify-between"
                            >
                              <span>
                                {branch.key}
                              </span>

                              <span>
                                {
                                  branch.steps
                                    .length
                                }{" "}
                                step(s)
                              </span>
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  )}

                  <Button
                    variant="ghost"
                    className="w-full"
                    onClick={() =>
                      setSelected(null)
                    }
                  >
                    <X className="h-4 w-4" />
                    Close
                  </Button>

                </div>
              ) : (
                <div className="py-10 text-center text-sm text-gray-500">
                  Select a node to edit its properties.
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Version history */}
        <Card>
          <CardHeader>
            <CardTitle>
              Version history
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-2">
            {versionsQ.data?.map(
              (version: WorkflowVersion) => (
                <div
                  key={version.id}
                  className="flex items-center justify-between rounded-lg border border-gray-200 px-4 py-3 text-sm"
                >
                  <div>
                    <span className="font-medium">
                      Version{" "}
                      {version.version_number}
                    </span>

                    <span className="ml-3 text-gray-500">
                      {version.content_hash?.slice(
                        0,
                        12
                      ) ?? "no hash"}
                    </span>
                  </div>

                  {version.is_current && (
                    <span className="rounded-full bg-emerald-100 px-2 py-1 text-xs text-emerald-700">
                      Current
                    </span>
                  )}
                </div>
              )
            )}
          </CardContent>
        </Card>

      </div>
    </>
  );
}