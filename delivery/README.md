# Delivery Packages

This directory defines the three commercial delivery layers for AI Employee.

## Current vendor release

The current immutable vendor release for the delivery topology is **v1.1.0** at commit `ab477b84a3f9f2441d2029a732a21d534fd217b9`.

## Packages

- `manifests/vendor/v1.1.0.yaml` — canonical vendor release reference.
- `manifests/reseller/v1.1.0-reseller.1.yaml` — reseller delivery configuration referencing the immutable vendor release.
- `manifests/customer/v1.1.0-customer.1.yaml` — end-customer deployment configuration referencing the reseller delivery.

The previous v1.0.1 manifests remain historical delivery records; they are not the current vendor package.

These are example manifests only. Replace placeholder IDs, branding, entitlement sets, deployment targets, and external contract references before a real delivery.

## Delivery rules

1. Never place credentials, tokens, customer data, or private keys in a manifest.
2. Keep the vendor tag and commit SHA immutable.
3. Treat reseller/customer configuration as a delivery revision, not a new product fork.
4. Every production delivery must be traceable back to an immutable vendor release.
5. Preserve the previous manifest when upgrading so rollback can identify the exact prior delivery.

## CI packaging

`.github/workflows/delivery-packages.yml` validates the v1.1.0 example manifests and creates a checksum-protected archive as a GitHub Actions artifact.

A real customer delivery should be generated from approved contract/configuration inputs rather than copying these examples unchanged.
