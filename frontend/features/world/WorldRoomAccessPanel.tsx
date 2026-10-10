"use client";

type AccessState = "loading" | "unavailable" | "denied" | "granted";

export function WorldRoomAccessPanel({
  state,
  itemCode,
  expiresAt,
  roomInstanceId,
  onClose,
  onRetry,
  onRent,
}: {
  state: AccessState;
  itemCode: string;
  expiresAt: string | null;
  roomInstanceId: string | null;
  onClose: () => void;
  onRetry: () => void;
  onRent: () => void;
}) {
  const expiry = expiresAt
    ? new Intl.DateTimeFormat("fa-IR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(expiresAt))
    : null;

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
      {state === "denied" && (
        <div className="mt-4 rounded-lg border border-slate-700 bg-slate-900 p-3 text-sm text-slate-200">
          <p role="status">برای این اتاق نمونهٔ موجودی با مجوز فعال پیدا نشد؛ اتاق همچنان قفل است.</p>
          <button type="button" onClick={onRent} className="mt-3 rounded-lg border border-amber-200/30 px-3 py-2 text-xs text-amber-100 hover:bg-amber-900/30">مشاهده پیشنهاد اجاره</button>
        </div>
      )}
      {state === "granted" && (
        <div className="mt-4 space-y-3 text-sm">
          <p className="text-emerald-200">سرور مجوز و نمونهٔ پایدار اتاق را تأیید کرده است؛ فضای سه‌بعدی اتاق در صحنه نمایش داده می‌شود.</p>
          <p className="text-slate-300">کد اتاق: <span className="font-mono">{itemCode}</span>{expiry ? ` · اعتبار تا ${expiry}` : ""}</p>
          {roomInstanceId && <p className="text-slate-300">شناسه نمونه: <span className="font-mono">{roomInstanceId}</span></p>}
          <p className="rounded-lg border border-slate-700 bg-slate-900 p-3 leading-6 text-slate-300">این نمونه از موجودی سمت سرور بارگذاری شده است. ذخیره‌سازی سفارشی‌سازی‌ها و چیدمان اختصاصی هنوز تکمیل نشده است.</p>
        </div>
      )}
    </section>
  );
}
