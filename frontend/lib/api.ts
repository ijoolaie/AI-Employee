import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "./auth-store";
import type {
  APIResponse, Employee, EmployeeCreate, FileItem, LoginRequest, MeResponse,
  RegisterRequest, Run, RunCreate, RunTrace, TokenResponse, UsageSummary,
  ToolDefinition, ToolApproval, WorkflowApproval, AdminDashboard, AdminTenantSummary,
  AuditLog, OperationsMetrics, DeadLetter, BillingPlan, Subscription,
  CustomerChannel, CustomerConversationSummary, PublicChannel, PublicConversation,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1` : "/api/proxy";
export const api = axios.create({ baseURL: API_BASE, headers: { "Content-Type": "application/json" } });
api.interceptors.request.use((config: InternalAxiosRequestConfig) => { const token = useAuthStore.getState().accessToken; if (token) config.headers.Authorization = `Bearer ${token}`; return config; });
api.interceptors.response.use((res) => res, async (error: AxiosError<APIResponse<unknown>>) => {
  const original = error.config;
  if (error.response?.status === 401 && original && !(original as InternalAxiosRequestConfig & { _retry?: boolean })._retry) {
    (original as InternalAxiosRequestConfig & { _retry?: boolean })._retry = true;
    const refresh = useAuthStore.getState().refreshToken;
    if (refresh) { try { const { data } = await axios.post<APIResponse<TokenResponse>>(`${API_BASE}/auth/refresh`, { refresh_token: refresh }); if (data.data) { useAuthStore.getState().setTokens(data.data.access_token, data.data.refresh_token); original.headers.Authorization = `Bearer ${data.data.access_token}`; return api(original); } } catch { useAuthStore.getState().logout(); if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) window.location.href = "/login?reason=session"; } }
    else { useAuthStore.getState().logout(); if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) window.location.href = "/login?reason=session"; }
  }
  return Promise.reject(error);
});
function unwrap<T>(res: { data: APIResponse<T> }): T { if (!res.data.success || res.data.data === undefined) throw new Error("Unexpected API response"); return res.data.data; }

export interface WorkItemSummary { id: string; title: string; description: string | null; status: string; priority: number; requester_id: string | null; executor_type: string | null; executor_id: string | null; input_data: Record<string, unknown>; output_data: Record<string, unknown> | null; created_at: string; updated_at: string; }
export interface WorkItemHistoryEvent { id: string; action: string; actor_type: string; actor_id: string | null; status: string; request_id: string | null; metadata: Record<string, unknown>; created_at: string; }
export async function listWorkItems(params?: { status?: string; limit?: number }) { return unwrap(await api.get<APIResponse<WorkItemSummary[]>>("/work-items", { params })); }
export async function getWorkItemHistory(id: string) { return unwrap(await api.get<APIResponse<WorkItemHistoryEvent[]>>(`/work-items/${id}/history`)); }

export async function listApiKeys() { return unwrap(await api.get<APIResponse<unknown[]>>("/api-keys")); }
export async function createApiKey(payload: { name: string; expires_at?: string | null }) { return unwrap(await api.post<APIResponse<unknown>>("/api-keys", payload)); }
export async function revokeApiKey(id: string) { return unwrap(await api.post<APIResponse<unknown>>(`/api-keys/${id}/revoke`)); }
export async function register(payload: RegisterRequest) { return unwrap(await api.post<APIResponse<TokenResponse>>("/auth/register", payload)); }
export async function login(payload: LoginRequest) { return unwrap(await api.post<APIResponse<TokenResponse>>("/auth/login", payload)); }
export async function forgotPassword(payload: { email: string; tenant_slug: string }) { return unwrap(await api.post<APIResponse<{ message: string }>>("/auth/forgot-password", payload)); }
export async function resetPassword(payload: { token: string; password: string }) { return unwrap(await api.post<APIResponse<{ message: string }>>("/auth/reset-password", payload)); }
export async function fetchMe() { return unwrap(await api.get<APIResponse<MeResponse>>("/auth/me")); }
export async function listAvailableTools() { return unwrap(await api.get<APIResponse<ToolDefinition[]>>("/employees/available-tools")); }
export async function listEmployees() { return unwrap(await api.get<APIResponse<Employee[]>>("/employees")); }
export async function getEmployee(id: string) { return unwrap(await api.get<APIResponse<Employee>>(`/employees/${id}`)); }
export async function createEmployee(payload: EmployeeCreate) { return unwrap(await api.post<APIResponse<Employee>>("/employees", payload)); }
export async function listRuns(employeeId?: string) { const params = employeeId ? { employee_id: employeeId } : undefined; return unwrap(await api.get<APIResponse<Run[]>>("/runs", { params })); }
export async function getRun(id: string) { return unwrap(await api.get<APIResponse<Run>>(`/runs/${id}`)); }
export async function createRun(payload: RunCreate) { return unwrap(await api.post<APIResponse<Run>>("/runs", payload)); }
export async function getRunTrace(id: string) { return unwrap(await api.get<APIResponse<RunTrace>>(`/runs/${id}/trace`)); }
export async function getOperationsMetrics() { return unwrap(await api.get<APIResponse<OperationsMetrics>>("/operations/metrics")); }
export async function getAuditLogs(params?: { limit?: number; action?: string; status_filter?: string }) { return unwrap(await api.get<APIResponse<AuditLog[]>>("/operations/audit-logs", { params })); }
export async function listDeadLetters(limit = 50) { return unwrap(await api.get<APIResponse<DeadLetter[]>>("/operations/dead-letters", { params: { limit } })); }
export async function replayDeadLetter(id: string) { return unwrap(await api.post<APIResponse<Record<string, unknown>>>(`/operations/dead-letters/${id}/replay`)); }
export async function getUsageSummary(params?: { from_at?: string; to_at?: string }) { return unwrap(await api.get<APIResponse<UsageSummary>>("/usage/summary", { params })); }
export async function listFiles() { return unwrap(await api.get<APIResponse<FileItem[]>>("/files")); }
export async function deleteFile(id: string) { await api.delete(`/files/${id}`); }
export async function getCustomerDashboard() { return unwrap(await api.get<APIResponse<unknown>>("/customer-dashboard")); }
export async function getErrorMessage(error: unknown) { return error instanceof Error ? error.message : "Request failed"; }
export async function listApprovals(status?: string) { const params = status ? { status } : undefined; return unwrap(await api.get<APIResponse<ToolApproval[]>>("/approvals", { params })); }
export async function decideApproval(id: string, decision: "approve" | "reject", reason?: string) { return unwrap(await api.post<APIResponse<ToolApproval>>(`/approvals/${id}/decision`, { decision, reason })); }
export async function listWorkflowApprovals(status?: string) { const params = status ? { status_filter: status } : undefined; return unwrap(await api.get<APIResponse<WorkflowApproval[]>>("/workflow-approvals", { params })); }
export async function decideWorkflowApproval(id: string, decision: "approve" | "reject", reason?: string) { return unwrap(await api.post<APIResponse<WorkflowApproval>>(`/workflow-approvals/${id}/decision`, { decision, reason })); }
