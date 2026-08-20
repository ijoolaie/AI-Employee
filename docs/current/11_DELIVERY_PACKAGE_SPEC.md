# Delivery Package Specification

## Purpose

Every reseller or end-customer handoff must be reproducible from an immutable vendor release and a small, explicit set of delivery metadata.

A delivery package is an operational contract, not a second source tree.

## Required package contents

```text
delivery/
├── MANIFEST.yaml
├── RELEASE_NOTES.md
├── INSTALL.md
├── UPGRADE.md
├── ROLLBACK.md
├── OPERATIONS.md
├── CONFIGURATION.md
└── EVIDENCE/
    ├── certification-summary.md
    ├── deployment-readiness.md
    └── verification-results.md
```

Binary/container artifacts may be attached separately by the release system.

## MANIFEST.yaml

The manifest is the authoritative link between commercial identity and technical identity.

Minimum fields:

```yaml
schema_version: 1
package_id: customer-example-001
edition: customer # vendor | reseller | customer

vendor:
  product: AI-Employee
  release_tag: v1.0.1
  commit_sha: 2d23a01098f432145ecaea14b2500fe520ad0bf7

reseller:
  id: reseller-example
  delivery_revision: 1

customer:
  id: customer-example
  deployment_revision: 1

deployment:
  environment: production
  region: replace-me
  image_registry: replace-me

configuration:
  schema_version: 1
  revision: customer-example-config-1

entitlements:
  plan: replace-me
  features: []

artifacts:
  backend_image: replace-me
  frontend_image: replace-me
  worker_image: replace-me

verification:
  certification_status: pass
  deployment_status: pass
```

The example above is a template only. Real credentials, tokens, passwords, private registry credentials, or customer data must never be committed into the manifest.

## Edition rules

### Vendor package

Contains the canonical product release and complete product-level evidence.

### Reseller package

Contains:

- referenced vendor release;
- reseller identity;
- reseller entitlements;
- reseller branding/configuration;
- deployment instructions;
- reseller-level verification evidence.

It must not contain vendor-only credentials or unrelated customer data.

### Customer package

Contains:

- referenced vendor release;
- reseller delivery identity, if the sale is through a reseller;
- customer identity;
- customer configuration revision;
- customer entitlements;
- deployment instructions;
- customer deployment verification evidence.

It must not contain credentials belonging to the vendor or another customer.

## Artifact immutability

Once a package is delivered, its manifest and release artifacts are immutable. Corrections produce a new package revision.

Do not silently replace an image or configuration under an existing delivery ID.

## Verification before handoff

The delivery owner must verify:

1. The vendor tag exists and resolves to the manifest SHA.
2. Every referenced artifact is available and has a digest.
3. No secret values are present in the package.
4. Configuration schema matches the referenced product release.
5. Migration and rollback instructions match the release.
6. Required certification evidence is attached.
7. The target deployment has an explicit environment identity.

## Rollback

Rollback must identify both:

- the previous immutable vendor release;
- the previous configuration/delivery revision.

A rollback is incomplete if only application images are restored while customer configuration remains at a newer incompatible revision.
