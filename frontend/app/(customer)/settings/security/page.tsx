"use client";

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

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (newPassword !== confirmPassword) {
      setError("New password and confirmation do not match.");
      return;
    }
    setSaving(true);
    try {
      await changePassword({ current_password: currentPassword, new_password: newPassword });
      setSuccess(true);
      setTimeout(() => logout(), 900);
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
          <CardHeader><CardTitle>Change password</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={submit} className="space-y-4">
              <input aria-label="Current password" type={type} autoComplete="current-password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required placeholder="Current password" className="w-full rounded-md border px-3 py-2" />
              <input aria-label="New password" type={type} autoComplete="new-password" minLength={8} maxLength={128} value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required placeholder="New password" className="w-full rounded-md border px-3 py-2" />
              <input aria-label="Confirm new password" type={type} autoComplete="new-password" minLength={8} maxLength={128} value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required placeholder="Confirm new password" className="w-full rounded-md border px-3 py-2" />
              <label className="flex items-center gap-2 text-sm text-gray-600"><input type="checkbox" checked={showPasswords} onChange={(e) => setShowPasswords(e.target.checked)} /> Show passwords</label>
              {error && <div role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
              {success && <div role="status" className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">Password changed successfully. Signing you out…</div>}
              <button type="submit" disabled={saving || success} className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-60">{saving ? "Changing password…" : "Change password"}</button>
            </form>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
