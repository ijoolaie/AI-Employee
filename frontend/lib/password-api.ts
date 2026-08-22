import { api } from "@/lib/api";
import type { APIResponse } from "@/types";

export async function changePassword(payload: {
  current_password: string;
  new_password: string;
}) {
  const response = await api.post<APIResponse<{ message: string }>>("/auth/change-password", payload);
  if (!response.data.success || response.data.data === undefined) {
    throw new Error(response.data.error?.message || "Unable to change password");
  }
  return response.data.data;
}
