# Client Handoff & Test Evidence — Current RC

**Status date:** 2026-08-22  
**Repository:** `ijoolaie/AI-Employee`  
**Purpose:** current handoff, certification evidence, post-release productization evidence and remaining deployment gates.

> Historical RC8 archive details remain useful as history, but they are superseded as the primary certification checkpoint by the fresh CI evidence below. Post-release productization work is tracked separately and does not retroactively modify the published release baseline.

## 1. Current certification checkpoint

The authoritative repository-level certification evidence remains the previously completed GitHub Actions Production Certification checkpoint documented in `docs/current/05_CERTIFICATION_PROGRESS.md`.

The 2026-08-22 productization work is **post-release verification**, not a request to reopen RC8/RC9 certification unless a later change affects a certified behavior.

## 2. Fresh runtime/product evidence

The current documented test session includes:

- backend full suite: **194 passed, 1 warning**;
- focused workflow foundation/approval/trigger tests: **7 passed, 1 warning**;
- execution hardening/workflow-versioning tests: **8 passed**;
- production-like Docker stack observed healthy;
- API healthy;
- frontend healthy;
- PostgreSQL healthy;
- Redis healthy;
- Worker running;
- Beat running;
- recurring Outbox and workflow scheduler/timeout/approval-expiry tasks completing successfully.

The only full-suite warning is the Python `crypt` deprecation emitted through Passlib; it is not a test failure.

## 3. Post-release productization / account-security evidence

Detailed evidence is recorded in `docs/current/08_POST_RELEASE_PRODUCTIZATION_TEST_EVIDENCE_2026-08-22.md`.

### Account security

- Authenticated password-change API/service is implemented.
- Settings exposes **Security / Password**.
- `/settings/security` provides the password-change UX.
- Password length is validated between 8 and 128 characters.
- Confirmation mismatch is rejected client-side before submission.
- Successful password changes require the user to sign in again.
- Password reset was manually verified successfully by the project owner.

### Tenant lifecycle

- Vendor can suspend/resume/deprovision direct reseller tenants.
- Reseller can suspend/resume/deprovision direct customer tenants.
- Direct-parent and edition-kind checks remain enforced.
- Invalid lifecycle transitions are rejected.
- Deprovisioning is blocked while child tenants remain active.
- Deprovisioning disables tenant users and retains tenant data; it does not perform destructive deletion.
- Lifecycle transitions are recorded through the existing audit path.
- Automated lifecycle transition and child-dependency guard tests were added.

## 4. CI / PR sequence

Relevant post-release productization PRs:

- **PR #29** — expose Security / Password in Settings and correct the unrelated guardrail-test fixture regression.
- **PR #30** — polish the Security / Password UX while preserving the authenticated backend contract.
- **PR #31** — add bounded Vendor → Reseller → Customer tenant lifecycle controls and lifecycle tests.

The current `main` lineage contains all three changes.

## 5. CI architecture

The certification workflow intentionally uses one Compose-managed runtime stack for PostgreSQL, Redis and application services. GitHub service containers are not duplicated alongside Compose, avoiding host-port conflicts.

Dependency setup is cached and performed once per certification job. Playwright installs Chromium without `--with-deps`, avoiding long-running host `apt` installation. OCR is validated in the API container where the production-like image provides Tesseract and Farsi language data.

## 6. Product workspace coverage

The current product surfaces are documented separately as:

- Platform Admin: `/admin`
- Business Dashboard: `/dashboard`
- AI Workspace: `/workspace`
- AI Employees: `/employees`
- Customer Channels: `/channels`
- Conversations: `/conversations`
- Public Customer Experience: `/chat/[publicKey]`
- Website widget loader: `/widget.js?channel=<publicKey>`
- Customer Settings → Security / Password: `/settings/security`

The public customer experience is not a tenant dashboard and must remain isolated from SaaS administration.

## 7. Deployment-specific gates — NOT YET CERTIFIED

Passing repository-level certification or post-release productization tests does **not** certify a real production deployment. The following remain open:

| Gate | Status |
|---|---|
| HTTPS / reverse proxy / trusted origins | NOT VERIFIED |
| Production secrets/configuration | NOT VERIFIED |
| Production PostgreSQL/Redis/Celery endpoints | NOT VERIFIED |
| Worker/Beat restart and queue health | NOT VERIFIED |
| Monitoring / centralized logging / OTel / alerting | NOT VERIFIED |
| Persistent storage | NOT VERIFIED |
| Backup / restore / recovery | NOT VERIFIED |
| SMTP/email | NOT VERIFIED |
| Object storage | NOT VERIFIED |
| Live payment/webhook provider | NOT VERIFIED |
| Production security certification | NOT CLAIMED |
| Production deployment / rollback rehearsal | NOT VERIFIED |

## 8. Production deployment checklist

Before a production release:

1. Supply real secrets through the deployment secret manager; never package repository defaults as production secrets.
2. Configure HTTPS and trusted origins/reverse proxy.
3. Configure and verify PostgreSQL, Redis and Celery endpoints with appropriate network restrictions.
4. Start API, worker and Beat as applicable; verify restart policy and queue health.
5. Configure telemetry, centralized logs and alerting.
6. Verify persistent storage and perform backup/restore/recovery rehearsal.
7. Configure external providers only where enabled and verify webhook/signature handling.
8. Run clean migration, deployment and rollback rehearsal.
9. Run the final certification against the deployment candidate.

## 9. Release classification

**CLIENT HANDOFF:** YES  
**DEPLOYMENT CANDIDATE:** YES  
**REPOSITORY-LEVEL CERTIFICATION:** YES  
**POST-RELEASE PRODUCTIZATION VERIFICATION:** YES  
**PRODUCTION CERTIFIED:** NO

Production certification must be granted only after the deployment-specific gates above pass with fresh evidence.
