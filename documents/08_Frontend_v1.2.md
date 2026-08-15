# AI Employee Platform

## 08 — Frontend Design

**نسخه 1.3** — MVP shipped + i18n requirement locked (fa/en, Phase 2 execution)

> **الزام زبان:** پلتفرم دو زبانه است (فارسی + انگلیسی). جزئیات و معیار پذیرش در `22_I18n_Localization_v1.0`. پیاده‌سازی کامل UI در **Phase 2**؛ این نسخه فقط الزام را قفل می‌کند.

---

### ۱. نمای کلی

Frontend پلتفرم با **Next.js 15 (App Router)**، React 19 و TypeScript پیاده‌سازی می‌شود و از Tailwind CSS برای استایل استفاده می‌کند. سه سطح اصلی رابط کاربری وجود دارد: Customer Panel، Admin Panel و Developer Console.

**وضعیت پیاده‌سازی (v0.1.0 frontend):**
- ✅ Auth (Register / Login / JWT + refresh)
- ✅ Customer Panel MVP: Dashboard، Employees، Runs، Files، Settings
- ⏳ Admin Panel — deferred
- ⏳ Developer Console — deferred
- ⏳ Knowledge / Billing / Usage charts — deferred

---

### ۲. اهداف Frontend

- تجربه کاربری سریع، واضح و قابل اعتماد
- پشتیبانی کامل از جریان Employee → Run → مشاهده نتیجه
- نمایش شفاف وضعیت Run، هزینه و خطاها
- جداسازی منطقی پنل مشتری، ادمین و توسعه‌دهنده
- کد تایپ‌شده، قابل نگهداری و مقیاس‌پذیر
- آمادگی برای SSR/SSG در صفحات عمومی و CSR در پنل‌ها

---

### ۳. Tech Stack Frontend (As-Built)

| فناوری | نقش | نسخه / یادداشت |
|--------|-----|----------------|
| Next.js (App Router) | فریمورک اصلی، Routing، Layout | 15.x |
| React | UI Components | 19.x |
| TypeScript | Type Safety | strict |
| Tailwind CSS | Utility-first Styling | 3.4 |
| Zustand | Auth / session (persist) | 5.x |
| TanStack Query | Server state | 5.x |
| Axios | API client + interceptors | 1.x |
| React Hook Form + Zod | فرم‌ها و اعتبارسنجی | — |
| Lucide React | Icons | — |
| Recharts | نمودارها | *Phase 2* |

---

### ۴. ساختار اپلیکیشن (As-Built)

```
frontend/
├── app/
│   ├── (auth)/              # login, register
│   ├── (customer)/          # Customer Panel
│   │   ├── dashboard/
│   │   ├── employees/       # list, new, [id]
│   │   ├── runs/            # list, [id] (live poll)
│   │   ├── files/
│   │   └── settings/
│   ├── layout.tsx
│   ├── page.tsx             # auth redirect
│   └── globals.css
├── components/
│   ├── ui/                  # Button, Input, Card, Badge, Spinner, EmptyState
│   ├── layout/              # Sidebar, Header
│   └── providers.tsx        # React Query
├── lib/
│   ├── api.ts               # Axios + domain API
│   ├── auth-store.ts        # Zustand persist
│   └── utils.ts
├── types/                   # Aligned with backend Pydantic schemas
├── package.json
├── next.config.ts           # /api/proxy rewrite
└── README.md
```

---

### ۵. پنل‌ها

#### ۵.۱ Customer Panel — **Implemented (MVP)**

| صفحه | وضعیت | توضیح |
|------|--------|--------|
| Dashboard | ✅ | آمار Employees / Runs / Cost / Success rate + recent runs |
| Employees | ✅ | لیست، ایجاد custom، جزئیات + Start Run |
| Runs | ✅ | لیست، جزئیات، polling خودکار برای pending/queued/running |
| Files | ✅ | Upload، list، soft-delete |
| Settings | ✅ | Profile + Tenant info |
| Knowledge | ⏳ | Phase 2+ |
| Usage / Billing | ⏳ | Phase 2 (Cost Dashboard) |

#### ۵.۲ Admin Panel — Deferred

Customers/Tenants، Subscriptions، Costs & Usage سطح پلتفرم، Monitoring.

#### ۵.۳ Developer Console — Deferred

Logs، Trace کامل Run، Workflow status، Token/Cost drill-down.

---

