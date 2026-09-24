"use client";

import { TestCenterWorkspace } from "@/components/test-center/test-center-workspace";
import { useI18n } from "@/lib/i18n/provider";

export default function AdminTestCenterPage() {
  const { locale } = useI18n();
  const fa = locale === "fa";
  return <TestCenterWorkspace title={fa ? "مرکز تست پلتفرم" : "Platform Test Center"} description={fa ? "اجرای تست‌های کنترل‌پلین Vendor و تست‌های مهندسی مشترک. تست‌های کسب‌وکار مشتری عمداً خارج از این فضای کاری هستند." : "Run vendor control-plane and shared engineering tests. Customer business tests are intentionally outside this workspace."} />;
}
