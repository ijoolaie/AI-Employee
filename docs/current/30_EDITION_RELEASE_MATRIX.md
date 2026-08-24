# Edition Release Matrix — Phase 6

## Purpose

Phase 6 separates the commercial delivery surface into three independently named release profiles while preserving one authoritative codebase and one immutable vendor source release.

The three profiles are:

1. **Vendor Edition** — primary seller control plane and product authority.
2. **Reseller Edition** — delegated commercial administration and customer provisioning.
3. **Customer Edition** — isolated end-customer deployment surface.

This is **delivery separation, not source-code forking**. Runtime authorization remains the security boundary.

## Release model

One immutable source release produces three profile artifacts:

```text
vendor    -> ai-employee-<vendor-release>-vendor.<profile-revision>.tar.gz
reseller  -> ai-employee-<vendor-release>-reseller.<profile-revision>.tar.gz
customer  -> ai-employee-<vendor-release>-customer.<profile-revision>.tar.gz
```

Every artifact references the same vendor release tag and source commit. Reseller and customer profiles add delivery revisions; they do not create alternate source histories.

## Matrix

| Property | Vendor | Reseller | Customer |
|---|---|---|---|
| Source authority | Vendor release | Vendor release | Vendor release |
| Control-plane scope | Global/vendor | Own reseller + direct customers | Own customer tenant |
| License authority | Issue/revoke downstream licenses | Issue/revoke direct customer licenses | Consume assigned license |
| Entitlement authority | Product-level | Delegated within vendor ceiling | Consume assigned entitlements |
| Provisioning | Resellers | Customers | No downstream provisioning |
| Support escalation | Final authority | Escalates to vendor | Escalates to reseller/vendor |
| Global/provider administration | Yes | No | No |
| Release channel | vendor | reseller | customer |
| Configuration owner | Vendor | Reseller | Customer/operator |
| Secrets | External secret store | External secret store | Customer secret store |
| Artifact identity | Vendor release | Delivery revision | Deployment revision |
| Rollback reference | Previous vendor release | Previous vendor + reseller revision | Previous vendor + customer revision |

## Security rule

A packaging distinction never replaces runtime authorization. The API/service layer must continue to enforce tenant, edition, role, license and entitlement boundaries. A reseller/customer archive must not become trusted merely because it has an edition label.

## Compatibility rule

All three profiles MUST remain compatible with the same source release and migration head. A profile-specific change that alters runtime behavior requires a new vendor source release, not a hidden profile fork.

## Completion criteria

Phase 6A–6C local implementation and verification are complete:

- [x] all three profile contracts are documented;
- [x] profile manifests validate locally;
- [x] one build command produces all three artifacts from one immutable source commit;
- [x] generated profiles contain no secrets;
- [x] each profile records its upstream vendor release identity;
- [x] reseller/customer profiles record delivery/deployment revision independently;
- [x] rollback metadata preserves both source release and profile revision;
- [x] profile packaging does not weaken runtime authorization;
- [x] release evidence records exactly which profile artifacts were produced.

Local execution evidence: `docs/current/35_PHASE6_LOCAL_BUILD_EVIDENCE_2026-08-24.md`.

GitHub Actions execution and real production deployment remain separate external gates.
