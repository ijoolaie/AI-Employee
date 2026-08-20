# Edition Delivery Checklist

Use this checklist before handing an AI Employee deployment to a reseller or end customer.

## Vendor baseline

- [ ] Confirm the vendor release tag is immutable.
- [ ] Confirm the vendor commit SHA matches the manifest.
- [ ] Confirm required certification evidence belongs to that release.
- [ ] Confirm migrations and supported rollback target are known.

## Reseller handoff

- [ ] Assign a unique reseller delivery revision.
- [ ] Record reseller contract and entitlement references without secrets.
- [ ] Apply reseller branding/configuration only through approved delivery inputs.
- [ ] Confirm reseller credentials are isolated from vendor credentials.
- [ ] Confirm no customer data is present in the reseller package.
- [ ] Preserve the previous reseller manifest for rollback.

## Customer handoff

- [ ] Assign a unique customer deployment revision.
- [ ] Record customer identity and contract/entitlement references without secrets.
- [ ] Apply customer branding/configuration only through approved delivery inputs.
- [ ] Confirm customer credentials are isolated from reseller/vendor credentials.
- [ ] Confirm tenant isolation and RBAC are enabled and tested.
- [ ] Confirm backup, restore, upgrade, and rollback procedures.
- [ ] Preserve the previous customer manifest for rollback.

## Package verification

- [ ] Manifest contains no credentials, tokens, passwords, private keys, or tenant data.
- [ ] Images/artifacts use immutable digests where applicable.
- [ ] Package checksum is recorded.
- [ ] Installation and migration instructions match the referenced release.
- [ ] Acceptance evidence is attached.
- [ ] Delivery identity resolves back to the exact vendor release.
