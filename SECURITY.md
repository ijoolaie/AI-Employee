# Security Policy

## Reporting a vulnerability

Do not open a public issue for a suspected security vulnerability.

Use GitHub's private security reporting mechanism for this repository when available. If private security reporting is not enabled yet, contact the repository owner through a private channel before disclosing the issue publicly.

Please include:

- affected component and version/commit;
- reproduction steps or a minimal proof of concept;
- security impact and realistic attack path;
- any mitigation already tested.

Do not include secrets, customer data, access tokens, private keys or other sensitive material in a public issue or pull request.

## Disclosure policy

Security fixes should be developed and validated privately when practical. Public disclosure should occur only after an appropriate fix or mitigation is available.

## Scope boundary

This repository contains local-development and test fixtures. Values explicitly documented as test-only credentials must never be reused in production. Production secrets, tenant data and customer configuration are expected to remain outside source control.
