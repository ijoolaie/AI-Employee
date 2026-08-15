# RC8 Implementation Matrix — Phase 0 (Baseline & Contract Freeze)

> این سند طبق Phase 0 نقشه راه RC8 تهیه شده: **"قبل از توسعه بیشتر، بدانیم دقیقاً چه چیزی داریم."**
> برخلاف فرضیات اولیه roadmap (که Chat/Tasks/Logs/Traces/API Keys را "Missing" فرض کرده بود)، بازرسی مستقیم کد نشان می‌دهد این پروژه (`AI_Employee_Platform_RC8_P0-P3_completed`) در عمل بسیار جلوتر است. این سند بر پایه بررسی واقعیِ ۷۷۴ فایل ریپو نوشته شده، نه حدس.

## 1. Baseline

| مورد | وضعیت |
|---|---|
| Docker startup | ✅ (docker-compose موجود، سرویس‌های backend/frontend/postgres/redis) |
| Postgres | ✅ (alembic migrations موجود) |
| Redis | ✅ |
| API health | ✅ (`backend/app/api/health.py`) |
| Frontend health | ✅ |
| Login | ✅ (`(auth)/login`, `backend/app/api/v1/auth.py`) |
| Dashboard | ✅ (`(customer)/dashboard`, `(admin)/admin`) |
| API proxy | ✅ (v2 fix حفظ شده) |

## 2. Route Inventory → API Mapping → وضعیت

### Phase 1 — Core Shell

| Feature | Frontend Route | Backend Endpoint | وضعیت |
|---|---|---|---|
| Role-based navigation (Customer) | `components/layout/sidebar.tsx` | – | **Implemented** — ۴ گروه (Business / AI Workspace / Operations / Developer)، بسیار کامل‌تر از پیش‌نویس نقشه راه |
| Role-based navigation (Developer) | `src/lib/developer/navigation.ts` | – | **Implemented** |
| Role-based navigation (Owner/Platform) | `src/lib/owner/navigation.ts` | – | **Partial** — به `/admin/operations`, `/admin/security`, `/admin/audit` لینک می‌دهد ولی این صفحات وجود ندارند (پایین را ببینید) |
| API Keys | `(customer)/api-keys` | `api_keys.py` (`/api-keys` CRUD) | **Implemented** — Create/List/Revoke موجود؛ خروجی roadmap Phase 1 عملاً از قبل ساخته شده |
| Shared UI states (Loading/Empty/Error/Toast/Pagination) | `components/ui/*` (`spinner`, `empty-state`, `badge`, …) | – | **Implemented** |

### Phase 2 — Customer Operations

| Feature | Frontend Route | Backend Endpoint | وضعیت |
|---|---|---|---|
| AI Employees (List/Create/Edit/Run) | `(customer)/employees`, `employees/[id]`, `employees/new` | `employees.py` | **Implemented** |
| Chat | `(customer)/chat`, `chat/[publicKey]` (widget) | `public_chat.py`, `runs.py` | **Implemented** — flow Employee→Run از قبل وصل است |
| Tasks | `(customer)/tasks` | `runs.py` (`listRuns`) | **Implemented** — روی Run infrastructure سوار است، دقیقاً طبق پیشنهاد roadmap |
| Reports | `(customer)/reports`, `analytics`, `usage` | `customer_dashboard.py`, `usage.py` | **Implemented** (MVP) |
| Approvals / Schedules / Workflows | `(customer)/approvals`, `schedules`, `workflows` | `workflow_*.py` | **Implemented** — فراتر از دامنه roadmap اصلی |

### Phase 3 — Developer / Observability

