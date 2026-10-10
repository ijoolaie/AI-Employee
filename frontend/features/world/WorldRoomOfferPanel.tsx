"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
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

type WorldOrder = {
  id: string;
  item_code_snapshot: string;
  amount: string | number;
  currency: string;
  payment_method: string;
  payment_provider: string;
  status: string;
};

type APIResponse<T> = { success: boolean; data?: T };

const CURRENCIES = [
  { code: "IRR", label: "ریال" },
  { code: "USD", label: "دلار آمریکا" },
  { code: "USDT", label: "تتر" },
] as const;

const PAYMENT_METHOD_LABELS: Record<string, string> = {
  manual_transfer: "انتقال دستی",
  gateway: "درگاه پرداخت",
  crypto: "پرداخت رمزارزی",
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function WorldRoomOfferPanel({ onClose }: { onClose: () => void }) {
  const [currency, setCurrency] = useState<(typeof CURRENCIES)[number]["code"]>("IRR");
  const [selectedProvider, setSelectedProvider] = useState("");
  const [selectedMethod, setSelectedMethod] = useState("");
  const [idempotencyKey, setIdempotencyKey] = useState<string | null>(null);

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
  const provider = providers.includes(selectedProvider) ? selectedProvider : providers[0] ?? "";
  const paymentMethod = paymentMethods.includes(selectedMethod) ? selectedMethod : paymentMethods[0] ?? "";

  const createOrderMutation = useMutation({
    mutationFn: async (payload: {
      item_code: string;
      currency: string;
      payment_method: string;
      payment_provider: string;
      idempotency_key: string;
    }) => {
      const response = await api.post<APIResponse<WorldOrder>>("/world-commerce/orders", payload);
      if (!response.data.success || !response.data.data) {
        throw new Error("پاسخ ثبت سفارش معتبر نیست.");
      }
      return response.data.data;
    },
  });

  const resetCheckoutChoice = () => {
    setIdempotencyKey(null);
    createOrderMutation.reset();
  };

  const createOrder = () => {
    if (!room || !amount || !provider || !paymentMethod || createOrderMutation.isPending) return;
    const key = idempotencyKey ?? crypto.randomUUID();
    setIdempotencyKey(key);
    createOrderMutation.mutate({
      item_code: room.code,
      currency,
      payment_method: paymentMethod,
      payment_provider: provider,
      idempotency_key: key,
    });
  };

  return (
    <section role="dialog" aria-modal="true" aria-labelledby="world-room-offer-title" className="absolute bottom-4 left-4 right-4 z-30 mx-auto max-w-lg rounded-2xl border border-amber-300/30 bg-slate-950/95 p-5 text-slate-100 shadow-2xl backdrop-blur-xl">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-amber-200">Expansion opportunity</p>
          <h3 id="world-room-offer-title" className="mt-1 text-lg font-semibold">اجاره یا تمدید اتاق شرکت</h3>
        </div>
        <button type="button" onClick={onClose} className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm">بستن</button>
      </div>

      <p className="mt-3 text-sm leading-6 text-slate-300">ثبت سفارش اجاره یک‌ماهه اتاق با ظرفیت یک کارمند و تجهیزات پایه. پس از تأیید و فعال‌سازی سمت سرور، اجاره فعال تمدید می‌شود و اجاره منقضی‌شده از زمان فعال‌سازی دوباره آغاز می‌شود. قیمت و روش‌های پرداخت فقط از کاتالوگ سمت سرور خوانده می‌شوند.</p>

      <div className="mt-4">
        <p className="mb-2 text-sm font-medium">واحد پول</p>
        <div className="grid grid-cols-3 gap-2">
          {CURRENCIES.map((item) => (
            <button key={item.code} type="button" disabled={createOrderMutation.isPending} aria-pressed={currency === item.code}
              onClick={() => { setCurrency(item.code); setSelectedProvider(""); setSelectedMethod(""); resetCheckoutChoice(); }}
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

          {amount && providers.length > 0 && paymentMethods.length > 0 && !createOrderMutation.data && (
            <div className="mt-4 grid gap-3">
              <label className="grid gap-1 text-sm text-slate-300">
                ارائه‌دهنده پرداخت
                <select disabled={createOrderMutation.isPending} value={provider} onChange={(event) => { setSelectedProvider(event.target.value); resetCheckoutChoice(); }}
                  className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100">
                  {providers.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
              </label>
              <label className="grid gap-1 text-sm text-slate-300">
                روش پرداخت
                <select disabled={createOrderMutation.isPending} value={paymentMethod} onChange={(event) => { setSelectedMethod(event.target.value); resetCheckoutChoice(); }}
                  className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100">
                  {paymentMethods.map((item) => <option key={item} value={item}>{PAYMENT_METHOD_LABELS[item] ?? item}</option>)}
                </select>
              </label>
              <p className="text-xs leading-5 text-slate-500">این گزینه‌ها فقط تنظیمات کاتالوگ هستند و به معنی فعال بودن درگاه واقعی نیستند.</p>
            </div>
          )}

          {createOrderMutation.isError && (
            <p role="alert" className="mt-3 text-sm text-red-300">ثبت سفارش انجام نشد. تنظیمات کاتالوگ را بررسی کنید و دوباره تلاش کنید. در صورت خطای شبکه، همان کلید تکرارناپذیری برای جلوگیری از سفارش تکراری حفظ می‌شود.</p>
          )}
          {createOrderMutation.data && (
            <div role="status" className="mt-4 rounded-lg border border-emerald-700/50 bg-emerald-950/30 p-3 text-sm">
              <p className="font-semibold text-emerald-200">سفارش ثبت شد؛ پرداخت انجام نشده است.</p>
              <p className="mt-1 break-all text-xs text-slate-300">شناسه سفارش: {createOrderMutation.data.id}</p>
              <p className="mt-1 text-slate-300">وضعیت: {createOrderMutation.data.status}</p>
              <p className="mt-2 text-xs leading-5 text-slate-400">هیچ مبلغی کسر نشده و اتاقی فعال نشده است. تأیید امن درگاه و فرایند تحویل هنوز پیاده‌سازی نشده‌اند.</p>
            </div>
          )}

          {!createOrderMutation.data && (
            <button type="button" onClick={createOrder}
              disabled={!amount || !provider || !paymentMethod || createOrderMutation.isPending}
              className="mt-4 w-full rounded-lg bg-amber-200 px-4 py-2.5 text-sm font-semibold text-slate-950 disabled:cursor-not-allowed disabled:opacity-50">
              {createOrderMutation.isPending ? "در حال ثبت سفارش…" : "ثبت سفارش (بدون پرداخت)"}
            </button>
          )}
        </div>
      )}

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <span className="text-xs text-slate-500">ثبت سفارش فقط درخواست خرید ایجاد می‌کند؛ پرداخت یا فعال‌سازی انجام نمی‌شود.</span>
        <button type="button" onClick={onClose} className="rounded-lg bg-amber-200 px-4 py-2 text-sm font-semibold text-slate-950">متوجه شدم</button>
      </div>
    </section>
  );
}
