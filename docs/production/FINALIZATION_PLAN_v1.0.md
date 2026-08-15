# AI Employee Platform — Finalization Plan v1.0

## هدف

این سند پروژه را از وضعیت RC8/feature-heavy به یک Release Candidate قابل‌اعتماد و سپس v1.0 هدایت می‌کند. اصل حاکم این است که «Implemented» با «Verified» یکی نیست؛ هر قابلیت فقط وقتی Done است که acceptance criteria، تست، integration، documentation و evidence انتشار را داشته باشد.

## وضعیت فعلی

- Core backend/frontend: گسترده و عمدتاً implemented
- Documentation: چند نسل و نیازمند یک source of truth
- Tenant administration: users/status/roles UI implemented; invitation workflow remains a post-v1.0 enhancement unless provider mail is configured
- Platform administration: read-only provider readiness surface implemented; credential mutation remains secret-manager controlled
- Invoice UI: list/detail/status/PDF surface implemented
- WhatsApp: inbound/provider-neutral foundation؛ outbound provider certification باقی است
- Stripe/Shopify: implementation موجود، certification تولیدی باقی است
- i18n/RTL: locale foundation, English/Persian switch and document direction implemented; full string translation coverage is post-v1.0
- Full E2E / production certification: هنوز gate نهایی نیست

## فازها و خروجی‌های اجباری

### Phase 0 — Freeze & Baseline

- baseline نسخه، migration، API و dependency
- known gaps و blockers
- ثبت محیط و evidence بدون ادعای PASS برای موارد اجرا نشده

### Phase 1 — Contract Alignment

- `PRODUCT_COMPLETION_MATRIX_v1.0.md` به‌عنوان Source of Truth
- mapping requirement → backend → API → frontend → evidence
- حذف ادعاهای تاریخی متناقض از مسیر release

### Phase 2 — Product Completion

- Tenant Team & Roles UI + tenant-scoped administration API
- Invoice list/detail/status/PDF UI
- Sales Deal Detail UI
- Platform Operations/Audit surfaces
- Knowledge/Memory UX hardening و تکمیل acceptance criteria
- i18n/RTL foundation و translation backlog
- Provider management gap documented until a safe management API exists

### Phase 3 — Reliability Hardening

- webhook failure is no longer silently swallowed
- Shopify webhook duplicate delivery is explicitly detected
- idempotency/retry/timeout/DLQ review
- transactional outbox review
- tenant isolation and RBAC enforcement
- background job recovery and rate-limit review

### Phase 4 — External Integrations

- Stripe: checkout → webhook → subscription → entitlement → cancellation
- Shopify: OAuth → credential storage → sync → webhook → idempotency → reconciliation → disconnect/reconnect
- WhatsApp: inbound → provider adapter → employee/run → outbound provider → delivery status → retry → handoff

### Phase 5 — Production Readiness

- production Docker stack
- PostgreSQL/Redis/Celery
- TLS, monitoring, logging, alerts
- backup/restore scripts and procedure (`ops/production/backup.sh`, `restore.sh`)
- rollback and incident runbooks (`ops/production/release-runbook.md`)
- support documentation

### Phase 6 — Release Documentation

- final completeness matrix
- known issues
- release notes
- migration/runbook documentation
- explicit PASS / BLOCKED / NOT EXECUTED evidence ledger

### Phase 7 — Final Verification (LAST)

**تست و certification عمداً آخرین فاز است.** هیچ تستی به‌عنوان gate نهایی قبل از تکمیل فازهای 0 تا 6 ملاک release نیست؛ در پایان تمام موارد بالا یک verification sweep واحد اجرا می‌شود:

- backend unit/integration
- frontend build/lint/unit/contract
- API contract
- browser E2E
- Docker E2E
- Stripe / Shopify / WhatsApp certification
- human handoff
- GDPR export/delete
- backup/restore
- security regression

Gate نهایی: فقط evidence واقعی `PASS` اجازه تبدیل RC به v1.0 را دارد.

## Definition of Done

هر قابلیت فقط با تمام موارد زیر Done است:

1. implementation کامل
2. backend/API/frontend alignment
3. failure-path و reliability handling
4. documentation و runbook
5. acceptance criteria مشخص
6. در Phase 7 واقعاً verify و certify شده
