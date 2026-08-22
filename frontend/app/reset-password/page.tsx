"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { resetPassword } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function ResetPasswordPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setMessage("");

    if (!token) {
      setError("This password reset link is missing its token. Please request a new reset email.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const result = await resetPassword({ token, password });
      setMessage(result.message || "Your password has been reset successfully.");

      // The backend invalidates previously issued JWT sessions after a
      // password change. Clear any local session before returning to login.
      useAuthStore.getState().logout();

      window.setTimeout(() => {
        router.replace("/login?reason=password-reset");
      }, 1200);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to reset your password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Set a new password</h1>
      <p className="mt-1 text-sm text-gray-500">
        Enter your new password below. The reset link can only be used once.
      </p>

      <form onSubmit={submit} className="mt-8 space-y-4">
        <Input
          label="New password"
          type="password"
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="At least 8 characters"
          minLength={8}
          maxLength={128}
          required
          disabled={!token}
        />
        <Input
          label="Confirm new password"
          type="password"
          autoComplete="new-password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          placeholder="Enter the password again"
          minLength={8}
          maxLength={128}
          required
          disabled={!token}
        />

        {!token && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            This reset link is invalid because no reset token was provided.
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        {message && (
          <div className="rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-700">
            {message}
          </div>
        )}

        <Button type="submit" className="w-full" loading={loading} disabled={!token}>
          Reset password
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-gray-500">
        <Link href="/forgot-password" className="font-medium text-brand-600 hover:text-brand-700">
          Request a new reset link
        </Link>
      </p>
    </div>
  );
}
