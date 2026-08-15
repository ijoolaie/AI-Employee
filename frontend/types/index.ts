/** Types aligned with backend Pydantic schemas (backend v0.2.0). */

export interface APIResponse<T> {
  success: boolean;
  data?: T;
  meta?: Record<string, unknown>;
}

export interface APIError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  tenant_id: string;
  is_active: boolean;
  is_platform_admin: boolean;
}

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  status: string;
}

export interface MeResponse {
  user: User;
  tenant: Tenant;
}

export interface RegisterRequest {
  tenant_name: string;
  tenant_slug: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  tenant_slug: string;
}

export interface Employee {
  id: string;
  slug: string;
  name: string;
  kind: string;
  is_active: boolean;
  created_at: string;
}

export interface EmployeeVersion {
  id: string;
  version_number: number;
  is_current: boolean;
  allowed_tools: string[];
  created_at: string;
}

export interface EmployeeCreate {
  slug: string;
  name: string;
  kind?: string;
  input_schema?: Record<string, unknown>;
  output_schema?: Record<string, unknown>;
  prompt_template?: string;
  allowed_tools?: string[];
  rules?: Record<string, unknown>;
}

export type RunStatus =
  | "pending"
  | "queued"
  | "running"
  | "success"
  | "failed"
  | "cancelled";

