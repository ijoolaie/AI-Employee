# W20 — Third-party Employee Marketplace

## Status

**First governed vertical slice implemented; REAL-STACK VERIFIED.**

W20 is distinct from W16 Skill Marketplace. W16 owns SkillPackage publication, skill installation, purchase entitlement and marketplace financial allocation. W20 packages a governed Employee/AgentTemplate composition and imports it into a buyer tenant without granting execution authority.

## Contract

`Package → Version → Permission → Tenant Boundary → Installation → Provider Execution → Revocation → Audit → Financial Truth`

### Implemented in this slice

- `EmployeeMarketplacePackage` is seller-tenant scoped and versioned by `owner_tenant_id + slug + version`.
- A package may only be published from a seller-owned `AgentTemplate` that is already PUBLISHED and has passed evaluation evidence.
- Package metadata is treated as untrusted marketplace input.
- Permission metadata cannot declare execution grants, automatic activation, approval bypass or provider credentials.
- Optional SkillPackage references are seller-owned and must already be PUBLISHED; W16 remains authoritative for their lifecycle.
- Public installation is cross-tenant only.
- Installation creates buyer-owned `AgentDefinition` + `AgentTemplate` records.
- The imported buyer template starts in DRAFT and requires the existing governed evaluation/promotion/activation path.
- No provider is invoked by installation.
- Provider execution status is explicitly `NOT_VERIFIED`.
- Installation and revocation are durable, tenant-scoped ledger events with audit records.
- Reinstallation after revocation reactivates the same ledger row.

## Security / governance boundaries

1. Marketplace publication is not execution authority.
2. Installation is not activation.
3. A seller cannot install its own public package through the buyer path.
4. Imported records are buyer-owned and tenant-scoped.
5. The marketplace package stores evidence references and requested permissions, not a grant to execute.
6. Existing AgentTemplate governance remains authoritative for evaluation, access review, approvals and activation.
7. Third-party provider execution remains fail-closed / unverified until a real provider contract and evidence exist.

## Financial boundary

This slice does **not** claim marketplace revenue, payout, tax settlement or external customer payment. W16 financial allocation remains the authoritative financial architecture for Skill Marketplace transactions. W20 financial truth should reuse or extend that governed accounting boundary rather than create a parallel informal ledger.

## Evidence

Dedicated workflow:

`.github/workflows/workforce-w20-e2e.yml`

Real-stack evidence covers:

- package publication from an evaluated seller template;
- cross-tenant installation;
- self-install rejection;
- execution-authority fail-closed semantics;
- explicit `NOT_VERIFIED` provider boundary;
- revocation;
- reinstallation/reactivation of the same installation ledger row.

Verification: W20 E2E Run `37308738607` / Job `111757?` — PASS on verification head `fe6377abcc7f110aa83a8cff3b8a0ea7e5c10c99`.

Production Certification is **NOT RUN** for W20.
