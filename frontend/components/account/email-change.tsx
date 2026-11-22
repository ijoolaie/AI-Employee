"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { requestEmailChange, confirmEmailChange } from "@/lib/email-api";
import { getErrorMessage } from "@/lib/errors";
import { useI18n } from "@/lib/i18n/provider";

export function EmailChangeSettings({ basePath }: { basePath: string }) {
  const { locale } = useI18n();
  const fa = locale === "fa";
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
    <Header title={fa ? "تغییر ایمیل ورود" : "Change sign-in email"} description={fa ? "پیش از تغییر ایمیل ورود، مالکیت آدرس جدید را تأیید کنید." : "Verify ownership before your login email is changed."} />
    <div className="mx-auto max-w-2xl p-6"><Card>
      <CardHeader><CardTitle>{fa ? "آدرس ایمیل جدید" : "New email address"}</CardTitle><p className="text-sm text-gray-500">{fa ? "ایمیل فعلی تا زمان تأیید آدرس جدید فعال می‌ماند. پس از تأیید، نشست‌های قبلی باطل می‌شوند." : "Your current email remains active until you verify the new address. Existing sessions will be signed out after confirmation."}</p></CardHeader>
      <CardContent>{success ? <div role="status" className="space-y-4"><p className="rounded-md bg-green-50 px-4 py-3 text-sm text-green-700">{fa ? "در صورت پیکربندی سرویس ایمیل، پیوند تأیید ارسال شده است. صندوق ورودی آدرس جدید را بررسی کنید. ایمیل فعلی تا زمان تأیید فعال می‌ماند." : "A verification link was queued if email delivery is configured. Check the new inbox. Your current email remains active until confirmation."}</p><Link href={basePath} className="text-sm underline">{fa ? "بازگشت به تنظیمات امنیت" : "Back to security"}</Link></div> : <form onSubmit={submit} className="space-y-5">
        <div className="space-y-2"><label htmlFor="email-change-password" className="text-sm font-medium">{fa ? "رمز عبور فعلی" : "Current password"}</label><input id="email-change-password" type="password" autoComplete="current-password" required maxLength={128} value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} className="w-full rounded-md border border-gray-300 px-3 py-2" /></div>
        <div className="space-y-2"><label htmlFor="new-email" className="text-sm font-medium">{fa ? "آدرس ایمیل جدید" : "New email address"}</label><input id="new-email" type="email" autoComplete="email" required maxLength={320} value={newEmail} onChange={e => setNewEmail(e.target.value)} className="w-full rounded-md border border-gray-300 px-3 py-2" /></div>
        {error && <div role="alert" className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
        <div className="flex flex-wrap items-center gap-3"><Button type="submit" loading={saving}>{saving ? (fa ? "در حال ارسال…" : "Sending…") : (fa ? "ارسال پیوند تأیید" : "Send verification link")}</Button><Link href={basePath} className="rounded-md border border-gray-300 px-4 py-2 text-sm">{fa ? "لغو" : "Cancel"}</Link></div>
      </form>}</CardContent>
    </Card></div>
  </>;
}

export function EmailChangeConfirmation({ backPath }: { backPath: string }) {
  const { locale } = useI18n();
  const fa = locale === "fa";
  const [token, setToken] = useState("");
  const [state, setState] = useState<"ready" | "submitting" | "success" | "error">("ready");
  const [message, setMessage] = useState(fa ? "برای ادامه، تأیید را انتخاب کنید." : "Review this request, then confirm to continue.");

  useEffect(() => {
    const value = new URLSearchParams(window.location.search).get("token") || "";
    if (!value) {
      setState("error");
      setMessage(fa ? "توکن پیوند تأیید وجود ندارد." : "The verification link is missing its token.");
    } else {
      setToken(value);
    }
  }, [fa]);

  async function confirm() {
    if (!token || state === "submitting" || state === "success") return;
    setState("submitting");
    try {
      await confirmEmailChange(token);
      setState("success");
      setMessage(fa ? "ایمیل ورود با موفقیت تغییر کرد. لطفاً با ایمیل جدید دوباره وارد شوید." : "Your sign-in email has been changed. Please sign in again using the new email address.");
    } catch (err) {
      setState("error");
      setMessage(err instanceof Error ? err.message : (fa ? "پیوند تأیید نامعتبر است یا منقضی شده است." : "The verification link is invalid or expired."));
    }
  }

  return <main className="mx-auto max-w-xl space-y-5 p-8">
    <h1 className="text-2xl font-semibold">{fa ? "تأیید تغییر ایمیل" : "Confirm email change"}</h1>
    <p role={state === "error" ? "alert" : "status"} className="text-sm text-gray-700">{message}</p>
    {token && state !== "success" && state !== "error" ? <Button type="button" onClick={confirm} loading={state === "submitting"}>{fa ? "تأیید تغییر ایمیل" : "Confirm email change"}</Button> : null}
    <Link href={backPath} className="text-sm underline">{fa ? "بازگشت به ورود" : "Back to sign in"}</Link>
  </main>;
}
