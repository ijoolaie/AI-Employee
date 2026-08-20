# AI Employee Platform — Finalization Plan v1.0

## هدف

این سند پروژه را از وضعیت RC8/feature-heavy به یک Release Candidate قابل‌اعتماد و سپس v1.0 هدایت می‌کند. اصل حاکم این است که «Implemented» با «Verified» یکی نیست؛ هر قابلیت فقط وقتی Done است که acceptance criteria، تست، integration، documentation و evidence انتشار را داشته باشد.

## وضعیت فعلی — 2026-08-20

**Current checkpoint: Local Production Readiness verified; release certification هنوز NO-GO است.**

Evidence ثبت‌شده روی branch `agent/product-acceptance-files-km-current`:

- local production Compose config: PASS
- production API image + worker + beat: built successfully
- PostgreSQL: healthy
- Redis: healthy
- API: healthy + `/health/dependencies`: PASS
- Frontend: healthy
- Worker: healthy
- Beat: running
- controlled API failure detection: PASS
- API recovery drill: PASS
- known-good revision: `27dc0aa5651b60afe171cada831185d28b73f58c`
- working tree after drill: clean

Important distinction: this is **local-production evidence**. It does not satisfy the separate staging/CI, TLS, real-provider, backup/restore-target, or final Phase 7 certification gates.

### Remaining release blockers

**P0 — before Phase 7**

- network-enabled CI/staging environment
- locked backend/frontend dependency installation in CI/staging
- real staging PostgreSQL/Redis/Celery configuration
- real provider credentials in secret manager
- HTTPS/TLS configuration
- migration + rollback rehearsal in staging
- backup storage + verified restore target

**P1 — final environment configuration**

- Stripe certification configuration
- Shopify OAuth/webhook configuration
- WhatsApp outbound provider configuration and certification
- production monitoring/alerting
- support/incident ownership

**Phase 7 — final verification**

- backend unit/integration
- frontend build/lint/unit/contract
- API contract
- browser E2E
- Docker E2E
- Stripe / Shopify / WhatsApp certification
- human handoff
- GDPR export/delete
- backup/restore verification
- security regression

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
- local-production deployment and controlled recovery drill verified on 2026-08-20
- staging/real-environment execution remains required

### Phase 6 — Release Documentation

- final completeness matrix
- known issues
- release notes
- migration/runbook documentation
- explicit PASS / BLOCKED / NOT EXECUTED evidence ledger
- current evidence must distinguish local-production verification from staging/production certification

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
