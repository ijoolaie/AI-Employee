# External Environment Evidence Record

> Do not put passwords, tokens, private keys, API keys, or secret values in this file.

## Identity

- environment_id:
- edition: `vendor` | `self-hosted` | `reseller` | `customer`
- release_version: `v1.4.1`
- source_commit_sha: `f7f5062feb125c7ca50263f74a0e40bc4abfa591`
- artifact_name:
- artifact_sha256:
- deployment_timestamp_utc:
- hostname_or_service_identifier:
- operator:

## Deployment

- deployment_method:
- deployed_image_or_package_identity:
- deployed_source_sha_verified: `PASS` | `FAIL`
- verification_reference:
- migration_head:
- migration_verification_reference:

## Health and operations

- API health: `PASS` | `FAIL`
- frontend health: `PASS` | `FAIL`
- dependency health: `PASS` | `FAIL`
- backup check: `PASS` | `FAIL`
- monitoring check: `PASS` | `FAIL`
- alert test: `PASS` | `FAIL`

## Security

- TLS: `PASS` | `FAIL`
- debug disabled: `PASS` | `FAIL`
- CORS/trusted-host policy: `PASS` | `FAIL`
- secrets externalized: `PASS` | `FAIL`
- secret rotation/recovery tested: `PASS` | `FAIL`
- DAST result/reference:
- independent security review/reference:

## Recovery

- backup timestamp:
- restore drill timestamp:
- measured RPO:
- measured RTO:
- failure/recovery rehearsal result:
- rollback rehearsal result:
- recovery artifact identity:

## Authority / isolation acceptance

- actor matrix reference:
- positive-path authorization evidence:
- negative-path authorization evidence:
- tenant isolation evidence:
- privileged audit evidence:

## Acceptance

- environment owner:
- acceptance timestamp:
- acceptance result: `ACCEPTED` | `REJECTED` | `CONDITIONAL`
- open exceptions:
- corrective actions:
- handoff status:

## Evidence references

List durable evidence references (artifact names, log/report identifiers, timestamps, screenshots, test reports, etc.) without embedding secrets.
