"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Tenant, User } from "@/types";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  tenant: Tenant | null;
  sessionVersion: number;
  setTokens: (access: string, refresh: string) => void;
  beginSession: (access: string, refresh: string) => void;
  setSession: (user: User, tenant: Tenant) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      tenant: null,
      sessionVersion: 0,
      setTokens: (access, refresh) =>
        set({ accessToken: access, refreshToken: refresh }),
      // Start a new login without retaining the previous account identity.
      // TenantQueryCacheBoundary observes the reset and clears cached data.
      beginSession: (access, refresh) =>
        set((state) => ({
          accessToken: access,
          refreshToken: refresh,
          user: null,
          tenant: null,
          sessionVersion: state.sessionVersion + 1,
        })),
      setSession: (user, tenant) => set({ user, tenant }),
      logout: () =>
        set((state) => ({
          accessToken: null,
          refreshToken: null,
          user: null,
          tenant: null,
          sessionVersion: state.sessionVersion + 1,
        })),
      isAuthenticated: () => !!get().accessToken,
    }),
    {
      name: "aiep-auth",
      partialize: (s) => ({
        accessToken: s.accessToken,
        refreshToken: s.refreshToken,
        user: s.user,
        tenant: s.tenant,
      }),
    }
  )
);
