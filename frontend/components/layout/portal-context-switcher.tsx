"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  activatePortalAccessGrant,
  fetchMe,
  listMyPortalAccessGrants,
  restorePrimaryPortalSession,
} from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { defaultPortalForAccount, portalPath, type PortalKind } from "@/lib/portal-access";
import type { PortalAccessGrant } from "@/types";

interface GrantLoadState {
  key: string;
  grants: PortalAccessGrant[];
  error: string | null;
}

export function PortalContextSwitcher() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const tenant = useAuthStore((state) => state.tenant);
  const sessionVersion = useAuthStore((state) => state.sessionVersion);
  const portalContextActive = useAuthStore((state) => state.portalContextActive);
  const [grantLoadState, setGrantLoadState] = useState<GrantLoadState | null>(null);
  const [busyGrant, setBusyGrant] = useState<string | null>(null);
  const [returning, setReturning] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const activeContext = portalContextActive || Boolean(user && tenant && user.tenant_id !== tenant.id);
  const accountKind = tenant?.tenant_kind;
  const canSwitch = accountKind === "vendor" || accountKind === "reseller";
  const hasIdentity = Boolean(user && tenant);
  const identityKey = hasIdentity && user && tenant
    ? user.id + ":" + tenant.id + ":" + sessionVersion
    : null;
  const currentGrantState = grantLoadState?.key === identityKey ? grantLoadState : null;
  const grants = currentGrantState?.grants ?? [];
  const grantError = currentGrantState?.error ?? null;
  const loadingGrants = Boolean(identityKey && canSwitch && !activeContext && !currentGrantState);

  useEffect(() => {
    if (!identityKey || activeContext || !canSwitch) return;
    let active = true;
    void listMyPortalAccessGrants()
      .then((items) => {
        if (active) setGrantLoadState({ key: identityKey, grants: items, error: null });
      })
      .catch(() => {
        if (active) {
          setGrantLoadState({
            key: identityKey,
            grants: [],
            error: "Unable to load your portal access grants.",
          });
        }
      });
    return () => { active = false; };
  }, [identityKey, activeContext, canSwitch]);

  async function enterPortal(grant: PortalAccessGrant) {
    if (accountKind !== "vendor" && accountKind !== "reseller") return;
    setBusyGrant(grant.id);
    setActionError(null);
    try {
      const current = useAuthStore.getState();
      const sessionVersionAtStart = current.sessionVersion;
      const primaryRefreshToken = current.homeRefreshToken ?? current.refreshToken;
      if (!primaryRefreshToken) throw new Error("Your session cannot be switched safely. Sign in again.");
      const activated = await activatePortalAccessGrant(accountKind, grant.id);
      const latest = useAuthStore.getState();
      if (
        latest.sessionVersion !== sessionVersionAtStart ||
        (latest.homeRefreshToken ?? latest.refreshToken) !== primaryRefreshToken
      ) {
        throw new Error("Account changed while opening the delegated portal.");
      }
      latest.beginPortalSession(activated.access_token, activated.refresh_token);
      try {
        const me = await fetchMe();
        useAuthStore.getState().setSession(me.user, me.tenant);
        router.replace(portalPath(grant.target_kind as PortalKind));
      } catch (identityError) {
        useAuthStore.getState().logout();
        router.replace("/login");
        throw identityError;
      }
    } catch {
      setActionError("Unable to enter that portal. The grant or its entitlement may have changed.");
    } finally {
      setBusyGrant(null);
    }
  }

  async function returnToPrimaryPortal() {
    setReturning(true);
    setActionError(null);
    try {
      const me = await restorePrimaryPortalSession();
      const homePortal = defaultPortalForAccount(me.tenant.tenant_kind ?? "customer");
      router.replace(homePortal === "admin" ? "/admin" : portalPath(homePortal));
    } catch {
      setActionError("Unable to restore your primary account session. Please sign in again if this continues.");
    } finally {
      setReturning(false);
    }
  }

  if (!user || !tenant) return null;

  if (activeContext) {
    return (
      <div className="mx-3 rounded-lg border border-slate-700 bg-slate-900/70 p-3">
        <p className="text-xs font-semibold text-slate-200">Delegated portal</p>
        <p className="mt-1 text-xs text-slate-400">Viewing {tenant.name} with your primary account identity.</p>
        <button
          type="button"
          onClick={returnToPrimaryPortal}
          disabled={returning}
          className="mt-2 w-full rounded-md bg-slate-700 px-3 py-2 text-xs font-semibold text-white hover:bg-slate-600 disabled:opacity-50"
        >
          {returning ? "Returning…" : "Return to my account"}
        </button>
        {actionError && <p role="alert" className="mt-2 text-xs text-red-300">{actionError}</p>}
      </div>
    );
  }

  if (!canSwitch || (!loadingGrants && grants.length === 0 && !grantError)) return null;

  return (
    <div className="mx-3 rounded-lg border border-slate-700 bg-slate-900/70 p-3">
      <p className="text-xs font-semibold text-slate-200">Authorized portals</p>
      {loadingGrants && <p className="mt-2 text-xs text-slate-400">Loading available portals…</p>}
      {!loadingGrants && grants.map((grant) => (
        <button
          key={grant.id}
          type="button"
          onClick={() => void enterPortal(grant)}
          disabled={busyGrant !== null}
          className="mt-2 flex w-full items-center justify-between gap-2 rounded-md bg-slate-800 px-3 py-2 text-left text-xs text-slate-100 hover:bg-slate-700 disabled:opacity-50"
        >
          <span className="min-w-0 truncate">{grant.target_name}</span>
          <span className="shrink-0 text-slate-400">{busyGrant === grant.id ? "Opening…" : grant.target_kind}</span>
        </button>
      ))}
      {(actionError || grantError) && <p role="alert" className="mt-2 text-xs text-red-300">{actionError || grantError}</p>}
    </div>
  );
}
