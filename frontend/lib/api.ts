import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "./auth-store";
import type {
  APIResponse,
  Employee,
  EmployeeCreate,
  FileItem,
  LoginRequest,
  MeResponse,
  RegisterRequest,
  Run,
  RunCreate,
  RunTrace,
  TokenResponse,
  UsageSummary,
  ToolDefinition,
  ToolApproval,
  WorkflowApproval,
  AdminDashboard,
  AdminTenantSummary,
  AuditLog,
  OperationsMetrics,
  DeadLetter,
  BillingPlan,
  Subscription,
  CustomerChannel,
  CustomerConversationSummary,
  PublicChannel,
  PublicConversation,
} from "@/types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL
    ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1`
    : "/api/proxy";

export const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError<APIResponse<unknown>>) => {
    const original = error.config;
    if (
      error.response?.status === 401 &&
      original &&
      !(original as InternalAxiosRequestConfig & { _retry?: boolean })._retry
    ) {
      (original as InternalAxiosRequestConfig & { _retry?: boolean })._retry =
        true;
      const refresh = useAuthStore.getState().refreshToken;
      if (refresh) {
        try {
          const { data } = await axios.post<APIResponse<TokenResponse>>(
            `${API_BASE}/auth/refresh`,
            { refresh_token: refresh }
          );
          if (data.data) {
            useAuthStore
              .getState()
              .setTokens(data.data.access_token, data.data.refresh_token);
            original.headers.Authorization = `Bearer ${data.data.access_token}`;
            return api(original);
          }
        } catch {
          useAuthStore.getState().logout();
          if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
            window.location.href = "/login?reason=session";
          }
        }
      } else {
        useAuthStore.getState().logout();
        if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
          window.location.href = "/login?reason=session";
        }
      }
    }
    return Promise.reject(error);
  }
);

function unwrap<T>(res: { data: APIResponse<T> }): T {
  if (!res.data.success || res.data.data === undefined) {
    throw new Error("Unexpected API response");
  }
  return res.data.data;
}

// ── API Keys ─────────────────────────────────────────
export interface APIKey {
  id: string;
  name: string;
  key_prefix: string;
  is_active: boolean;
  last_used_at: string | null;
  expires_at: string | null;
  revoked_at: string | null;
  created_at: string;
}
export interface APIKeyCreated extends APIKey { key: string; }

export async function listApiKeys() {
  return unwrap(await api.get<APIResponse<APIKey[]>>("/api-keys"));
}
export async function createApiKey(payload: { name: string; expires_at?: string | null }) {
  return unwrap(await api.post<APIResponse<APIKeyCreated>>("/api-keys", payload));
}
export async function revokeApiKey(id: string) {
  return unwrap(await api.post<APIResponse<APIKey>>(`/api-keys/${id}/revoke`));
}

// ── Auth ──────────────────────────────────────────────
export async function register(payload: RegisterRequest) {
  return unwrap(await api.post<APIResponse<TokenResponse>>("/auth/register", payload));
}

export async function login(payload: LoginRequest) {
  return unwrap(await api.post<APIResponse<TokenResponse>>("/auth/login", payload));
}

export async function forgotPassword(payload: { email: string; tenant_slug: string }) {
  return unwrap(await api.post<APIResponse<{ message: string }>>("/auth/forgot-password", payload));
}

export async function resetPassword(payload: { token: string; password: string }) {
  return unwrap(await api.post<APIResponse<{ message: string }>>("/auth/reset-password", payload));
}

export async function fetchMe() {
  return unwrap(await api.get<APIResponse<MeResponse>>("/auth/me"));
}

// ── Employees ─────────────────────────────────────────
export async function listAvailableTools() {
  return unwrap(await api.get<APIResponse<ToolDefinition[]>>("/employees/available-tools"));
}

export async function listEmployees() {
  return unwrap(await api.get<APIResponse<Employee[]>>("/employees"));
}

export async function getEmployee(id: string) {
  return unwrap(await api.get<APIResponse<Employee>>(`/employees/${id}`));
}

export async function createCustomerChannel(payload: { employee_id: string; name: string; channel_type?: "web_widget" | "public_chat" | "whatsapp"; config?: Record<string, unknown> }) {
  return unwrap(await api.post<APIResponse<CustomerChannel>>("/customer-channels", payload));
}

export async function listCustomerChannels(employeeId?: string) {
  const params = employeeId ? { employee_id: employeeId } : undefined;
  return unwrap(await api.get<APIResponse<CustomerChannel[]>>("/customer-channels", { params }));
}

export async function listCustomerConversations(employeeId?: string) {
  const params = employeeId ? { employee_id: employeeId } : undefined;
  return unwrap(await api.get<APIResponse<CustomerConversationSummary[]>>("/customer-channels/conversations", { params }));
}

export async function getPublicChannel(publicKey: string) {
  return unwrap(await api.get<APIResponse<PublicChannel>>(`/public/chat/channels/${publicKey}`));
}

export async function createPublicConversation(publicKey: string, payload?: { customer_name?: string; customer_email?: string; customer_phone?: string }) {
  return unwrap(await api.post<APIResponse<PublicConversation>>(`/public/chat/channels/${publicKey}/conversations`, payload ?? {}));
}

export async function getPublicConversation(conversationId: string, token: string) {
  return unwrap(await api.get<APIResponse<PublicConversation>>(`/public/chat/conversations/${conversationId}`, { headers: { "X-Customer-Token": token } }));
}

export async function sendPublicMessage(conversationId: string, token: string, content: string) {
  return unwrap(await api.post<APIResponse<{ conversation_id: string; run_id: string; status: string }>>(`/public/chat/conversations/${conversationId}/messages`, { content }, { headers: { "X-Customer-Token": token } }));
}

export async function createEmployee(payload: EmployeeCreate) {
  return unwrap(
    await api.post<APIResponse<Employee>>("/employees", payload)
  );
}

// ── Runs ──────────────────────────────────────────────
export async function listRuns(employeeId?: string) {
  const params = employeeId ? { employee_id: employeeId } : undefined;
  return unwrap(await api.get<APIResponse<Run[]>>("/runs", { params }));
}

export async function getRun(id: string) {
  return unwrap(await api.get<APIResponse<Run>>(`/runs/${id}`));
}

export async function createRun(payload: RunCreate) {
  return unwrap(await api.post<APIResponse<Run>>("/runs", payload));
}

export async function getRunTrace(id: string) {
  return unwrap(await api.get<APIResponse<RunTrace>>(`/runs/${id}/trace`));
}

export async function getCustomerDashboard() {
  return unwrap(await api.get<APIResponse<import("@/types").CustomerDashboard>>("/customer-dashboard"));
}

export async function getOperationsMetrics() {
  return unwrap(await api.get<APIResponse<OperationsMetrics>>("/operations/metrics"));
}

export async function getAuditLogs(params?: { limit?: number; action?: string; status_filter?: string }) {
  return unwrap(await api.get<APIResponse<AuditLog[]>>("/operations/audit-logs", { params }));
}

export async function listDeadLetters(limit = 50) {
  return unwrap(await api.get<APIResponse<DeadLetter[]>>("/operations/dead-letters", { params: { limit } }));
}

export async function replayDeadLetter(id: string) {
  return unwrap(await api.post<APIResponse<Record<string, unknown>>>(`/operations/dead-letters/${id}/replay`));
}

export async function getUsageSummary(params?: { from_at?: string; to_at?: string }) {
  return unwrap(
    await api.get<APIResponse<UsageSummary>>("/usage/summary", { params })
  );
}

// ── Files ─────────────────────────────────────────────
export async function listFiles() {
  return unwrap(await api.get<APIResponse<FileItem[]>>("/files"));
}

export async function uploadFile(file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await api.post<APIResponse<FileItem>>("/files", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return unwrap(res);
}

export async function deleteFile(id: string) {
  await api.delete(`/files/${id}`);
}

// Phase 2: stream a file's bytes through the authenticated API client (a
// plain <a href> can't carry the Bearer token) and trigger a browser save.
export async function downloadFile(id: string, filename: string) {
  const res = await api.get(`/files/${id}/download`, { responseType: "blob" });
  const url = window.URL.createObjectURL(res.data as Blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

// Phase 3 — Validation tooling
export interface FeedbackPayload {
  rating: number;
  comment?: string;
  run_id?: string;
  employee_id?: string;
  category?: "run" | "general";
}

export async function submitFeedback(payload: FeedbackPayload) {
  return unwrap(await api.post<APIResponse<unknown>>("/feedback", payload));
}

export { getErrorMessage } from "./errors";
// ── Tool approvals ───────────────────────────────────
export async function listApprovals(status?: string) {
  const params = status ? { status } : undefined;
  return unwrap(await api.get<APIResponse<ToolApproval[]>>("/approvals", { params }));
}

export async function decideApproval(id: string, decision: "approve" | "reject", reason?: string) {
  return unwrap(await api.post<APIResponse<ToolApproval>>(`/approvals/${id}/decision`, { decision, reason }));
}

// ── Workflow approvals ───────────────────────────────
export async function listWorkflowApprovals(status?: string) {
  const params = status ? { status_filter: status } : undefined;
  return unwrap(await api.get<APIResponse<WorkflowApproval[]>>("/workflow-approvals", { params }));
}

export async function decideWorkflowApproval(id: string, decision: "approve" | "reject", reason?: string) {
  return unwrap(await api.post<APIResponse<WorkflowApproval>>(`/workflow-approvals/${id}/decision`, { decision, reason }));
}


// ── Platform Admin ───────────────────────────────────
export async function getAdminDashboard() {
  return unwrap(await api.get<APIResponse<AdminDashboard>>("/admin/dashboard"));
}

export async function listAdminTenants(status?: string) {
  const params = status ? { status } : undefined;
  const data = unwrap(await api.get<APIResponse<{ items: AdminTenantSummary[] }>>("/admin/tenants", { params }));
  return data.items;
}

// Phase 3 — Validation dashboard (03_Roadmap_v1.1 §6 exit-criteria proxy)
export interface ValidationTenantSummary {
  tenant_id: string;
  tenant_name: string;
  report_employee_runs_last_14d: number;
  report_employee_runs_total: number;
  last_run_at: string | null;
  feedback_count: number;
  avg_rating: number | null;
}
export interface FeedbackItem {
  id: string;
  tenant_id: string;
  user_id: string | null;
  run_id: string | null;
  employee_id: string | null;
  rating: number;
  comment: string | null;
  category: string;
  created_at: string;
}
export interface ValidationSummary {
  active_tenant_count: number;
  meets_phase3_customer_criteria: boolean;
  phase3_customer_target: number;
  total_feedback_count: number;
  overall_avg_rating: number | null;
  tenants: ValidationTenantSummary[];
  recent_feedback: FeedbackItem[];
}
export async function getValidationSummary() {
  return unwrap(await api.get<APIResponse<ValidationSummary>>("/admin/validation"));
}

// ── Workflows ─────────────────────────────────────────
export async function createWorkflow(payload: {
  slug: string;
  name: string;
  steps: import("@/types").WorkflowStepDefinition[];
  trigger_type?: "manual" | "schedule" | "event";
  max_runtime_seconds?: number | null;
}) {
  return unwrap(await api.post<APIResponse<import("@/types").Workflow>>("/workflows", payload));
}

export async function createWorkflowRun(workflowId: string, payload?: { input_data?: Record<string, unknown>; idempotency_key?: string }) {
  const key = payload?.idempotency_key ?? `ui-${crypto.randomUUID()}`;
  return unwrap(await api.post<APIResponse<import("@/types").WorkflowRun>>(`/workflows/${workflowId}/runs`, payload ?? { input_data: {} }, { headers: { "Idempotency-Key": key } }));
}

export async function listWorkflowRuns(workflowId: string) {
  return unwrap(await api.get<APIResponse<import("@/types").WorkflowRun[]>>(`/workflows/${workflowId}/runs`));
}

export async function replayWorkflowRun(workflowId: string, runId: string) {
  return unwrap(await api.post<APIResponse<import("@/types").WorkflowRun>>(`/workflows/${workflowId}/runs/${runId}/replay`, { idempotency_key: `ui-replay-${crypto.randomUUID()}` }));
}

export async function activateWorkflowVersion(workflowId: string, versionId: string) {
  return unwrap(await api.post<APIResponse<import("@/types").WorkflowVersion>>(`/workflows/${workflowId}/versions/${versionId}/activate`));
}

export async function getWorkflowRun(workflowId: string, runId: string) {
  return unwrap(await api.get<APIResponse<import("@/types").WorkflowRun>>(`/workflows/${workflowId}/runs/${runId}`));
}

export async function getWorkflowObservability(workflowId: string, runId: string) {
  return unwrap(await api.get<APIResponse<Record<string, unknown>>>(`/workflows/${workflowId}/runs/${runId}/observability`));
}

export async function cancelWorkflowRun(workflowId: string, runId: string, reason?: string) {
  return unwrap(await api.post<APIResponse<import("@/types").WorkflowRun>>(`/workflows/${workflowId}/runs/${runId}/cancel`, { reason }));
}

export async function getWorkflow(id: string) {
  return unwrap(await api.get<APIResponse<import("@/types").Workflow>>(`/workflows/${id}`));
}

export async function listWorkflowVersions(id: string) {
  return unwrap(await api.get<APIResponse<import("@/types").WorkflowVersion[]>>(`/workflows/${id}/versions`));
}

export async function createWorkflowVersion(id: string, payload: {
  steps: import("@/types").WorkflowStepDefinition[];
  trigger_type?: "manual" | "schedule" | "event";
  max_runtime_seconds?: number | null;
  activate?: boolean;
}) {
  return unwrap(await api.post<APIResponse<import("@/types").WorkflowVersion>>(`/workflows/${id}/versions`, payload));
}

// ── Workflow schedules ────────────────────────────────
export async function listWorkflowSchedules() {
  return unwrap(await api.get<APIResponse<import("@/types").WorkflowScheduleList[]>>("/workflow-schedules"));
}

export async function createWorkflowSchedule(workflowId: string, payload: { cron_expression: string; timezone: string }) {
  return unwrap(await api.post<APIResponse<import("@/types").WorkflowSchedule>>(`/workflows/${workflowId}/schedules`, payload));
}

export async function updateWorkflowSchedule(id: string, payload: { cron_expression?: string; timezone?: string; is_active?: boolean }) {
  return unwrap(await api.patch<APIResponse<import("@/types").WorkflowSchedule>>(`/workflow-schedules/${id}`, payload));
}

export async function deleteWorkflowSchedule(id: string) {
  await api.delete(`/workflow-schedules/${id}`);
}

export async function listWorkflows() {
  return unwrap(await api.get<APIResponse<import("@/types").Workflow[]>>("/workflows"));
}

// ── Workflow Webhooks ────────────────────────────────
export async function listWorkflowEventTriggers(workflowId: string) {
  return unwrap(await api.get<APIResponse<import("@/types").WorkflowEventTrigger[]>>(`/workflows/${workflowId}/event-triggers`));
}

export async function createWorkflowEventTrigger(workflowId: string, eventType: string) {
  return unwrap(await api.post<APIResponse<import("@/types").WorkflowEventTrigger>>(`/workflows/${workflowId}/event-triggers`, { event_type: eventType }));
}

export async function updateWorkflowEventTrigger(workflowId: string, triggerId: string, payload: { is_active: boolean }) {
  return unwrap(await api.patch<APIResponse<import("@/types").WorkflowEventTrigger>>(`/workflows/${workflowId}/event-triggers/${triggerId}`, payload));
}

export async function rotateWorkflowEventTriggerSecret(workflowId: string, triggerId: string) {
  return unwrap(await api.post<APIResponse<import("@/types").WorkflowEventTrigger>>(`/workflows/${workflowId}/event-triggers/${triggerId}/rotate-secret`));
}

export async function listWorkflowEventDeliveries(triggerId?: string, status?: string) {
  const params: Record<string, string> = {};
  if (triggerId) params.trigger_id = triggerId;
  if (status) params.status_filter = status;
  return unwrap(await api.get<APIResponse<import("@/types").WorkflowEventDelivery[]>>("/workflow-event-deliveries", { params }));
}

export async function replayWorkflowEventDelivery(deliveryId: string) {
  return unwrap(await api.post<APIResponse<import("@/types").WorkflowEventDelivery>>(`/workflow-event-deliveries/${deliveryId}/replay`));
}


// ── Billing / Monetization ───────────────────────────
export async function listBillingPlans() {
  return unwrap(await api.get<APIResponse<BillingPlan[]>>("/billing/plans"));
}

export async function getSubscription() {
  return unwrap(await api.get<APIResponse<Subscription>>("/billing/subscription"));
}

export async function changeSubscription(plan_code: string) {
  return unwrap(await api.post<APIResponse<Subscription>>("/billing/subscription", { plan_code }));
}

export async function cancelSubscription(at_period_end = true) {
  return unwrap(await api.post<APIResponse<Subscription>>("/billing/subscription/cancel", { at_period_end }));
}

// Phase 6 — real Stripe checkout / self-serve portal
export async function createCheckoutSession(plan_code: string) {
  return unwrap(await api.post<APIResponse<{ checkout_url: string }>>("/billing/checkout", { plan_code }));
}

export async function createPortalSession() {
  return unwrap(await api.post<APIResponse<{ portal_url: string }>>("/billing/portal"));
}
export async function getBillingEntitlements() {
  return unwrap(await api.get<APIResponse<{ usage: { calls:number; tokens:number; runs:number; employees:number; workflows:number }; trial_ends_at:string|null; status:string; plan:BillingPlan }>>("/billing/entitlements"));
}

// ── Knowledge (RAG) ───────────────────────────────────
export async function indexKnowledgeFile(file_id: string) {
  return unwrap(
    await api.post<APIResponse<import("@/types").KnowledgeDocument>>("/knowledge/index", {
      file_id,
    })
  );
}

export async function searchKnowledge(query: string, top_k = 5) {
  return unwrap(
    await api.post<APIResponse<import("@/types").KnowledgeSearchResult[]>>("/knowledge/search", {
      query,
      top_k,
    })
  );
}

// ── Memory ────────────────────────────────────────────
export async function createMemory(payload: {
  employee_id: string;
  content: string;
  memory_type?: string;
  importance?: number;
}) {
  return unwrap(
    await api.post<APIResponse<import("@/types").MemoryItem>>("/memory", payload)
  );
}

export async function searchMemory(payload: {
  employee_id: string;
  query: string;
  top_k?: number;
  min_score?: number;
}) {
  return unwrap(
    await api.post<APIResponse<import("@/types").MemorySearchResult[]>>("/memory/search", payload)
  );
}

export async function deleteMemory(memory_id: string) {
  return unwrap(await api.delete<APIResponse<null>>(`/memory/${memory_id}`));
}

// ── Business Orders (Phase 8) ─────────────────────────
export async function listOrders(status?: string) {
  const params: Record<string, string> = {};
  if (status) params.status = status;
  return unwrap(
    await api.get<APIResponse<import("@/types").BusinessOrder[]>>("/orders", { params })
  );
}

export async function getOrderSummary() {
  return unwrap(
    await api.get<APIResponse<import("@/types").OrderSummary>>("/orders/summary")
  );
}

export async function getOrder(orderId: string) {
  return unwrap(
    await api.get<APIResponse<import("@/types").BusinessOrder>>(`/orders/${orderId}`)
  );
}

export async function updateOrderStatus(orderId: string, status: string) {
  return unwrap(
    await api.post<APIResponse<import("@/types").BusinessOrder>>(
      `/orders/${orderId}/status`,
      { status }
    )
  );
}

// ── Sales Deals (Phase 9) ─────────────────────────────
export async function listDeals(stage?: string) {
  const params: Record<string, string> = {};
  if (stage) params.stage = stage;
  return unwrap(
    await api.get<APIResponse<import("@/types").BusinessDeal[]>>("/sales/deals", { params })
  );
}

export async function getSalesPipeline() {
  return unwrap(
    await api.get<APIResponse<import("@/types").SalesPipelineSummary>>("/sales/pipeline")
  );
}

export async function getSalesForecast(horizon_days = 30) {
  return unwrap(
    await api.get<APIResponse<import("@/types").SalesForecast>>("/sales/forecast", {
      params: { horizon_days },
    })
  );
}

export async function getDeal(dealId: string) { return unwrap(await api.get<APIResponse<import("@/types").BusinessDeal>>(`/sales/deals/${dealId}`)); }
export async function updateDealStage(
  dealId: string,
  stage: string,
  probability?: number
) {
  return unwrap(
    await api.post<APIResponse<import("@/types").BusinessDeal>>(
      `/sales/deals/${dealId}/stage`,
      { stage, probability }
    )
  );
}

// ── SaaS sales readiness ─────────────────────────────
export async function listProducts(q?: string) {
  return unwrap(await api.get<APIResponse<import("@/types").Product[]>>("/products", { params: q ? { q } : undefined }));
}
export async function createProduct(payload: Partial<import("@/types").Product>) {
  return unwrap(await api.post<APIResponse<import("@/types").Product>>("/products", payload));
}
export async function updateProductInventory(id: string, inventory: number) {
  return unwrap(await api.post<APIResponse<import("@/types").Product>>(`/products/${id}/inventory`, { inventory }));
}
export async function listCommerceIntegrations() {
  return unwrap(await api.get<APIResponse<import("@/types").CommerceIntegration[]>>("/commerce-integrations"));
}
export async function createCommerceIntegration(payload: { provider: string; name: string; config?: Record<string, unknown> }) {
  return unwrap(await api.post<APIResponse<import("@/types").CommerceIntegration>>("/commerce-integrations", payload));
}
export async function testCommerceIntegration(id: string) {
  return unwrap(await api.post<APIResponse<{ connected: boolean; shop?: { name?: string; domain?: string; id?: string } }>>(`/commerce-integrations/${id}/test`));
}
export async function syncCommerceProducts(id: string) {
  return unwrap(await api.post<APIResponse<{ provider: string; products_seen: number; created: number; updated: number }>>(`/commerce-integrations/${id}/sync/products`));
}
export async function syncCommerceOrders(id: string) {
  return unwrap(await api.post<APIResponse<{ provider: string; orders_seen: number; created: number; updated: number }>>(`/commerce-integrations/${id}/sync/orders`));
}
export async function reconcileCommerce(id: string) {
  return unwrap(await api.post<APIResponse<Record<string, unknown>>>(`/commerce-integrations/${id}/reconcile`));
}
export function shopifyInstallUrl(shop: string) {
  return `${API_BASE}/commerce-integrations/shopify/install?shop=${encodeURIComponent(shop)}`;
}
export async function getOnboarding() {
  return unwrap(await api.get<APIResponse<import("@/types").OnboardingProgress>>("/onboarding"));
}
export async function updateOnboarding(payload: { step: number; business_type?: string; data?: Record<string, unknown>; complete_step?: boolean }) {
  return unwrap(await api.post<APIResponse<import("@/types").OnboardingProgress>>("/onboarding/progress", payload));
}
export async function listInboxConversations() {
  return unwrap(await api.get<APIResponse<import("@/types").InboxConversation[]>>("/inbox/conversations"));
}
export async function setConversationHandoff(id: string, requested: boolean, assigned_user_id?: string | null) {
  return unwrap(await api.post<APIResponse<{ id: string; status: string; handoff_requested: boolean; assigned_user_id: string | null }>>(`/inbox/conversations/${id}/handoff`, { requested, assigned_user_id: assigned_user_id ?? null }));
}

export async function listCustomers(q?: string) { return unwrap(await api.get<APIResponse<import("@/types").Customer[]>>("/customers", { params: q ? { q } : undefined })); }
export async function getCustomer(id: string) { return unwrap(await api.get<APIResponse<import("@/types").Customer>>(`/customers/${id}`)); }
export async function updateCustomer(id: string, payload: Partial<import("@/types").Customer>) { return unwrap(await api.patch<APIResponse<import("@/types").Customer>>(`/customers/${id}`, payload)); }

export async function getInboxMessages(id: string) { return unwrap(await api.get<APIResponse<{id:string;role:string;content:string;created_at:string}[]>>(`/inbox/conversations/${id}/messages`)); }
export async function sendInboxMessage(id: string, content: string) { return unwrap(await api.post<APIResponse<{id:string;conversation_id:string;role:string;content:string;created_at:string}>>(`/inbox/conversations/${id}/messages`, { content })); }

// RC6 — templates, ROI, guardrails and privacy
export async function listEmployeeTemplates() {
  return unwrap(await api.get<APIResponse<import("@/types").EmployeeTemplate[]>>("/employee-templates"));
}
export async function installEmployeeTemplate(code: string) {
  return unwrap(await api.post<APIResponse<{id:string;name:string;slug:string}>>(`/employee-templates/${code}/install`));
}
export async function getROIAnalytics() {
  return unwrap(await api.get<APIResponse<import("@/types").ROIAnalytics>>("/analytics/roi"));
}
export async function getEmployeeGuardrails(id: string) {
  return unwrap(await api.get<APIResponse<import("@/types").Guardrails>>(`/employees/${id}/guardrails`));
}
export async function updateEmployeeGuardrails(id: string, payload: {rules:Record<string,unknown>; allowed_tools?:string[]}) {
  return unwrap(await api.put<APIResponse<import("@/types").Guardrails>>(`/employees/${id}/guardrails`, payload));
}
export async function exportCustomerData(id: string) {
  return unwrap(await api.get<APIResponse<Record<string,unknown>>>(`/privacy/customers/${id}/export`));
}
export async function deleteCustomerData(id: string) {
  return unwrap(await api.delete<APIResponse<{deleted:boolean;customer_id:string}>>(`/privacy/customers/${id}`));
}

// ── Business invoices ─────────────────────────────────
export async function listInvoices(status?: string) { return unwrap(await api.get<APIResponse<import("@/types").BusinessInvoice[]>>("/invoices", { params: status ? { status } : undefined })); }
export async function getInvoice(id: string) { return unwrap(await api.get<APIResponse<import("@/types").BusinessInvoice>>(`/invoices/${id}`)); }
export async function getInvoiceSummary() { return unwrap(await api.get<APIResponse<import("@/types").InvoiceFinancialSummary>>("/invoices/summary")); }
export async function updateInvoiceStatus(id: string, status: string) { return unwrap(await api.post<APIResponse<import("@/types").BusinessInvoice>>(`/invoices/${id}/status`, { status })); }
export async function exportInvoicePdf(id: string) { return unwrap(await api.post<APIResponse<Record<string, unknown>>>(`/invoices/${id}/export-pdf`)); }

// ── Tenant administration ─────────────────────────────
export async function listTenantUsers() { return unwrap(await api.get<APIResponse<import("@/types").TenantUser[]>>("/tenant-admin/users")); }
export async function listTenantRoles() { return unwrap(await api.get<APIResponse<import("@/types").TenantRole[]>>("/tenant-admin/roles")); }
export async function updateTenantUserStatus(id: string, is_active: boolean) { return unwrap(await api.post<APIResponse<import("@/types").TenantUser>>(`/tenant-admin/users/${id}/status`, { is_active })); }
export async function updateTenantUserRoles(id: string, role_ids: string[]) { return unwrap(await api.post<APIResponse<import("@/types").TenantUser>>(`/tenant-admin/users/${id}/roles`, { role_ids })); }


// Platform provider readiness (read-only; secrets are never returned).
export async function getPlatformProviders() {
  return unwrap(await api.get<APIResponse<{ providers: { name: string; category: string; configured: boolean; secret_configured: boolean }[] }>>("/admin/providers"));
}
