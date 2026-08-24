# Commercial Support and Update Policy

**Status date:** 2026-08-24
**Scope:** commercial handoff contract; production-specific contacts and targets remain environment-specific.

## Support model

### Vendor

The Vendor owns:

- immutable release authority;
- release publication and supported-version policy;
- vendor-wide security/update policy;
- global product/package and entitlement authority;
- escalation for reseller control-plane issues.

### Reseller

The Reseller owns:

- customer provisioning within its direct tenant boundary;
- customer entitlement delegation within the vendor-authorized ceiling;
- first-line customer operational support where contractually assigned;
- escalation to the Vendor for issues outside the reseller boundary.

### Customer

The Customer owns or operates, according to the contract:

- customer configuration and business data;
- user and role administration inside the customer boundary;
- first-line business acceptance and workflow verification;
- incident reporting with release, time and environment context.

## Support escalation

Every production handoff must record:

1. Vendor support identity.
2. Reseller support identity, if applicable.
3. Customer support identity.
4. Severity definitions and response targets.
5. Security-incident escalation path.
6. Data-loss/recovery escalation path.
7. Provider/integration escalation ownership.

Support escalation must respect the Vendor → Reseller → Customer hierarchy. A downstream edition must not gain implicit access to an upstream control plane.

## Update policy

1. Only immutable, published release identities may be deployed.
2. Supported-version policy is authoritative for Vendor, Reseller and Customer channels.
3. Upgrade admission checks the target version before changing the tenant release reference.
4. Downgrades are not performed through the upgrade path; use the documented rollback/recovery workflow.
5. Security updates take priority over feature updates when a supported release contains a material security fix.
6. Production updates require a pre-upgrade backup, a known-good rollback target, release identity capture and post-upgrade acceptance checks.
7. Any customer-specific configuration change must remain external to the immutable vendor release artifact.

## Release channels

The current policy is defined in `docs/current/26_RELEASE_CHANNEL_POLICY.md` and enforced by `backend/app/services/release_channel_service.py`.

## Change control

Post-handoff source modifications are not permitted as an informal customer customization path. Changes must be introduced through a new immutable vendor release or an explicitly versioned downstream delivery revision, with evidence and rollback implications recorded.

## Incident handling

For a production incident:

1. Record the incident time, environment and current release identity.
2. Preserve logs, monitoring evidence and migration state.
3. Determine whether forward remediation or rollback/recovery is safer.
4. Preserve the latest known-good backup before destructive recovery actions.
5. Execute the approved recovery workflow.
6. Verify health, tenant isolation and critical customer flows.
7. Record final state and follow-up actions.

## Evidence boundary

This document defines the commercial operating contract. It does not claim that a real production support contact, external monitoring provider or live customer deployment has already been configured. Those facts must be evidenced per environment.
