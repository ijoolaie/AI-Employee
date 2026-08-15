export type ApiRequestOptions = RequestInit & {
  tenantId?: string;
};

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (options.tenantId) headers.set("X-Tenant-Id", options.tenantId);

  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}
