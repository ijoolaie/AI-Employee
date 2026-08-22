"use client";

import Link from "next/link";
import { useState } from "react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/lib/auth-store";
import { changePassword } from "@/lib/password-api";
import { getErrorMessage } from "@/lib/errors";

export default function SecuritySettingsPage() {
  const { logout } = useAuthStore();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPasswords, setShowPasswords] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const requirements = [
    { label: "At least 8 characters", valid: newPassword.length >= 8 },
    { label: "No more than 128 characters", valid: newPassword.length <= 128 },
    {
      label: "New password and confirmation match",
      valid: newPassword.length > 0 && newPassword === confirmPassword,
    },
  ];

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (newPassword.length < 8 || newPassword.length > 128) {
      setError("New password must be between 8 and 128 characters.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("New password and confirmation do not match.");
      return;
    }

    setSaving(true);
    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setSuccess(true);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  const type = showPasswords ? "text" : "password";

  return (
    <>
      <Header title="Security" description="Manage your account password" />
      <div className="mx-auto max-w-2xl p-6">
        <Card>
          <CardHeader>
            <CardTitle>Change password</CardTitle>
            <p className="text-sm text-gray-500">
              Update your password without leaving the Settings area. For your
              protection, you will need to sign in again after a successful change.
            </p>
          </CardHeader>
          <CardContent>
            {success ? (
              <div className="space-y-5">
                <div role="status" className="rounded-md bg-green-50 px-4 py-3 text-sm text-green-700">
                  Password changed successfully. Your current session is no longer valid.
                </div>
                <button
                  type="button"
                  onClick={logout}
                  className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
                >
                  Sign in again
                </button>
              </div>
            ) : (
              <form onSubmit={submit} className="space-y-5">
                <div className="space-y-2">
                  <label htmlFor="current-password" className="text-sm font-medium text-gray-700">
                    Current password
                  </label>
                  <input
                    id="current-password"
                    aria-label="Current password"
                    type={type}
                    autoComplete="current-password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    required
                    className="w-full rounded-md border border-gray-300 px-3 py-2 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
                  />
                </div>

                <div className="space-y-2">
                  <label htmlFor="new-password" className="text-sm font-medium text-gray-700">
                    New password
                  </label>
                  <input
                    id="new-password"
                    aria-label="New password"
                    type={type}
                    autoComplete="new-password"
                    minLength={8}
                    maxLength={128}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    className="w-full rounded-md border border-gray-300 px-3 py-2 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
                  />
                </div>

                <div className="space-y-2">
                  <label htmlFor="confirm-password" className="text-sm font-medium text-gray-700">
                    Confirm new password
                  </label>
                  <input
                    id="confirm-password"
                    aria-label="Confirm new password"
                    type={type}
                    autoComplete="new-password"
                    minLength={8}
                    maxLength={128}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    className="w-full rounded-md border border-gray-300 px-3 py-2 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
                  />
                </div>

                <div className="rounded-md bg-gray-50 px-4 py-3">
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Password requirements
                  </p>
                  <ul className="space-y-1 text-sm">
                    {requirements.map((requirement) => (
                      <li key={requirement.label} className={requirement.valid ? "text-green-700" : "text-gray-500"}>
                        {requirement.valid ? "✓" : "•"} {requirement.label}
                      </li>
                    ))}
                  </ul>
                </div>

                <label className="flex items-center gap-2 text-sm text-gray-600">
                  <input
                    type="checkbox"
                    checked={showPasswords}
                    onChange={(e) => setShowPasswords(e.target.checked)}
                  />
                  Show passwords
                </label>

                {error && (
                  <div role="alert" className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
                    {error}
                  </div>
                )}

                <div className="flex flex-wrap items-center gap-3">
                  <button
                    type="submit"
                    disabled={saving}
                    className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {saving ? "Changing password…" : "Change password"}
                  </button>
                  <Link
                    href="/settings"
                    className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </Link>
                </div>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
