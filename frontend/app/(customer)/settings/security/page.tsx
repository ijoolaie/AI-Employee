"use client";

import Link from "next/link";
import { useState } from "react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/lib/auth-store";
import { changePassword } from "@/lib/password-api";
import { getErrorMessage } from "@/lib/errors";
import { useI18n } from "@/lib/i18n/provider";

export default function SecuritySettingsPage() {
  const { logout } = useAuthStore(); const { t }=useI18n(); const m=t.security;
  const [currentPassword,setCurrentPassword]=useState(""); const [newPassword,setNewPassword]=useState(""); const [confirmPassword,setConfirmPassword]=useState("");
  const [showPasswords,setShowPasswords]=useState(false); const [saving,setSaving]=useState(false); const [error,setError]=useState<string|null>(null); const [success,setSuccess]=useState(false);
  const requirements=[{label:m.minLength,valid:newPassword.length>=8},{label:m.maxLength,valid:newPassword.length<=128},{label:m.match,valid:newPassword.length>0&&newPassword===confirmPassword}];
  async function submit(event:React.FormEvent<HTMLFormElement>){
    event.preventDefault();setError(null);
    if(newPassword.length<8||newPassword.length>128){setError(m.lengthError);return;}
    if(newPassword!==confirmPassword){setError(m.matchError);return;}
    setSaving(true);
    try{await changePassword({current_password:currentPassword,new_password:newPassword});setSuccess(true);}
    catch(err){setError(getErrorMessage(err) || m.updateError);} finally{setSaving(false);}
  }
  const type=showPasswords?"text":"password";
  return <><Header title={m.title} description={m.description}/><div className="mx-auto max-w-2xl p-6"><Card><CardHeader><CardTitle>{m.changePassword}</CardTitle><p className="text-sm text-gray-500">{m.changeDescription}</p></CardHeader><CardContent>
    {success?<div className="space-y-5"><div role="status" className="rounded-md bg-green-50 px-4 py-3 text-sm text-green-700">{m.success}</div><Button onClick={logout}>{m.signInAgain}</Button></div>:
    <form onSubmit={submit} className="space-y-5">
      <PasswordField id="current-password" label={m.currentPassword} auto="current-password" type={type} value={currentPassword} onChange={setCurrentPassword}/>
      <PasswordField id="new-password" label={m.newPassword} auto="new-password" type={type} value={newPassword} onChange={setNewPassword} minLength={8} maxLength={128}/>
      <PasswordField id="confirm-password" label={m.confirmPassword} auto="new-password" type={type} value={confirmPassword} onChange={setConfirmPassword} minLength={8} maxLength={128}/>
      <div className="rounded-md bg-gray-50 px-4 py-3"><p className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">{m.requirements}</p><ul className="space-y-1 text-sm">{requirements.map(r=><li key={r.label} className={r.valid?"text-green-700":"text-gray-500"}>{r.valid?"✓":"•"} {r.label}</li>)}</ul></div>
      <label className="flex items-center gap-2 text-sm text-gray-600"><input type="checkbox" checked={showPasswords} onChange={e=>setShowPasswords(e.target.checked)}/>{m.showPasswords}</label>
      {error&&<div role="alert" className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
      <div className="flex flex-wrap items-center gap-3"><Button type="submit" loading={saving}>{saving?m.saving:m.submit}</Button><Link href="/settings" className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">{m.cancel}</Link></div>
    </form>}
  </CardContent></Card></div></>;
}
function PasswordField({id,label,auto,type,value,onChange,minLength,maxLength}:{id:string;label:string;auto:string;type:"text"|"password";value:string;onChange:(v:string)=>void;minLength?:number;maxLength?:number}){
  return <div className="space-y-2"><label htmlFor={id} className="text-sm font-medium text-gray-700">{label}</label><input id={id} aria-label={label} type={type} autoComplete={auto} minLength={minLength} maxLength={maxLength} value={value} onChange={e=>onChange(e.target.value)} required className="w-full rounded-md border border-gray-300 px-3 py-2 text-start outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"/></div>;
}
