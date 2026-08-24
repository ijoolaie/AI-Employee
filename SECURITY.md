# Security Policy

## Supported Versions

Security fixes are applied to the active supported release line. Older release lines may be unsupported unless explicitly identified in the current release documentation.

| Release line | Support |
| --- | --- |
| Current supported release | :white_check_mark: |
| Older unsupported releases | :x: |

## Reporting a Vulnerability

Do not open a public GitHub issue for a suspected security vulnerability.

Use GitHub's private vulnerability reporting/security advisory channel for this repository when available. If that channel is unavailable, contact the repository maintainer privately through the GitHub account associated with this repository.

When reporting a vulnerability, include:

- a clear description of the issue;
- affected component, version, commit, or workflow;
- reliable reproduction steps or a minimal proof of concept;
- security impact and any known prerequisites;
- any suggested mitigation, if available.

Do not include real customer data, production credentials, access tokens, private keys, or other secrets in a report.

## Response Expectations

Reports are triaged privately. We will acknowledge receipt when practical, validate the report, determine affected versions, and coordinate remediation or mitigation before public disclosure when appropriate.

## Disclosure

Security fixes should be developed and validated privately when practical.

Please allow reasonable time for investigation and remediation before publicly disclosing a vulnerability. Coordinated disclosure may include a security advisory, release note, or patched release once a fix is available.

## Scope

This policy covers the AI-Employee source repository, its application code, release automation, dependency configuration, and repository-maintained deployment tooling.

Third-party services and customer-operated infrastructure are outside the repository maintainer's direct operational control.

This repository contains local-development and test fixtures. Values explicitly documented as test-only credentials must never be reused in production.

Production secrets, tenant data and customer configuration are expected to remain outside source control.

## Security Reporting Boundary

Do not include secrets, customer data, access tokens, private keys or other sensitive material in a public issue or pull request.

Security fixes should be developed and validated privately when practical. Public disclosure should occur only after an appropriate fix or mitigation is available.
