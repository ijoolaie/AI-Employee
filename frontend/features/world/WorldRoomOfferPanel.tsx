"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

type CatalogueItem = {
  id: string;
  code: string;
  item_type: string;
  name: string;
  description: string | null;
  price_options: Record<string, unknown>;
  is_free: boolean;
};

type APIResponse<T> = { success: boolean; data?: T };

const CURRENCIES = [
  { code: "IRR", label: "ریال" },
  { code: "USD", label: "دلار آمریکا" },
  { code: "USDT", label: "تتر" },
] as const;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function WorldRoomOfferPanel({ onClose }: { onClose: () => void }) {
  const [currency, setCurrency] = useState<(typeof CURRENCIES)[number]["code"]>("IRR");
  const catalogueQuery = useQuery({
    queryKey: ["world-commerce-catalogue"],
    queryFn: async () => {
      const response = await api.get<APIResponse<CatalogueItem[]>>("/world-commerce/catalogue");
      if (!response.data.success || !Array.isArray(response.data.data)) {
        throw new Error("پاسخ کاتالوگ معتبر نیست.");
      }
      return response.data.data;
    },
    staleTime: 30_000,
    retry: 1,
  });

  const room = useMemo(
    () => catalogueQuery.data?.find((item) => item.item_type === "room" && !item.is_free) ?? null,
    [catalogueQuery.data],
  );
  const priceOption = room && isRecord(room.price_options[currency]) ? room.price_options[currency] : null;
  const amountValue = priceOption?.amount;
  const amount = typeof amountValue === "string" || typeof amountValue === "number"
    ? String(amountValue)
    : null;
  const providers = priceOption && Array.isArray(priceOption.providers)
    ? priceOption.providers.filter((provider): provider is string => typeof provider === "string")
    : [];
  const paymentMethods = priceOption && Array.isArray(priceOption.payment_methods)
    ? priceOption.payment_methods.filter((method): method is string => typeof method === "string")
    : [];

  return (
    <section role="dialog" aria-modal="true" aria-labelledby="world-room-offer-title" className="absolute bottom-4 left-4 right-4 z-30 mx-auto max-w-lg rounded-2xl border border-amber-300/30 bg-slate-950/95 p-5 text-slate-100 shadow-2xl backdrop-blur-xl">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-amber-200">Expansion opportunity</p>
          <h3 id="world-room-offer-title" className="mt-1 text-lg font-semibold">اتاق بعدی شرکت</h3>
        </div>
        <button type="button" onClick={onClose} className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm">بستن</button>
      </div>

      <p className="mt-3 text-sm leading-6 text-slate-300">پیشنهاد اجاره یک‌ماهه اتاق با ظرفیت یک کارمند و تجهیزات پایه. قیمت و روش‌های پرداخت فقط از کاتالوگ سمت سرور خوانده می‌شوند.</p>

      <div className="mt-4">
        <p className="mb-2 text-sm font-medium">واحد پول</p>
        <div className="grid grid-cols-3 gap-2">
          {CURRENCIES.map((item) => (
            <button key={item.code} type="button" aria-pressed={currency === item.code} onClick={() => setCurrency(item.code)}
              className={`rounded-lg border px-3 py-2 text-sm ${currency === item.code ? "border-amber-200 bg-amber-200/10 text-amber-100" : "border-slate-700 bg-slate-900 text-slate-300"}`}>
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {catalogueQuery.isLoading && <p role="status" className="mt-4 text-sm text-slate-400">در حال دریافت کاتالوگ معتبر…</p>}
      {catalogueQuery.error && (
        <div role="alert" className="mt-4 rounded-lg border border-red-500/30 bg-red-950/30 p-3 text-sm text-red-200">
          دریافت کاتالوگ ناموفق بود. قیمت یا روش پرداختی به‌صورت حدسی نمایش داده نمی‌شود.
          <button type="button" onClick={() => void catalogueQuery.refetch()} className="mr-2 underline">تلاش دوباره</button>
        </div>
      )}
      {catalogueQuery.isSuccess && !room && (
        <p className="mt-4 rounded-lg border border-slate-800 bg-slate-900 p-3 text-sm text-slate-300">در حال حاضر پیشنهاد فعال اتاق پولی در کاتالوگ ثبت نشده است.</p>
      )}
      {room && (
        <div className="mt-4 rounded-lg border border-slate-800 bg-slate-900 p-3">
          <p className="font-medium">{room.name}</p>
          {room.description && <p className="mt-1 text-sm text-slate-400">{room.description}</p>}
          {amount ? (
            <p className="mt-3 text-lg font-semibold text-amber-100">{amount} {currency}</p>
          ) : (
            <p className="mt-3 text-sm text-amber-100">برای این اتاق قیمت {CURRENCIES.find((item) => item.code === currency)?.label} در کاتالوگ تعریف نشده است.</p>
          )}
          {providers.length > 0 && <p className="mt-3 text-sm text-slate-300">ارائه‌دهندگان پیکربندی‌شده: {providers.join("، ")}</p>}
          {paymentMethods.length > 0 && <p className="mt-1 text-sm text-slate-300">روش‌های پیکربندی‌شده: {paymentMethods.join("، ")}</p>}
          {amount && providers.length > 0 && paymentMethods.length > 0 && (
            <p className="mt-3 text-xs text-slate-500">وجود پیکربندی به معنی فعال‌بودن درگاه واقعی نیست؛ تا زمان پیاده‌سازی تأیید امن پرداخت، این صفحه فقط پیش‌نمایش است.</p>
          )}
        </div>
      )}

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <span className="text-xs text-slate-500">پیش‌نمایش · پرداخت یا فعال‌سازی انجام نمی‌شود</span>
        <button type="button" onClick={onClose} className="rounded-lg bg-amber-200 px-4 py-2 text-sm font-semibold text-slate-950">متوجه شدم</button>
      </div>
    </section>
  );
}
