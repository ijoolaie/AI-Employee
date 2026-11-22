"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { requestEmailChange, confirmEmailChange } from "@/lib/email-api";
import { getErrorMessage } from "@/lib/errors";

export function EmailChangeSettings({ basePath }: { basePath: string }) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(null); setSaving(true);
    try { await requestEmailChange({ current_password: currentPassword, new_email: newEmail }); setSuccess(true); }
    catch (err) { setError(getErrorMessage(err) || "Unable to request email change."); }
    finally { setSaving(false); }
  }
  return <>
    <Header title="Change sign-in email" description="Verify ownership before your login email is changed." />
    <div className="mx-auto max-w-2xl p-6"><Card>
      <CardHeader><CardTitle>New email address</CardTitle><p className="text-sm text-gray-500">Your current email remains active until you verify the new address. Existing sessions will be signed out after confirmation.</p></CardHeader>
      <CardContent>{success ? <div role="status" className="space-y-4"><p className="rounded-md bg-green-50 px-4 py-3 text-sm text-green-700">A verification link was queued if email delivery is configured. Check the new inbox. Your current email remains active until confirmation.</p><Link href={basePath} className="text-sm underline">Back to security</Link></div> : <form onSubmit={submit} className="space-y-5">
        <div className="space-y-2"><label htmlFor="email-change-password" className="text-sm font-medium">Current password</label><input id="email-change-password" type="password" autoComplete="current-password" required maxLength={128} value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} className="w-full rounded-md border border-gray-300 px-3 py-2" /></div>
        <div className="space-y-2"><label htmlFor="new-email" className="text-sm font-medium">New email address</label><input id="new-email" type="email" autoComplete="email" required maxLength={320} value={newEmail} onChange={e => setNewEmail(e.target.value)} className="w-full rounded-md border border-gray-300 px-3 py-2" /></div>
        {error && <div role="alert" className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
        <div className="flex flex-wrap items-center gap-3"><Button type="submit" loading={saving}>{saving ? "Sending…" : "Send verification link"}</Button><Link href={basePath} className="rounded-md border border-gray-300 px-4 py-2 text-sm">Cancel</Link></div>
      </form>}</CardContent>
    </Card></div>
  </>;
}

export function EmailChangeConfirmation({ backPath }: { backPath: string }) {
  const [state, setState] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("Confirming your new email address…");
  useEffect(() => {
    let active = true;
    const token = new URLSearchParams(window.location.search).get("token") || "";
    if (!token) {
      setState("error");
      setMessage("The verification link is missing its token.");
    } else {
      confirmEmailChange(token).then(result => {
        if (!active) return;
        setState("success");
        setMessage(result.message);
      }).catch(err => {
        if (!active) return;
        setState("error");
        setMessage(err instanceof Error ? err.message : "The verification link is invalid or expired.");
      });
    }
    return () => { active = false; };
  }, []);
  return <main className="mx-auto max-w-xl space-y-5 p-8"><h1 className="text-2xl font-semibold">Confirm email change</h1><p role={state === "error" ? "alert" : "status"} className="text-sm text-gray-700">{message}</p>{state === "success" ? <p className="text-sm">Please sign out and sign in again using the new email address.</p> : null}<Link href={backPath} className="text-sm underline">Back to security settings</Link></main>;
}
