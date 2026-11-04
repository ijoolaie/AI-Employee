"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { api, getErrorMessage } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface AcceptanceResponse {
  activated: boolean;
  message: string;
}

function AcceptInvitationForm() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [result, setResult] = useState<AcceptanceResponse | null>(null);


  const accept = useMutation({
    mutationFn: async () => {
      const response = await api.post<{ success: boolean; data: AcceptanceResponse }>("/auth/invitations/accept", { token: token.trim(), password });
      if (!response.data.success) throw new Error("Invitation could not be accepted.");
      return response.data.data;
    },
    onSuccess: setResult,
  });

  const canSubmit = token.trim().length >= 32 && password.length >= 12 && password === confirmPassword;

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <Card className="w-full max-w-lg">
        <CardHeader><CardTitle>Accept your workspace invitation</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          {result ? (
            <div role="status" className="space-y-3">
              <p>{result.message}</p>
              {result.activated ? (
                <button onClick={() => router.push("/login")} className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white">Continue to sign in</button>
              ) : (
                <p className="text-sm text-gray-600">Your password is set. You will be able to sign in once the workspace receives an approved payment or Demo grant.</p>
              )}
            </div>
          ) : (
            <>
              <label className="grid gap-1 text-sm"><span>Invitation token</span><textarea value={token} onChange={event => setToken(event.target.value)} rows={3} autoComplete="off" className="rounded-lg border px-3 py-2 font-mono text-xs" /></label>
              <label className="grid gap-1 text-sm"><span>Create password</span><input type="password" value={password} onChange={event => setPassword(event.target.value)} autoComplete="new-password" minLength={12} className="rounded-lg border px-3 py-2" /></label>
              <label className="grid gap-1 text-sm"><span>Confirm password</span><input type="password" value={confirmPassword} onChange={event => setConfirmPassword(event.target.value)} autoComplete="new-password" minLength={12} className="rounded-lg border px-3 py-2" /></label>
              {password && confirmPassword && password !== confirmPassword && <p className="text-sm text-red-600">Passwords do not match.</p>}
              {accept.isError && <p role="alert" className="text-sm text-red-600">{getErrorMessage(accept.error)}</p>}
              <button disabled={!canSubmit || accept.isPending} onClick={() => accept.mutate()} className="w-full rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">{accept.isPending ? "Accepting invitation..." : "Accept invitation"}</button>
            </>
          )}
        </CardContent>
      </Card>
    </main>
  );
}


export default function AcceptInvitationPage() {
  return <AcceptInvitationForm />;
}
