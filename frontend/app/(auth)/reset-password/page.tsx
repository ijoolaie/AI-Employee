"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { resetPassword } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

function ResetForm() {
  const params = useSearchParams();
  const token = params.get("token") || "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setError(""); setMessage("");
    if (!token) return setError("This reset link is missing its token.");
    if (password.length < 8) return setError("Password must be at least 8 characters.");
    if (password !== confirm) return setError("Passwords do not match.");
    setLoading(true);
    try { const result = await resetPassword({ token, password }); setMessage(result.message); }
    catch (err) { setError(err instanceof Error ? err.message : "This reset link is invalid or expired."); }
    finally { setLoading(false); }
  }
  return <div>
    <h1 className="text-2xl font-bold text-gray-900">Set a new password</h1>
    <p className="mt-1 text-sm text-gray-500">Choose a new password for your account.</p>
    <form onSubmit={submit} className="mt-8 space-y-4">
      <Input label="New password" type="password" value={password} onChange={e=>setPassword(e.target.value)} minLength={8} maxLength={128} required />
      <Input label="Confirm password" type="password" value={confirm} onChange={e=>setConfirm(e.target.value)} minLength={8} maxLength={128} required />
      {error && <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
      {message && <div className="rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-700">{message} <Link href="/login" className="font-semibold underline">Sign in</Link></div>}
      {!message && <Button type="submit" className="w-full" loading={loading}>Reset password</Button>}
    </form>
  </div>;
}
export default function ResetPasswordPage() { return <Suspense fallback={<div>Loading…</div>}><ResetForm /></Suspense>; }
