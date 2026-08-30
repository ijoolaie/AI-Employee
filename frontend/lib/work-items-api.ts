import { api } from "./api";

type APIResponse<T> = { success: boolean; data?: T };
type WorkItemResponse<T> = T | APIResponse<T>;

function unwrapWorkItem<T>(response: WorkItemResponse<T>): T {
  if (Array.isArray(response)) return response as T;
  if (typeof response === "object" && response !== null && "success" in response) {
    const envelope = response as APIResponse<T>;
    if (!envelope.success || envelope.data === undefined) throw new Error("Unexpected API response");
    return envelope.data;
  }
  return response as T;
}

export interface WorkItemSummary {
  id: string;
  title: string;
  description: string | null;
  status: string;
  priority: number;
  requester_id: string | null;
  executor_type: string | null;
  executor_id: string | null;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface WorkItemExecutionResponse {
  work_item_id: string;
  status: string;
  dispatched: boolean;
  waiting_for_approval: boolean;
}

export async function listWorkItems(params?: { status?: string; limit?: number }) {
  const res = await api.get<WorkItemResponse<WorkItemSummary[]>>("/work-items", { params });
  return unwrapWorkItem(res.data);
}

export async function dispatchWorkItem(id: string) {
  const res = await api.post<WorkItemResponse<WorkItemExecutionResponse>>(`/work-items/${id}/dispatch`);
  return unwrapWorkItem(res.data);
}

export async function cancelWorkItem(id: string) {
  const res = await api.post<WorkItemResponse<WorkItemExecutionResponse>>(`/work-items/${id}/cancel`);
  return unwrapWorkItem(res.data);
}

export async function retryWorkItem(id: string) {
  const res = await api.post<WorkItemResponse<WorkItemExecutionResponse>>(`/work-items/${id}/retry`);
  return unwrapWorkItem(res.data);
}