### ۶. Auth Flow (As-Built)

1. **Register** → `POST /api/v1/auth/register` (tenant + user) → tokens
2. **Login** → `POST /api/v1/auth/login` (email + password + tenant_slug) → tokens
3. Tokens در Zustand (persist) ذخیره می‌شوند
4. Axios interceptor: `Authorization: Bearer` + auto-refresh روی 401
5. `GET /auth/me` برای hydrate کردن user + tenant
6. Customer layout: guard بر اساس `isAuthenticated()`

---

### ۷. API Client

- Base URL: `NEXT_PUBLIC_API_URL/api/v1` یا proxy `/api/proxy`
- Envelope: `APIResponse<T>` (`success` + `data`)
- Types در `types/index.ts` دقیقاً با backend schemas هم‌تراز هستند

| UI Action | Endpoint |
|-----------|----------|
| Register / Login / Me | `/auth/*` |
| List / Create / Get Employee | `/employees` |
| List / Create / Get Run | `/runs` |
| List / Upload / Delete File | `/files` |

---

### ۸. State Management

- **Zustand** — auth tokens, user, tenant (localStorage persist)
- **TanStack Query** — employees, runs, files (staleTime 30s, refetch on focus off)
- Run detail: `refetchInterval` وقتی status هنوز active است

---

### ۹. UI Components (MVP)

پیاده‌سازی‌شده:
- Layout: Sidebar، Header
- Status Badge (pending / queued / running / succeeded / failed / …)
- Empty State، Spinner، Card، Button، Input
- Tables برای Runs و Files

بعدی (Phase 2):
- Data Table با pagination/filter
- File Upload drag-and-drop
- Charts (Recharts) برای Report Employee
- Modal / Drawer / Toast

---

### ۱۰. Responsive و Accessibility

- Customer Panel برای desktop-first طراحی شده؛ layout sidebar روی موبایل بعداً به drawer تبدیل می‌شود
- معناشناسی HTML پایه رعایت شده
- RTL کامل در Phase بعدی

---

### ۱۱. محیط و اجرا

```bash
cp .env.example .env.local
npm install
npm run dev   # http://localhost:3000
```

Backend باید روی `http://localhost:8000` (یا مقدار `NEXT_PUBLIC_API_URL`) در حال اجرا باشد. CORS بک‌اند برای `localhost:3000` از قبل باز است.

---

### ۱۲. بین‌المللی‌سازی (الزام برای فاز بعد)

طبق `22_I18n_Localization_v1.0`:
- زبان‌های اجباری: **فارسی (`fa`)** و **انگلیسی (`en`)**
- RTL برای فارسی
- اجرای کامل در **Phase 2** با `next-intl` (پیشنهادی)
- Phase 1 MVP می‌تواند UI انگلیسی داشته باشد؛ هیچ تصمیم محصولی نباید بعداً تک‌زبانه بودن را توجیه کند.

### ۱۳. خارج از محدوده MVP فعلی

- Design System کامل / UI kit اختصاصی
- PWA و آفلاین
- i18n کامل fa/en + RTL (الزام مصوب — اجرای Phase 2 طبق سند 22)
- Employee Builder بصری
- Admin و Developer panels

---

### ۱۴. همسویی با سایر مستندات

این سند با Backend v0.2.0، API Design، Architecture و Product Vision همسو است. جزئیات بصری بیشتر در `09_UI_UX` پوشش داده می‌شود.

---

### Revision History

| نسخه | تاریخ | تغییرات |
|------|--------|---------|
| 1.0 | — | طراحی اولیه |
| 1.1 | 2026-08-05 | تأیید ترتیب: Backend-first |
| **1.2** | **2026-08-06** | As-built: Customer Panel MVP (v0.1.0) |
| **1.3** | **2026-08-06** | الزام دوزبانه fa/en + RTL ثبت شد (سند 22). Harden اولیه Auth/خطا در کلاینت. |

— پایان Frontend Design v1.2 —

> **Current-state synchronization (v0.2.9-LMSTUDIO, 2026-08-07):** This document remains authoritative for its planned/design scope. Current implementation status is tracked in `00_AS_BUILT_BASELINE_v0.2.9_LMSTUDIO.md` and `23_AS_BUILT_CURRENT_STATE_v0.2.9.md`. LM Studio is the default local provider; Windows Celery uses `--pool=solo`; the real `.env` is excluded from release packages.

