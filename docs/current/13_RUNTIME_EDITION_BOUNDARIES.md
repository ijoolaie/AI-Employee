# Runtime Vendor / Reseller / Customer Boundaries

## Status

Implemented on the `productization/runtime-edition-boundaries` branch as the runtime follow-up to issue #19.

The model is a strict hierarchy:

```text
Vendor
  └── Reseller
        └── Customer
```

A downstream edition never receives implicit access to the control plane of its parent.

## Runtime rules

### Vendor

- A vendor tenant is the only tenant allowed to use the platform-admin control plane.
- Provider configuration and global administration are vendor-only.
- A vendor may provision direct reseller tenants.
- A vendor cannot directly operate a customer's tenant through the reseller/customer API surface.

### Reseller

- A reseller is a direct child of one vendor.
- Reseller administrators can provision and manage direct customer tenants only.
- Resellers can delegate feature entitlements and quotas to their own customers.
- Resellers cannot access vendor tenants, provider secrets, or vendor control-plane endpoints.
- Resellers can escalate support to their parent vendor.

### Customer

- A customer is a direct child of one reseller.
- Customer users remain scoped to their own tenant.
- Customers cannot access reseller or vendor tenants.
- Customers can open a support escalation to their parent reseller.
- Customer permissions do not include reseller provisioning, entitlement delegation, or vendor operations.

## Identity and delivery metadata

Each tenant stores:

- `tenant_kind`: `vendor`, `reseller`, or `customer`;
- `parent_tenant_id` for downstream editions;
- `vendor_release_tag` for the immutable vendor product baseline;
- `delivery_revision` for reseller/customer delivery revisions.

Existing platform-admin tenants are promoted to the vendor root by the migration so the current control plane is not stranded.

## Entitlement delegation

Entitlements are stored per tenant and record the tenant that delegated them. Delegation is only legal from:

- vendor → direct reseller;
- reseller → direct customer.

A child cannot self-assign an entitlement or receive one from a non-parent tenant.

## Support escalation

Support escalation is intentionally upward-only:

- customer → parent reseller;
- reseller → parent vendor.

A vendor cannot escalate upward because it is the root of the hierarchy.

## Verification

The automated boundary tests prove:

- vendor → direct reseller is allowed;
- vendor → customer is denied;
- reseller → direct customer is allowed;
- reseller → vendor is denied;
- customer → reseller/customer sibling is denied;
- parent and expected child edition are both required for provisioning/delegation.

The Alembic migration must be applied before starting the new control-plane endpoints. No credentials or customer data are included in source or delivery manifests.
