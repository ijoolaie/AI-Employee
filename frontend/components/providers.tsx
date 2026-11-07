"use client";

import { QueryClient, QueryClientProvider, useQueryClient } from "@tanstack/react-query";
import { useLayoutEffect, useState, type ReactNode } from "react";
import { useAuthStore } from "@/lib/auth-store";
import { I18nProvider } from "@/lib/i18n/provider";

function TenantQueryCacheBoundary() {
  const queryClient = useQueryClient();
  const userId = useAuthStore((state) => state.user?.id ?? null);
  const tenantId = useAuthStore((state) => state.tenant?.id ?? null);

  useLayoutEffect(() => {
    // Query keys across the app are not all tenant-qualified. Clear before
    // paint so cached tenant data cannot flash across account/tenant switches.
    queryClient.clear();
  }, [queryClient, userId, tenantId]);

  return null;
}

export function Providers({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={client}>
      <TenantQueryCacheBoundary />
      <I18nProvider>{children}</I18nProvider>
    </QueryClientProvider>
  );
}