export interface Run {
  id: string;
  employee_id: string;
  employee_version_id: string;
  employee_name?: string | null;
  employee_slug?: string | null;
  status: RunStatus | string;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown> | null;
  error: Record<string, unknown> | null;
  total_tokens: number;
  total_cost_usd: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface RunCreate {
  employee_id: string;
  input_data?: Record<string, unknown>;
}

export interface FileItem {
  id: string;
  filename: string;
  content_type: string | null;
  size_bytes: number;
  status: string;
  created_at: string;
}

export interface TraceEvent {
  type: string;
  timestamp: string;
  action?: string;
  status?: string;
  provider?: string;
  model?: string;
  prompt_tokens?: number;
  completion_tokens?: number;
  cost_usd?: number;
  latency_ms?: number;
  prompt_version?: string | null;
  request_id?: string | null;
  metadata?: Record<string, unknown>;
  error_message?: string | null;
}

export interface RunTrace {
  run_id: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  total_tokens: number;
  total_cost_usd: number;
  events: TraceEvent[];
}

export interface UsageBreakdown {
  provider: string;
  model: string;
  calls: number;
  successful_calls: number;
  failed_calls: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
  avg_latency_ms: number;
}

export interface UsageSummary {
  from_at: string | null;
  to_at: string | null;
  calls: number;
  successful_calls: number;
  failed_calls: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
  avg_latency_ms: number;
  breakdown: UsageBreakdown[];
  notes: string[];
}


export interface ToolDefinition {
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
  side_effects: boolean;
}


export interface WorkflowApproval {
  id: string;
  workflow_run_id: string;
  workflow_step_run_id: string;
  step_key: string;
  status: "pending" | "approved" | "rejected" | "expired" | string;
  requested_by: string | null;
  decided_by: string | null;
  decision_reason: string | null;
  metadata: Record<string, unknown>;
  expires_at: string | null;
  decided_at: string | null;
  created_at: string;
}

export interface ToolApproval {
  id: string;
  run_id: string;
  tool_name: string;
  tool_call_id: string;
  arguments: Record<string, unknown>;
  status: "pending" | "approved" | "rejected" | "consumed";
  requested_by: string | null;
  decided_by: string | null;
  decision_reason: string | null;
  decided_at: string | null;
  created_at: string;
}

export type WorkflowStepType = "employee" | "condition" | "approval" | "parallel";
export interface WorkflowStepDefinition {
  key: string;
  type: WorkflowStepType;
  employee_id?: string | null;
  input_mapping?: Record<string, string>;
  output_key?: string | null;
  retry_max?: number;
  condition?: Record<string, unknown> | null;
  condition_value?: boolean;
  condition_ref?: string | null;
  timeout_seconds?: number;
  message?: string | null;
  metadata?: Record<string, unknown>;
  branches?: Array<{ key: string; steps: Record<string, unknown>[] }>;
}
export interface Workflow {
  id: string;
  slug: string;
  name: string;
  is_active: boolean;
  current_version_id: string | null;
  created_at: string;
}
export interface WorkflowRun {
  id: string;
  workflow_id: string;
  workflow_version_id: string;
  status: string;
  context: Record<string, unknown>;
  output_data: Record<string, unknown> | null;
  error: Record<string, unknown> | null;
  started_at: string | null;
  completed_at: string | null;
  deadline_at: string | null;
  cancelled_at: string | null;
  cancel_reason: string | null;
  created_at: string;
}

export interface WorkflowVersion {
  id: string;
  workflow_id: string;
  version_number: number;
  is_current: boolean;
  trigger_type: string;
  config: Record<string, unknown>;
  execution_contract: Record<string, unknown>;
  content_hash: string | null;
  created_by: string | null;
  created_at: string;
}

export interface WorkflowSchedule {
  id: string;
  workflow_id: string;
  cron_expression: string;
  timezone: string;
  is_active: boolean;
  next_run_at: string | null;
  last_run_at: string | null;
  last_workflow_run_id: string | null;
}

export interface WorkflowScheduleList extends WorkflowSchedule {
  workflow_name: string;
}

export interface WorkflowEventTrigger {
  id: string;
  workflow_id: string;
  event_type: string;
  is_active: boolean;
  created_at: string;
  secret_rotated_at: string | null;
  webhook_secret?: string;
  webhook_url?: string;
}

export interface WorkflowEventDelivery {
  id: string;
  trigger_id: string;
  event_id: string;
  event_type: string;
  status: string;
  workflow_run_id: string | null;
  attempts: number;
  error: Record<string, unknown> | null;
  received_at: string;
  processed_at: string | null;
}

export interface AdminTenantSummary {
  id: string;
  name: string;
  slug: string;
  status: string;
  users: number;
  workflows: number;
  runs: number;
  cost_usd: number;
  created_at: string;
}

export interface AdminProviderSummary {
  provider: string;
  calls: number;
  successful_calls: number;
  failed_calls: number;
  total_tokens: number;
  cost_usd: number;
  avg_latency_ms: number;
}

export interface AdminDashboard {
  tenants: number;
  active_tenants: number;
  users: number;
  workflows: number;
  workflow_runs: number;
  ai_calls: number;
  total_tokens: number;
  total_cost_usd: number;
  failed_runs: number;
  pending_outbox: number;
  dead_outbox: number;
  tenants_breakdown: AdminTenantSummary[];
  providers: AdminProviderSummary[];
  health: {
    database: string;
    redis: string;
    celery: string;
    ai_provider: string;
  };
}

export interface CustomerDashboard {
  employee_count: number;
  active_employee_count: number;
  workflow_count: number;
  active_workflow_count: number;
  workflow_run_count: number;
  running_workflow_run_count: number;
  successful_workflow_run_count: number;
  failed_workflow_run_count: number;
  pending_approval_count: number;
  active_schedule_count: number;
  active_webhook_count: number;
  recent_runs: Array<{
    id: string;
    workflow_id: string;
    workflow_version_id: string;
    status: string;
    created_at: string;
    started_at: string | null;
    completed_at: string | null;
    total_cost_usd: number;
  }>;
  usage: {
    calls: number;
    successful_calls: number;
    failed_calls: number;
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
    cost_usd: number;
    avg_latency_ms: number;
  };
  health: Record<string, string>;
  generated_at: string;
}


export interface AuditLog {
  id: string;
  actor_type: string;
  actor_id: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  request_id: string | null;
  status: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface OperationsMetrics {
  outbox: { pending: number; processing: number; dead: number };
  workflow_runs_total: number;
  workflow_steps_total: number;
}

export interface DeadLetter {
  id: string;
  kind: string;
  attempts: number;
  last_error: string | null;
  dead_at: string | null;
  replayed_at: string | null;
  payload: Record<string, unknown>;
}

export interface BillingPlan {
  code: string;
  name: string;
  monthly_price_usd: number;
  monthly_runs: number;
  monthly_tokens: number;
  max_employees: number;
  max_workflows: number;
  features: Record<string, unknown>;
}

export interface Subscription {
  id: string;
  plan: BillingPlan;
  status: string;
  provider: string;
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  canceled_at: string | null;
  trial_ends_at: string | null;
}

// ── Knowledge (RAG) ───────────────────────────────────
export interface KnowledgeDocument {
  id: string;
  file_id: string;
  status: string;
  chunk_count: number;
  embedding_model: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeSearchResult {
  chunk_id: string;
  document_id: string;
  file_id: string;
  filename: string;
  chunk_index: number;
  score: number;
  content: string;
}

// ── Memory ────────────────────────────────────────────
export interface MemoryItem {
  id: string;
  employee_id: string;
  memory_type: string;
  content: string;
  importance: number;
  status: string;
  metadata_?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  expires_at: string | null;
  created_at: string;
  updated_at: string;
  version: number;
  supersedes_id: string | null;
}

export interface MemorySearchResult {
  id: string;
  employee_id: string;
  memory_type: string;
  content: string;
  importance: number;
  score: number;
  metadata: Record<string, unknown>;
  version: number;
  status: string;
  supersedes_id: string | null;
}

// ── Business Orders (Phase 8) ─────────────────────────
export interface BusinessOrder {
  id: string;
  number: string;
  status: string;
  currency: string;
  customer_name: string;
  customer_email: string | null;
  order_date: string;
  requested_delivery_date: string | null;
  tax_rate: string | number;
  subtotal: string | number;
  tax_amount: string | number;
  total: string | number;
  line_items: Array<{
    description: string;
    quantity: number;
    unit_price: number;
    amount?: number;
    sku?: string;
  }>;
  notes: string | null;
  source_file_id: string | null;
  invoice_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface OrderSummary {
  currency_breakdown: Record<string, Record<string, number>>;
  counts_by_status: Record<string, number>;
  total_orders: number;
}

// ── Sales Deals (Phase 9) ─────────────────────────────
export interface BusinessDeal {
  id: string;
  title: string;
  customer_name: string;
  customer_email: string | null;
  stage: string;
  amount: string | number;
  currency: string;
  probability: number;
  expected_close_date: string | null;
  owner_name: string | null;
  notes: string | null;
  source: string | null;
  order_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface SalesPipelineSummary {
  counts_by_stage: Record<string, number>;
  amount_by_stage: Record<string, number>;
  weighted_pipeline: number;
  won_amount: number;
  lost_amount: number;
  open_deals: number;
  total_deals: number;
  currency: string;
}

export interface SalesForecast {
  method: string;
  horizon_days: number;
  expected_revenue: number;
  currency: string;
  assumptions: Record<string, unknown>;
}

export interface CustomerChannel {
  id: string;
  employee_id: string;
  name: string;
  channel_type: string;
  public_key: string;
  config: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
}

export interface CustomerConversationSummary {
  id: string;
  employee_id: string;
  channel_id: string;
  status: string;
  customer_name: string | null;
  customer_email: string | null;
  customer_phone: string | null;
  message_count: number;
  last_message: string | null;
  updated_at: string;
}

export interface PublicChannel {
  public_key: string;
  employee_id: string;
  employee_name: string;
  employee_slug: string;
  channel_name: string;
  channel_type: string;
  config: Record<string, unknown>;
}

export interface PublicMessage {
  id: string;
  role: "user" | "assistant" | string;
  content: string;
  created_at: string;
}

export interface PublicConversation {
  id: string;
  employee_name: string;
  status: string;
  customer_token?: string | null;
  messages: PublicMessage[];
}

export interface Product {
  id: string; sku: string | null; name: string; description: string | null; category: string | null;
  price: string | number; currency: string; inventory: number; attributes: Record<string, unknown>;
  images: string[]; is_active: boolean; source: string; created_at: string; updated_at: string;
}
export interface CommerceIntegration { id: string; provider: string; name: string; status: string; config: Record<string, unknown>; is_active: boolean; created_at: string; updated_at: string; }
export interface OnboardingProgress { current_step: number; completed_steps: number[]; business_type: string | null; setup_data: Record<string, unknown>; completed: boolean; }
export interface InboxConversation extends CustomerConversationSummary { handoff_requested: boolean; assigned_user_id: string | null; }

export interface Customer { id:string; external_key:string; name:string|null; email:string|null; phone:string|null; tags:string[]; notes:string|null; last_channel:string|null; created_at:string; updated_at:string; }

export interface EmployeeTemplate {
  code: string; name: string; description: string; kind: string;
  allowed_tools: string[]; rules: Record<string, unknown>; prompt_template: string;
}
export interface ROIAnalytics {
  conversations:number; ai_resolved:number; human_handoffs:number; runs:number; successful_runs:number;
  orders:number; revenue:number; influenced_orders:number; influenced_revenue:number;
  ai_resolution_rate:number; handoff_rate:number;
}
export interface Guardrails { employee_id:string; version_id:string; rules:Record<string, unknown>; }

export interface BusinessInvoice { id: string; number: string; status: string; currency: string; customer_name: string; customer_email: string | null; issue_date: string; due_date: string | null; tax_rate: string | number; subtotal: string | number; tax_amount: string | number; total: string | number; line_items: Array<Record<string, any>>; notes: string | null; source_file_id: string | null; pdf_file_id: string | null; created_at: string; updated_at: string; }
export interface InvoiceFinancialSummary { currency_breakdown: Record<string, Record<string, number>>; counts_by_status: Record<string, number>; total_invoices: number; }
export interface TenantUser { id: string; email: string; full_name: string | null; is_active: boolean; roles: string[]; }
export interface TenantRole { id: string; name: string; description: string | null; permissions: string[]; }
