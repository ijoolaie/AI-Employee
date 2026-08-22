import { api } from "@/lib/api";
import type { APIResponse } from "@/types";

type PasswordChangeResponse = APIResponse<{ message: string }> & {
  error?: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
};

export async function changePassword(payload: {
  current_password: string;
  new_password: string;
}) {
  const response = await api.post<PasswordChangeResponse>("/auth/change-password", payload);
  if (!response.data.success || response.data.data === undefined) {
    throw new Error(response.data.error?.message || "Unable to change password");
  }
  return response.data.data;
}
