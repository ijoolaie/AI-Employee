"use client";

import { useI18n } from "@/lib/i18n/provider";
import { ResellerSurface } from "@/components/reseller/reseller-surface";

export default function ResellerIntegrationsPage() {
  const { locale } = useI18n();
  const fa = locale === "fa";

  return (
    <ResellerSurface
      title={fa ? "یکپارچه‌سازی‌ها" : "Integrations"}
      description={
        fa
          ? "مدیریت اتصال‌های سطح نماینده فقط زمانی فعال است که دامنه و مالکیت اعتبارنامه آن در کنترل‌پلین نماینده وجود داشته باشد."
          : "Reseller-level integration management is only enabled where a real reseller-owned domain and credential authority exist."
      }
      capabilities={
        fa
          ? [
              "مرزبندی اعتبارنامه‌های نماینده و مشتری",
              "جلوگیری از نمایش اتصال‌های اختصاصی مشتری در فضای نماینده",
              "اتصال‌های تجاری مشتری در فضای همان مشتری مدیریت می‌شوند",
              "اتصال جدید سطح نماینده تا زمان وجود API و مجوز واقعی فعال نمی‌شود",
            ]
          : [
              "Separate reseller and client credential ownership",
              "Keep client-specific integrations out of the reseller workspace",
              "Customer commerce integrations remain managed inside the customer workspace",
              "New reseller-level integrations stay disabled until a real API and authorization boundary exist",
            ]
      }
    />
  );
}
