"use client";

import { Suspense, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { fetchMe, getErrorMessage, login } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { canEnterPortal, defaultPortalForAccount, portalPath, type PortalKind } from "@/lib/portal-access";

const schema = z.object({
  email: z.string().email("Valid email required"),
  password: z.string().min(1, "Password required"),
  tenant_slug: z.string().min(2, "Tenant slug required").regex(/^[a-z0-9-]+$/, "Lowercase letters, numbers, hyphens only"),
});

type FormData = z.infer<typeof schema>;

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { beginSession, setSession } = useAuthStore();
  const rawPortal = searchParams.get("portal");
  const requestedPortal: PortalKind = rawPortal === "vendor" || rawPortal === "reseller" ? rawPortal : "customer";
  const portalLabels: Record<PortalKind, string> = { vendor: "Vendor portal", reseller: "Reseller portal", customer: "Customer portal" };
  const [error, setError] = useState<string | null>(
    searchParams.get("reason") === "session"
      ? "Your session expired. Please sign in again."
      : null
  );

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "", tenant_slug: "" },
  });

  async function onSubmit(data: FormData) {
    setError(null);
    try {
      const tokens = await login(data);
      beginSession(tokens.access_token, tokens.refresh_token);
      let me: Awaited<ReturnType<typeof fetchMe>>;
      try {
        me = await fetchMe();
      } catch (error) {
        // Do not leave a token-only session if identity resolution fails.
        useAuthStore.getState().logout();
        throw error;
      }
      setSession(me.user, me.tenant);
      if (!me.tenant.access_granted) {
        router.replace("/billing");
        return;
      }
      const tenantKind = (me.tenant as typeof me.tenant & { tenant_kind?: string }).tenant_kind;
      const accountKind = me.user.is_platform_admin ? "platform-admin" : tenantKind ?? "customer";
      if (me.user.is_platform_admin) {
        router.replace("/admin");
        return;
      }
      if (!canEnterPortal(accountKind, requestedPortal)) {
        const fallback = defaultPortalForAccount(accountKind);
        router.replace(portalPath(fallback === "admin" ? "customer" : fallback));
        return;
      }
      router.replace(portalPath(requestedPortal));
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Sign in to {portalLabels[requestedPortal]}</h1>
      <p className="mt-1 text-sm text-gray-500">
        Enter your tenant and credentials. Your account permissions determine which portals you can use.
      </p>
      <nav aria-label="Choose portal" className="mt-4 grid grid-cols-3 gap-2 text-sm">
        {(["customer", "reseller", "vendor"] as PortalKind[]).map((portal) => (
          <Link key={portal} href={`/login/${portal}`} aria-current={requestedPortal === portal ? "page" : undefined}
            className={`rounded-lg border px-2 py-2 text-center ${requestedPortal === portal ? "border-brand-600 bg-brand-50 font-semibold text-brand-700" : "border-gray-200 text-gray-600 hover:bg-gray-50"}`}>
            {portalLabels[portal]}
          </Link>
        ))}
      </nav>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-4">
        <Input label="Tenant slug" placeholder="acme-corp" error={errors.tenant_slug?.message} {...register("tenant_slug")} />
        <Input label="Email" type="email" placeholder="you@company.com" error={errors.email?.message} {...register("email")} />
        <Input label="Password" type="password" placeholder="••••••••" error={errors.password?.message} {...register("password")} />
        {error && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? "Signing in…" : "Sign in"}
        </Button>
      </form>

      <p className="mt-4 text-center text-sm"><Link href="/forgot-password" className="font-medium text-brand-600 hover:text-brand-700">Forgot your password?</Link></p>
      <p className="mt-6 text-center text-sm text-gray-500">
        No account?{" "}
        <Link href="/register" className="font-medium text-brand-600 hover:text-brand-700">Create one</Link>
      </p>
    </div>
  );
}

export default function LoginPage() {
  return <Suspense fallback={<Spinner className="min-h-[240px]" />}><LoginForm /></Suspense>;
}
