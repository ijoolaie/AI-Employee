"use client";

import { useI18n } from "@/lib/i18n/provider";
import { ResellerSurface } from "@/components/reseller/reseller-surface";

export default function ResellerBillingPage() {
  const { locale } = useI18n();
  const fa = locale === "fa";
  return <ResellerSurface title={fa ? "صورتحساب" : "Billing"} description={fa ? "در حال حاضر API واقعی برای صورتحساب تجمیعی نماینده، مدیریت اشتراک نماینده یا صورتحساب مشتریان از طرف نماینده وجود ندارد." : "There is currently no real API for reseller-level aggregated billing, reseller subscription management, or client chargeback."} capabilities={fa ? ["صورتحساب و اشتراک مشتری در فضای همان مشتری باقی می‌ماند","مصرف و هزینه ثبت‌شده در بخش Usage قابل مشاهده است","مدیریت صورتحساب تجمیعی نماینده تا زمان وجود دامنه واقعی فعال نمی‌شود"] : ["Customer billing and subscriptions remain in the customer workspace","Recorded usage and cost are available in Usage & Cost","Reseller-level aggregated billing stays disabled until a real domain exists"]} />;
}