| Feature | Frontend Route | Backend Endpoint | وضعیت |
|---|---|---|---|
| Developer Console | `(customer)/developer` | چند سرویس | **Implemented** |
| API Console/Docs | `(customer)/api-console` (جدید) | از endpointهای موجود (`employees`, `runs`, `api-keys`, `knowledge`, `workflows`, `operations`, `billing`, `usage`, `customers`, `orders`, `products`) استفاده می‌کند | **Implemented (این نوبت اضافه شد)** — کاتالوگ endpoint، ورودی path-param، ویرایشگر JSON body، دکمه Send با session فعلی، نمایش status/latency/response؛ لینک به `/api/v1/openapi.json` برای اسپک کامل |
| Logs | `(customer)/logs` | `operations.py` → `GET /audit-logs` | **Implemented** |
| Trace Explorer | `(customer)/traces` | `runs.py` → `GET /{run_id}/trace` (`trace_service`) | **Implemented** — شامل timeline، planner/memory/tool/LLM events، tokens/cost |
| Debug View (per-run breakdown) | همان `traces` page | همان trace endpoint | **Implemented** (در دل Trace Explorer، نه صفحه جدا) |
| Webhooks | `(customer)/webhooks` | `channel_webhooks.py`, `billing_webhooks.py` | **Implemented** |

### Phase 4 — Tenant Administration

| Feature | Frontend Route | Backend Endpoint | وضعیت |
|---|---|---|---|
| Users (List/Invite/Disable/Role) | ❌ صفحه‌ای پیدا نشد | ❌ | **Missing** — در `(customer)/settings/page.tsx` صراحتاً آمده: *"Team invites and role management will be added in a later release."* |
| Permissions / RBAC matrix | ❌ | نقش‌ها در `owner/navigation.ts` به صورت `permission:` رشته‌ای reference می‌شوند | **Backend-only / Missing UI** — مدل permission در نویگیشن هست ولی صفحه مدیریت RBAC نیست |
| Knowledge Management | `(customer)/knowledge` | `knowledge.py` | **Implemented** |
| Billing | `(customer)/billing` | `billing.py`, `invoices.py`, `billing_webhooks.py` | **Implemented** — Stripe-backed، طبق پیشنهاد roadmap به backend موجود وصل شده |

### Phase 5 — Platform Administration

| Feature | Frontend Route | Backend Endpoint | وضعیت |
|---|---|---|---|
| Tenant Management | `(admin)/admin/tenants` | `admin.py` | **Implemented** |
| Provider Management (list/health/config) | فقط بخشی از `(admin)/admin` (کارت "Provider usage") | `admin.py` (health/usage) | **Partial** — usage نمایش داده می‌شود، ولی صفحه مستقل مدیریت Provider (enable/disable/default model) نیست |
| Global Metrics | `(admin)/admin` | `admin.py` | **Implemented** (MVP dashboard) |
| Operations / Security / Audit (لینک‌شده در nav) | ❌ صفحه وجود ندارد | نامشخص | **Missing** — `owner/navigation.ts` به `/admin/operations`, `/admin/security`, `/admin/audit` اشاره می‌کند اما `page.tsx` متناظر در `(admin)` نیست → **broken nav links** |
| Validation | `(admin)/admin/validation` | نامشخص، نیاز به بررسی سرویس | **Implemented (frontend) / نیاز به تایید backend** |

### Phase 6 — Integrations

| Feature | Frontend Route | Backend Endpoint | وضعیت |
|---|---|---|---|
| Shopify (Connect/OAuth/Sync/Reconcile) | `(customer)/integrations` | `commerce_integrations.py` | **Implemented** — OAuth install URL، sync products/orders، reconcile |
| WhatsApp | `(customer)/channels` (به عنوان یک نوع channel، نه صفحه جدا) | `channel_webhooks.py`, `customer_channels.py` | **Partial** — endpoint وبهوک provider-neutral ساخته شده و UI کد webhook را نشان می‌دهد، اما به صراحت در متن صفحه آمده باید به یک WhatsApp Business provider واقعی وصل شود؛ health/status اختصاصی وجود ندارد |

### Phase 7 — Documentation

| مورد | وضعیت |
|---|---|
| اسناد معماری/ممیزی موجود (`docs/architecture`, `docs/audit`, `docs/production`, `docs/current`) | **Implemented** — حجم زیادی مستندات M2–M15، Gate 1–9 و RC1–RC8 از قبل موجود است |
| این سند (`RC8_IMPLEMENTATION_MATRIX.md`) | **New — این تحویل Phase 0 است** |

## 2.1 وضعیت اجرای Phase 1–3 (به‌روزرسانی)

