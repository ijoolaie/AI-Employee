"use client";

import { useI18n } from "@/lib/i18n/provider";
import { ResellerSurface } from "@/components/reseller/reseller-surface";

export default function ResellerSecurityPage() {
  const { locale } = useI18n();
  const fa = locale === "fa";
  return <ResellerSurface title={fa ? "امنیت" : "Security"} description={fa ? "مرز امنیتی فضای نماینده با کنترل‌های واقعی احراز هویت و نقش‌های تیمی تعریف می‌شود؛ کنترل‌های جدید بدون API و مجوز واقعی فعال نمی‌شوند." : "The reseller security boundary uses the real authentication and team-role controls; new controls stay disabled until backed by real APIs and authorization."} capabilities={fa ? ["مدیریت وضعیت و نقش کاربران تیم در بخش Team","مرزبندی دسترسی نماینده با tenant مشتری","کنترل امنیتی جدید فقط پس از پیاده‌سازی دامنه و مجوز واقعی فعال می‌شود"] : ["Team user status and role management in Team","Reseller-to-client access boundary","New security controls stay disabled until backed by real domain APIs and authorization"]} />;
}
