"use client";
import Link from "next/link";
import { useState } from "react";
import { forgotPassword } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [tenantSlug, setTenantSlug] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setError(""); setMessage(""); setLoading(true);
    try { const result = await forgotPassword({ email, tenant_slug: tenantSlug }); setMessage(result.message); }
    catch (err) { setError(err instanceof Error ? err.message : "Unable to process the request."); }
    finally { setLoading(false); }
  }
  return <div>
    <h1 className="text-2xl font-bold text-gray-900">Forgot your password?</h1>
    <p className="mt-1 text-sm text-gray-500">Enter your tenant and account email. If the account exists, we&apos;ll send a reset link.</p>
    <form onSubmit={submit} className="mt-8 space-y-4">
      <Input label="Tenant slug" value={tenantSlug} onChange={e=>setTenantSlug(e.target.value)} placeholder="acme-corp" required />
      <Input label="Email" type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@company.com" required />
      {error && <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
      {message && <div className="rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-700">{message}</div>}
      <Button type="submit" className="w-full" loading={loading}>Send reset link</Button>
    </form>
    <p className="mt-6 text-center text-sm text-gray-500"><Link href="/login" className="font-medium text-brand-600 hover:text-brand-700">Back to sign in</Link></p>
  </div>;
}
