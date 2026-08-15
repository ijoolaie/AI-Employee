"use client";

import { useState } from "react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { cancelSubscription, changeSubscription, createCheckoutSession, createPortalSession, getBillingEntitlements, getErrorMessage, getSubscription, listBillingPlans } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export default function BillingPage() {
  const qc = useQueryClient();
  const [message, setMessage] = useState<string | null>(null);
  const plans = useQuery({ queryKey: ["billing-plans"], queryFn: listBillingPlans });
  const subscription = useQuery({ queryKey: ["subscription"], queryFn: getSubscription });
  const entitlements = useQuery({ queryKey: ["billing-entitlements"], queryFn: getBillingEntitlements });
  const change = useMutation({ mutationFn: changeSubscription, onSuccess: () => { setMessage("Subscription updated."); qc.invalidateQueries({ queryKey: ["subscription"] }); }, onError: (e) => setMessage(getErrorMessage(e)) });
  const cancel = useMutation({ mutationFn: cancelSubscription, onSuccess: () => { setMessage("Cancellation scheduled for the end of the current period."); qc.invalidateQueries({ queryKey: ["subscription"] }); }, onError: (e) => setMessage(getErrorMessage(e)) });
  // Phase 6 — real Stripe Checkout for paid plans; the browser is
  // redirected to Stripe's own hosted payment page, so card data never
  // touches this frontend or backend.
  const checkout = useMutation({
    mutationFn: createCheckoutSession,
    onSuccess: (data) => { window.location.href = data.checkout_url; },
    onError: (e) => setMessage(getErrorMessage(e)),
  });
  const portal = useMutation({
    mutationFn: createPortalSession,
    onSuccess: (data) => { window.location.href = data.portal_url; },
    onError: (e) => setMessage(getErrorMessage(e)),
  });

  function choosePlan(planCode: string) {
    if (planCode === "starter") {
      change.mutate(planCode);
    } else {
      checkout.mutate(planCode);
    }
  }

  return <>
    <Header title="Billing" description="Plans, subscription and usage entitlements" />
    <div className="space-y-6 p-6">
      {message && <div className="rounded-lg border border-gray-200 bg-white px-4 py-3 text-sm text-gray-700">{message}</div>}
      {subscription.isLoading || plans.isLoading ? <Spinner /> : null}
      {subscription.data?.status === "trialing" && subscription.data.trial_ends_at && <div className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800">Free trial ends on <strong>{new Date(subscription.data.trial_ends_at).toLocaleDateString()}</strong>. Your limits are enforced during the trial; upgrade anytime.</div>}
      {entitlements.data && <Card><CardHeader><CardTitle>Current usage</CardTitle></CardHeader><CardContent className="grid gap-4 md:grid-cols-4 text-sm"><div><p className="text-gray-500">Runs</p><p className="font-semibold">{entitlements.data.usage.runs.toLocaleString()} / {entitlements.data.plan.monthly_runs.toLocaleString()}</p></div><div><p className="text-gray-500">AI tokens</p><p className="font-semibold">{entitlements.data.usage.tokens.toLocaleString()} / {entitlements.data.plan.monthly_tokens.toLocaleString()}</p></div><div><p className="text-gray-500">Employees</p><p className="font-semibold">{entitlements.data.usage.employees} / {entitlements.data.plan.max_employees}</p></div><div><p className="text-gray-500">Workflows</p><p className="font-semibold">{entitlements.data.usage.workflows} / {entitlements.data.plan.max_workflows}</p></div></CardContent></Card>}
      {subscription.data && <Card><CardHeader><CardTitle>Current subscription</CardTitle></CardHeader><CardContent className="grid gap-4 md:grid-cols-4 text-sm">
        <div><p className="text-gray-500">Plan</p><p className="font-semibold text-gray-900">{subscription.data.plan.name}</p></div>
        <div><p className="text-gray-500">Status</p><p className="font-semibold text-gray-900">{subscription.data.status}</p></div>
        <div><p className="text-gray-500">Monthly price</p><p className="font-semibold text-gray-900">{formatCurrency(Number(subscription.data.plan.monthly_price_usd))}</p></div>
        <div><p className="text-gray-500">Period end</p><p className="font-semibold text-gray-900">{new Date(subscription.data.current_period_end).toLocaleDateString()}</p></div>
      </CardContent></Card>}
      {subscription.data?.provider === "stripe" && (
        <button
          onClick={() => portal.mutate()}
          disabled={portal.isPending}
          className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        >
          {portal.isPending ? "Opening…" : "Manage billing (Stripe)"}
        </button>
      )}
      <div className="grid gap-4 md:grid-cols-3">
        {plans.data?.map((plan) => <Card key={plan.code} className={subscription.data?.plan.code === plan.code ? "ring-2 ring-brand-500" : ""}>
          <CardHeader><CardTitle>{plan.name}</CardTitle><p className="text-2xl font-semibold">{formatCurrency(Number(plan.monthly_price_usd))}<span className="text-sm font-normal text-gray-500"> / month</span></p></CardHeader>
          <CardContent className="space-y-2 text-sm text-gray-600">
            <p>{plan.monthly_runs.toLocaleString()} workflow runs / month</p><p>{plan.monthly_tokens.toLocaleString()} AI tokens / month</p><p>Up to {plan.max_employees} employees</p><p>Up to {plan.max_workflows} workflows</p>
            <button
              disabled={change.isPending || checkout.isPending || subscription.data?.plan.code === plan.code}
              onClick={() => choosePlan(plan.code)}
              className="mt-3 w-full rounded-lg bg-brand-600 px-4 py-2 font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {subscription.data?.plan.code === plan.code
                ? "Current plan"
                : checkout.isPending
                ? "Redirecting to Stripe…"
                : plan.code === "starter"
                ? `Choose ${plan.name}`
                : `Subscribe to ${plan.name} — Stripe Checkout`}
            </button>
          </CardContent>
        </Card>)}
      </div>
      {subscription.data?.status === "active" && !subscription.data.cancel_at_period_end && subscription.data.plan.code !== "starter" && <button onClick={() => cancel.mutate(true)} disabled={cancel.isPending} className="rounded-lg border border-red-200 px-4 py-2 text-sm font-medium text-red-700 disabled:opacity-50">Cancel at period end</button>}
    </div>
  </>;
}
