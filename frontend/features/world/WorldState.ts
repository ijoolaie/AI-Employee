import type { CustomerOffice, CustomerOfficeEmployee, OfficePresentationState } from "@/types";

export type WorldEmployeeState = Extract<
  OfficePresentationState,
  "WORKING" | "WAITING_APPROVAL" | "IDLE" | "BLOCKED" | "ESCALATED" | "COMPLETED"
>;

export type WorldDepartmentId = "command" | "sales" | "support" | "operations" | "engineering";

export interface WorldDepartment {
  id: WorldDepartmentId;
  label: string;
  description: string;
  col: number;
  row: number;
}

export interface WorldEmployee {
  id: string;
  name: string;
  slug: string;
  kind: string;
  avatarUrl: string | null;
  state: WorldEmployeeState;
  currentWorkItem: CustomerOfficeEmployee["current_work_item"];
  latestRunId: string | null;
  latestRunStatus: string | null;
  latestRunCreatedAt: string | null;
  slot: number;
}

export interface WorldProgression {
  tier: string;
  activeEmployees: number;
  employeeLimit: number;
  activeWorkflows: number;
  workflowLimit: number;
  monthlyRuns: number;
  monthlyRunLimit: number;
  completionPercent: number;
}

export interface WorldReadModel {
  generatedAt: string;
  officeState: string;
  departments: WorldDepartment[];
  employees: WorldEmployee[];
  pendingApprovals: CustomerOffice["pending_approvals"];
  progression: WorldProgression;
}

export const WORLD_DEPARTMENTS: WorldDepartment[] = [
  { id: "command", label: "Command", description: "Executive and approval area", col: 2, row: 1 },
  { id: "sales", label: "Sales", description: "Customer and revenue operations", col: 6, row: 1 },
  { id: "support", label: "Customer Support", description: "Customer care operations", col: 7, row: 5 },
  { id: "operations", label: "Operations", description: "Workflow and delivery operations", col: 2, row: 5 },
  { id: "engineering", label: "Engineering", description: "Automation and platform capability", col: 5, row: 4 },
];

const WORLD_STATES = new Set<WorldEmployeeState>([
  "WORKING",
  "WAITING_APPROVAL",
  "IDLE",
  "BLOCKED",
  "ESCALATED",
  "COMPLETED",
]);

function normalizeState(value: string): WorldEmployeeState {
  return WORLD_STATES.has(value as WorldEmployeeState)
    ? (value as WorldEmployeeState)
    : "IDLE";
}

export function projectWorldReadModel(office: CustomerOffice): WorldReadModel {
  const employees = office.employees.map((employee, index) => ({
    id: employee.id,
    name: employee.name,
    slug: employee.slug,
    kind: employee.kind,
    avatarUrl: employee.avatar_url,
    state: normalizeState(employee.presentation_state),
    currentWorkItem: employee.current_work_item,
    latestRunId: employee.latest_run_id,
    latestRunStatus: employee.latest_run_status,
    latestRunCreatedAt: employee.latest_run_created_at,
    slot: index,
  }));

  const limits = [
    [office.hq_metrics.active_employees, office.hq_metrics.employee_limit],
    [office.hq_metrics.active_workflows, office.hq_metrics.workflow_limit],
    [office.hq_metrics.monthly_runs, office.hq_metrics.monthly_run_limit],
  ] as const;

  const completionPercent = Math.round(
    (limits.reduce((sum, [used, limit]) => sum + (limit > 0 ? Math.min(used / limit, 1) : 0), 0) / limits.length) * 100,
  );

  return {
    generatedAt: office.generated_at,
    officeState: office.office_state,
    departments: WORLD_DEPARTMENTS,
    employees,
    pendingApprovals: office.pending_approvals,
    progression: {
      tier: office.hq_tier,
      activeEmployees: office.hq_metrics.active_employees,
      employeeLimit: office.hq_metrics.employee_limit,
      activeWorkflows: office.hq_metrics.active_workflows,
      workflowLimit: office.hq_metrics.workflow_limit,
      monthlyRuns: office.hq_metrics.monthly_runs,
      monthlyRunLimit: office.hq_metrics.monthly_run_limit,
      completionPercent,
    },
  };
}
