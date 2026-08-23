# Phase 5 — Release Channel and Supported-Version Policy

Date: 2026-08-23

## Purpose

Define the supported-version boundary for Vendor, Reseller and Customer delivery channels without coupling commercial policy to GitHub Actions availability.

## Channels

| Channel | Minimum supported | Supported releases |
|---|---|---|
| Vendor | v1.1.0 | v1.1.0, v1.1.1, v1.1.2 |
| Reseller | v1.1.1 | v1.1.1, v1.1.2 |
| Customer | v1.1.1 | v1.1.1, v1.1.2 |

## Rules

1. A target version must be explicitly supported by the target channel.
2. A target below the channel minimum is rejected.
3. Upgrade checks reject downgrades; rollback uses the documented rollback workflow instead.
4. The policy is version-aware but does not claim production deployment evidence.
5. Production rollout remains blocked until the target environment has the required deployment, monitoring, recovery and security evidence.

## Evidence boundary

The policy implementation is database-free and covered by contract tests. Full repository CI and production-environment verification remain pending until GitHub Actions capacity and the real deployment target are available.
