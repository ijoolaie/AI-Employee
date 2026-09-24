"use client";

import { useI18n } from "@/lib/i18n/provider";
import { ResellerSurface } from "@/components/reseller/reseller-surface";

export default function ResellerSettingsPage() {
  const { locale } = useI18n();
  const fa = locale === "fa";
  return <ResellerSurface title={fa ? "تنظیمات نماینده" : "Reseller Settings"} description={fa ? "این سطح فقط مرز تنظیمات نماینده را مشخص می‌کند؛ API واقعی برای تغییر پروفایل، برندینگ یا سیاست‌های onboarding در این صفحه هنوز وجود ندارد." : "This surface defines the reseller settings boundary; no real API currently exists here for profile, branding, or onboarding-policy mutations."} capabilities={fa ? ["مرز تنظیمات نماینده و مشتری","جلوگیری از تغییر مستقیم تنظیمات tenant مشتری","تنظیمات عملیاتی جدید فقط پس از ایجاد API و مجوز واقعی فعال می‌شوند"] : ["Reseller-versus-client settings boundary","No direct mutation of client-tenant settings","New operational settings stay disabled until real APIs and authorization exist"]} />;
}
