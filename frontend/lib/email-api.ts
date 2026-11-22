import { api } from "@/lib/api";
import type { APIResponse } from "@/types";

type EmailChangeResponse = APIResponse<{ message: string }> & {
  error?: { code: string; message: string; details?: Record<string, unknown> };
};

export async function requestEmailChange(payload: { current_password: string; new_email: string }) {
  const response = await api.post<EmailChangeResponse>("/auth/email-change/request", payload);
  if (!response.data.success || response.data.data === undefined) {
    throw new Error(response.data.error?.message || "Unable to request email change");
  }
  return response.data.data;
}

export async function confirmEmailChange(token: string) {
  const response = await api.post<EmailChangeResponse>("/auth/email-change/confirm", { token });
  if (!response.data.success || response.data.data === undefined) {
    throw new Error(response.data.error?.message || "Unable to confirm email change");
  }
  return response.data.data;
}
