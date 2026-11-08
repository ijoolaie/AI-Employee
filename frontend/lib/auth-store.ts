"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Tenant, User } from "@/types";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  homeRefreshToken: string | null;
  portalContextActive: boolean;
  user: User | null;
  tenant: Tenant | null;
  sessionVersion: number;
  setTokens: (access: string, refresh: string) => void;
  beginSession: (access: string, refresh: string) => void;
  beginPortalSession: (access: string, refresh: string) => void;
  setSession: (user: User, tenant: Tenant) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      homeRefreshToken: null,
      portalContextActive: false,
      user: null,
      tenant: null,
      sessionVersion: 0,
      setTokens: (access, refresh) =>
        set((state) => ({
          accessToken: access,
          refreshToken: refresh,
          // Keep the home credential rotating with home sessions, but never
          // overwrite it with a delegated portal refresh token.
          homeRefreshToken:
            state.portalContextActive || (state.user && state.tenant && state.user.tenant_id !== state.tenant.id)
              ? state.homeRefreshToken
              : refresh,
        })),
      // Start a new login without retaining the previous account identity.
      // TenantQueryCacheBoundary observes the reset and clears cached data.
      beginSession: (access, refresh) =>
        set((state) => ({
          accessToken: access,
          refreshToken: refresh,
          homeRefreshToken: refresh,
          portalContextActive: false,
          user: null,
          tenant: null,
          sessionVersion: state.sessionVersion + 1,
        })),
      beginPortalSession: (access, refresh) =>
        set((state) => ({
          accessToken: access,
          refreshToken: refresh,
          homeRefreshToken: state.homeRefreshToken ?? state.refreshToken,
          portalContextActive: true,
          user: null,
          tenant: null,
          sessionVersion: state.sessionVersion + 1,
        })),
      setSession: (user, tenant) => set({ user, tenant }),
      logout: () =>
        set((state) => ({
          accessToken: null,
          refreshToken: null,
          homeRefreshToken: null,
          portalContextActive: false,
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
        homeRefreshToken: s.homeRefreshToken,
        portalContextActive: s.portalContextActive,
        user: s.user,
        tenant: s.tenant,
      }),
    }
  )
);
