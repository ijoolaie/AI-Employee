export type ApiError = {
  code?: string;
  message: string;
  request_id?: string;
  details?: unknown;
};

export function normalizeApiError(error: unknown): ApiError {
  if (typeof error === "object" && error !== null && "message" in error) {
    return error as ApiError;
  }
  return { message: "Something went wrong. Please try again." };
}