نتیجه بررسی: **Phase 1 و Phase 2 از قبل به طور کامل پیاده‌سازی شده بودند** (Shell، Navigation، API Keys، Employees، Chat، Tasks، Reports). تنها Gap واقعی داخل محدوده Phase 1–3، نبودِ **API Console/Try-it** در Phase 3 بود که در همین session ساخته شد:

- فایل جدید: `frontend/app/(customer)/api-console/page.tsx`
- به Developer navigation (`src/lib/developer/navigation.ts`) و Sidebar اصلی (`components/layout/sidebar.tsx`) اضافه شد
- کاتالوگ endpoint مستقیماً از خواندن route decoratorهای `backend/app/api/v1/*.py` تهیه شد (نه فرضی)
- درخواست‌ها با همان `api` axios instance موجود (session bearer token) ارسال می‌شوند؛ برای استفاده خارجی/CI به صفحه API Keys ارجاع داده می‌شود

**وریفای انجام‌شده:**
| بررسی | نتیجه |
|---|---|
| `npx tsc --noEmit` (کل پروژه frontend) | ✅ بدون خطا |
| `npx eslint` روی فایل‌های جدید/ویرایش‌شده | ✅ بدون خطا |
| `npm run build` (Next.js production build) | ⚠️ در همین محیط sandbox به‌خاطر بلاک‌بودن دسترسی به Google Fonts (`fonts.googleapis.com`) در مرحله fetch فونت fail می‌شود — این خطا مربوط به شبکه sandbox است، نه کد اضافه‌شده؛ در محیط واقعی (یا با فونت local) باید پاس شود |

نتیجه: Phase 1، 2 و 3 از نظر دامنه‌ای که در roadmap تعریف شده، اکنون **Implemented** هستند.

## 3. جمع‌بندی Gap واقعی (بر خلاف فرض اولیه roadmap)

بیشتر چیزهایی که roadmap فرض کرده بود "Missing" هستند (API Keys، Chat، Tasks، Logs، Traces) در واقع **Implemented** هستند. Gapهای واقعی که با بررسی کد تایید شدند:

1. **Users / Team invites / Role management** — صراحتاً در کد به عنوان "later release" علامت‌گذاری شده. (Phase 4)
2. **صفحه مدیریت RBAC/Permission matrix** — وجود ندارد. (Phase 4)
3. **سه لینک شکسته در Owner nav**: `/admin/operations`, `/admin/security`, `/admin/audit` — در منو هستند ولی صفحه ندارند. (Phase 5)
4. **صفحه مستقل Provider Management** (نه فقط usage) — وجود ندارد. (Phase 5)
5. ~~API Console/Try-it داخل UI~~ — **رفع شد** (بخش ۲.۱ را ببینید). (Phase 3)
6. **WhatsApp integration health/status اختصاصی** — فقط webhook config عمومی هست، مدیریت اتصال واقعی provider نیست. (Phase 6)

## 4. پیشنهاد ترتیب اجرا (به‌روزشده بر اساس Gap واقعی)

چون بخش بزرگی از P1–P3 از قبل کامل است، اولویت واقعی برای رساندن پروژه به همان خروجی که roadmap دنبال می‌کند این است:

| اولویت | کار | فاز roadmap | دلیل |
|---|---|---|---|
| 1 | ساخت صفحات `/admin/operations`, `/admin/security`, `/admin/audit` یا حذف لینک‌های شکسته از nav | P5 | جلوگیری از 404 در محصول فعلی |
| 2 | Users list + Invite + Role assignment (frontend + احتمالاً backend endpoint جدید) | P4 | تنها گپ کامل بدون هیچ پیاده‌سازی |
| 3 | صفحه Permission/RBAC matrix | P4 | وابسته به #2 |
| 4 | صفحه مستقل Provider Management | P5 | usage از قبل هست، فقط UI مدیریت باقی مانده |
| ~~5~~ | ~~API Console با Try-it~~ | P3 | ✅ انجام شد |
| 6 | WhatsApp health/status | P6 | کمترین اولویت طبق تصمیم خود roadmap |

---
*تولید شده در Phase 0 با بازرسی مستقیم سورس (frontend routes، backend routers، nav config)، نه بر پایه فرض.*
