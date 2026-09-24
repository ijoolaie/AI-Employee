"use client";

import { useI18n } from "@/lib/i18n/provider";
import { ResellerSurface } from "@/components/reseller/reseller-surface";

export default function ResellerReportsPage() {
  const { locale } = useI18n();
  const fa = locale === "fa";
  return <ResellerSurface title={fa ? "گزارش‌ها" : "Reports"} description={fa ? "در حال حاضر دامنه گزارش‌گیری تجمیعی اختصاصی نماینده برای سلامت سبد مشتری، SLA، درآمد یا عملکرد نیروی کار وجود ندارد." : "There is currently no dedicated reseller reporting domain for client-portfolio health, SLA, revenue, or workforce aggregation."} capabilities={fa ? ["گزارش‌های اختصاصی هر مشتری در فضای همان مشتری باقی می‌ماند","مصرف نماینده در بخش Usage قابل مشاهده است","گزارش‌گیری تجمیعی نماینده تا زمان وجود API واقعی فعال نمی‌شود"] : ["Customer-specific reporting remains inside the customer workspace","Reseller-tenant usage is available in Usage & Cost","Reseller-level aggregation stays disabled until a real reporting API exists"]} />;
}
