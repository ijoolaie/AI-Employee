import { api } from "./api";

type APIResponse<T> = { success: boolean; data?: T };

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
  const res = await api.get<APIResponse<WorkItemSummary[]>>("/work-items", { params });
  if (!res.data.success || res.data.data === undefined) throw new Error("Unexpected API response");
  return res.data.data;
}

export async function dispatchWorkItem(id: string) {
  const res = await api.post<APIResponse<WorkItemExecutionResponse>>(`/work-items/${id}/dispatch`);
  if (!res.data.success || res.data.data === undefined) throw new Error("Unexpected API response");
  return res.data.data;
}
