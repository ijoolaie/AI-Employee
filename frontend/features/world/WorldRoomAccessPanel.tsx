"use client";

import { getRoomLeaseExpiryStatus } from "./world-room-expiry";

type AccessState = "loading" | "unavailable" | "granted";

export function WorldRoomAccessPanel({
  state,
  itemCode,
  expiresAt,
  roomInstanceId,
  onClose,
  onRetry,
}: {
  state: AccessState;
  itemCode: string;
  expiresAt: string | null;
  roomInstanceId: string | null;
  onClose: () => void;
  onRetry: () => void;
}) {
  const expiry = expiresAt && getRoomLeaseExpiryStatus(expiresAt).kind !== "unknown"
    ? new Intl.DateTimeFormat("fa-IR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(expiresAt))
    : null;
  const expiryStatus = getRoomLeaseExpiryStatus(expiresAt);

  return (
    <section role="dialog" aria-modal="true" aria-labelledby="world-room-access-title" className="absolute bottom-4 left-4 right-4 z-30 mx-auto max-w-lg rounded-2xl border border-cyan-300/30 bg-slate-950/95 p-5 text-slate-100 shadow-2xl backdrop-blur-xl">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-cyan-200">Server-authorized room access</p>
          <h3 id="world-room-access-title" className="mt-1 text-lg font-semibold">دسترسی اتاق شرکت</h3>
        </div>
        <button type="button" onClick={onClose} className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm">بستن</button>
      </div>

      {state === "loading" && <p role="status" className="mt-4 text-sm text-slate-300">در حال بررسی دسترسی اتاق از سرور؛ تا زمان تأیید، دسترسی فعال فرض نمی‌شود.</p>}
      {state === "unavailable" && (
        <div className="mt-4 rounded-lg border border-amber-400/30 bg-amber-950/20 p-3 text-sm text-amber-100">
          <p role="alert">وضعیت مجوز از سرور قابل تأیید نیست. دسترسی اتاق مسدود می‌ماند.</p>
          <button type="button" onClick={onRetry} className="mt-3 rounded-lg border border-amber-200/30 px-3 py-2 text-xs hover:bg-amber-900/30">بررسی دوباره</button>
        </div>
      )}
      {state === "granted" && (
        <div className="mt-4 space-y-3 text-sm">
          <p className="text-emerald-200">سرور مجوز و نمونهٔ اتاق را تأیید کرده است؛ فضای سه‌بعدی تا پایان اعتبار نمایش داده می‌شود.</p>
          <p className="text-slate-300">کد اتاق: <span className="font-mono">{itemCode}</span>{expiry ? ` · اعتبار تا ${expiry}` : ""}</p>
          {expiryStatus.kind === "urgent" && (
            <p role="status" className="rounded-lg border border-amber-400/40 bg-amber-950/30 p-3 leading-6 text-amber-100">
              اعتبار اتاق {expiryStatus.daysRemaining} روز دیگر پایان می‌یابد. تمدید خودکار فعال نیست؛ ثبت سفارش به‌تنهایی پرداخت یا تمدید را انجام نمی‌دهد.
            </p>
          )}
          {expiryStatus.kind === "expired" && (
            <p role="alert" className="rounded-lg border border-red-400/40 bg-red-950/30 p-3 leading-6 text-red-100">
              زمان اعتبار ثبت‌شده گذشته است. برای تأیید وضعیت جاری، دسترسی را دوباره از سرور بررسی کنید؛ این پیام به‌تنهایی مجوز را تمدید نمی‌کند.
            </p>
          )}
          {expiryStatus.kind === "unknown" && (
            <p role="alert" className="rounded-lg border border-amber-400/40 bg-amber-950/30 p-3 leading-6 text-amber-100">
              تاریخ پایان اعتبار مشخص نیست؛ برای وضعیت معتبر به پاسخ تازهٔ سرور نیاز است.
            </p>
          )}
          {roomInstanceId && <p className="text-slate-300">شناسه نمونه: <span className="font-mono">{roomInstanceId}</span></p>}
          <p className="rounded-lg border border-slate-700 bg-slate-900 p-3 leading-6 text-slate-300">چیدمان مبلمان این اتاق از سرور بارگذاری و ذخیره می‌شود؛ جایگذاری کارمندان و سفارشی‌سازی پایدار مدیر هنوز تکمیل نشده است.</p>
        </div>
      )}
    </section>
  );
}
