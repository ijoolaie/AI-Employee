"use client";

import { TestCenterWorkspace } from "@/components/test-center/test-center-workspace";
import { useI18n } from "@/lib/i18n/provider";

export default function ResellerTestCenterPage() {
  const { locale } = useI18n();
  return <TestCenterWorkspace title={locale === "fa" ? "مرکز تست نماینده" : "Reseller Test Center"} description={locale === "fa" ? "اجرای تست‌های واقعی مربوط به تحویل سرویس نماینده، فرزند مستقیم مجاز و تست‌های مهندسی مشترک." : "Run real reseller service-delivery, authorized direct-child, and shared engineering tests."} />;
}
