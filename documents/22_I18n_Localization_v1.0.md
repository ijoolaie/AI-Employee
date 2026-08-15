# AI Employee Platform

## 22 — Internationalization & Localization (i18n / l10n)

**نسخه 1.0** — 2026-08-06  
**وضعیت:** الزام مصوب برای ساخت — **پیاده‌سازی کامل در Phase 2** (پس از تثبیت Customer Panel MVP)

---

### ۱. تصمیم الزام‌آور

پلتفرم **از روز طراحی دو زبانه** است:

| زبان | کد | اولویت |
|------|-----|--------|
| **فارسی** | `fa` | زبان اصلی بازار هدف (ایران / کاربران فارسی‌زبان) |
| **انگلیسی** | `en` | زبان دوم؛ API docs، Developer Console، مشتریان بین‌المللی |

- رابط کاربری Customer Panel، Admin Panel و صفحات عمومی باید هر دو زبان را پشتیبانی کنند.
- Backend پیام‌های خطای user-facing در Phase 2 می‌توانند کدخطا + ترجمه UI داشته باشند؛ تا آن زمان کد/پیام انگلیسی API قابل‌قبول است و UI ترجمه می‌کند.
- **RTL** برای فارسی اجباری است (`dir="rtl"` روی ریشه وقتی زبان `fa` است).

این سند بخشی از **اسناد ساخت** است و در فازهای بعدی بدون نیاز به تصمیم‌گیری مجدد اجرا می‌شود.

---

### ۲. محدوده Phase 2 (اجرا)

1. انتخاب کتابخانه i18n (پیشنهاد: `next-intl` با App Router)
2. فایل‌های پیام: `messages/fa.json`، `messages/en.json`
3. سوییچر زبان در Header / Settings (persist در localStorage + ترجیحاً پروفایل کاربر)
4. RTL کامل برای `fa` (layout، sidebar، جداول، فرم‌ها)
5. تاریخ و عدد: نمایش Localized (مثلاً `Intl` یا dayjs با locale)
6. تمام رشته‌های UI پنل مشتری (و بعداً Admin) بدون hard-code انگلیسی

**خارج از Phase 2 (بعدی):**
- ترجمه محتوای تولیدشده توسط AI Employee (خروجی مدل) — اختیاری per-Employee
- چندزبانگی بیش از fa/en

---

### ۳. اصول

- هیچ متن UI نهایی نباید فقط به صورت hard-coded انگلیسی در کامپوننت بماند (پس از اتمام Phase 2 i18n).
- کلیدهای ترجمه معنادار باشند: `auth.login.title` نه `text1`.
- هم‌ترازی با `08_Frontend` و `09_UI_UX`.
- SEO صفحات عمومی: `lang` و در صورت نیاز مسیر `/fa/...` یا `/en/...` (تصمیم نهایی در پیاده‌سازی Phase 2).

---

### ۴. وابستگی به اسناد دیگر

| سند | ارتباط |
|-----|--------|
| 08_Frontend | Tech stack + ساختار app؛ i18n به stack اضافه می‌شود |
| 09_UI_UX | RTL، تایپوگرافی فارسی، سوییچر زبان |
| 03_Roadmap | قرارگیری در Phase 2 |
| 01_Product Vision | بازار فارسی‌زبان به‌عنوان persona اولیه |

---

### ۵. معیار پذیرش (Phase 2)

- [ ] کل Customer Panel با سوییچ fa/en بدون متن باقی‌مانده hard-coded ضروری
- [ ] RTL صحیح در فارسی (بدون شکستگی layout)
- [ ] انتخاب زبان پس از refresh حفظ می‌شود
- [ ] Login / Register / خطاهای رایج به هر دو زبان

---

*پایان سند 22 — I18n v1.0*

> **Current-state synchronization (v0.2.9-LMSTUDIO, 2026-08-07):** This document remains authoritative for its planned/design scope. Current implementation status is tracked in `00_AS_BUILT_BASELINE_v0.2.9_LMSTUDIO.md` and `23_AS_BUILT_CURRENT_STATE_v0.2.9.md`. LM Studio is the default local provider; Windows Celery uses `--pool=solo`; the real `.env` is excluded from release packages.

