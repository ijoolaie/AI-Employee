"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Tenant, User } from "@/types";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  tenant: Tenant | null;
  setTokens: (access: string, refresh: string) => void;
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
      setTokens: (access, refresh) =>
        set({ accessToken: access, refreshToken: refresh }),
      setSession: (user, tenant) => set({ user, tenant }),
      logout: () =>
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
          tenant: null,
        }),
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
