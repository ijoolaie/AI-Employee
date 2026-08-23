# Vendor → Reseller → Customer Handoff

## Vendor package

Provide:

- Versioned runtime archive
- `SHA256SUMS`
- `RELEASE-MANIFEST.json`
- Configuration template
- Installation, upgrade, backup/restore and rollback runbooks
- Security/secrets checklist
- Compatibility matrix
- Customer acceptance checklist

## Reseller handoff

Reseller receives the immutable release artifact and deployment instructions. Reseller may configure customer-specific values but must not modify runtime artifacts without creating a new release identity.

Record:

- vendor release
- reseller/operator identity
- customer identifier
- deployment target
- checksum
- configuration ownership
- support escalation path

## Customer handoff

Customer receives the deployed service plus operational documentation, support contacts, backup policy, recovery expectations and acceptance record.

## Change control

Any runtime modification after handoff must be traceable to a new source commit and release package. Never replace files inside an accepted package silently.
