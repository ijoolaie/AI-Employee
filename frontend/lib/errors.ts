import axios from "axios";

export function getErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as
      | {
          error?: { message?: string; code?: string };
          detail?: string | Array<{ msg?: string; message?: string }>;
          message?: string;
        }
      | undefined;

    // Our API envelope
    if (data?.error?.message) return data.error.message;

    // FastAPI HTTPException detail (string)
    if (typeof data?.detail === "string") return data.detail;

    // FastAPI validation errors (array)
    if (Array.isArray(data?.detail)) {
      const parts = data.detail
        .map((d) => d.msg || d.message)
        .filter(Boolean);
      if (parts.length) return parts.join("; ");
    }

    if (data?.message) return data.message;

    if (err.response?.status === 401) return "Session expired. Please sign in again.";
    if (err.response?.status === 403) return "You do not have permission for this action.";
    if (err.response?.status === 404) return "Resource not found.";
    if (err.response?.status === 409) return "Conflict — resource already exists.";
    if (err.response?.status && err.response.status >= 500)
      return "Server error. Please try again later.";

    return err.message || "Request failed";
  }
  if (err instanceof Error) return err.message;
  return "Unknown error";
}
