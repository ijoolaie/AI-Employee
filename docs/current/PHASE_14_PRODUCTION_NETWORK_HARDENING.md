# Phase 14 — Production Network Hardening

**Status:** Engineering contract complete / external deployment evidence pending

## Purpose

The production compose topology must keep application dependencies private and must not expose PostgreSQL, Redis, API, worker, Beat, or frontend directly through host-published ports. External ingress, TLS termination, firewall/security-group policy, DNS, WAF/load-balancer controls, and egress policy remain operator-managed deployment concerns.

## Repository-verifiable controls

- `docker-compose.production.yml` publishes no host ports.
- All production services are attached to the private `backend` bridge network.
- API and frontend health checks use loopback addresses inside their containers.
- PostgreSQL and Redis are reachable through the private compose network rather than host exposure.
- Production rate limiting is enabled and configured fail-closed.
- A deterministic CI validator prevents accidental reintroduction of host-published ports or loss of private-network attachment.

## External boundary

This gate proves configuration intent only. It does **not** prove the real deployment's firewall, security-group/NACL, ingress controller, TLS configuration, WAF, DNS, egress restrictions, service-to-service policy, or network segmentation.

External acceptance requires an operator-controlled staging/production environment with the exact release identity, documented ingress/egress rules, TLS certificate configuration, restricted management access, and evidence that internal services are not internet-reachable.

`production_certification_claimed=false`.
