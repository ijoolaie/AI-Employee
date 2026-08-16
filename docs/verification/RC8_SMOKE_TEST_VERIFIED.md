# RC8 Smoke Test Verification

## Status: PASSED

**Verified:** 2026-08-16  
**Release:** AI Employee Platform RC8 Fix8 V1

این Smoke Test به‌صورت کامل اجرا و تأیید شده است. برای تست‌های روتین بعدی، اجرای مجدد این سناریو لازم نیست مگر اینکه کد، Worker، AI provider، queue، run execution یا زیرساخت مرتبط تغییر کرده باشد.

### سناریوی تأییدشده

1. API و سرویس‌های وابسته بررسی شدند:
   - `/health/dependencies` → `200 OK`
   - PostgreSQL → `ok`
   - Redis → `ok`
2. ثبت‌نام و احراز هویت موفق بود.
3. Onboarding:
   - `POST /api/v1/onboarding/progress` → `200 OK`
   - `GET /api/v1/onboarding` → `200 OK`
4. ساخت Employee:
   - Employee با slug `smoke-test-employee` ساخته شد.
5. انتشار Employee Version:
   - Version `2` با موفقیت منتشر شد و `is_current=true` بود.
6. ساخت Run:
   - Run با موفقیت ایجاد شد و ابتدا در وضعیت `pending` قرار گرفت.
7. Worker:
   - Celery Worker با موفقیت بالا آمد و task `run.execute` را دریافت کرد.
8. اجرای AI:
   - Run در نهایت به `success` رسید.
   - خروجی: `Acknowledged. Proceeding with checks.`
   - Total tokens: `100`
   - Cost: `$0.00`
9. Trace:
   - Trace با `200 OK` برگشت.
   - رویدادهای `run.created`، `ai.provider_call` و `run.completed` با وضعیت `success` ثبت شدند.
   - Provider: `lm_studio`
   - Model: `google/gemma-4-e4b`
   - `tool_count=0`
   - `rag_enabled=false`

### نتیجه

**RC8 end-to-end smoke test: PASS**

Run ID مرجع:
`28a0e2ae-581b-4cda-bbaf-7efa761d0dd4`

این Run به‌عنوان **Baseline Smoke Test موفق** ثبت می‌شود و نباید صرفاً برای تأیید دوباره همین مسیر، در هر اجرای تست تکرار شود.

> توجه: این ثبت وضعیت به معنی صرف‌نظر از تست‌های regression یا تست‌های مربوط به تغییرات جدید نیست.
