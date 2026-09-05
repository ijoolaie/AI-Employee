# Phase 14 — Provider Integration Validation

**Status:** Engineering preflight implemented; live provider validation remains **EXTERNAL-PENDING**.

## Scope

The repository contains provider adapters for Stripe and Shopify. The engineering gate now validates that the provider surfaces, production HTTPS safeguards, test coverage, and CI contract are present without requiring credentials or making outbound provider calls.

The preflight is intentionally deterministic and produces machine-readable evidence. It must not be interpreted as proof that a provider account, payment, OAuth installation, webhook delivery, or customer transaction has succeeded.

## Provider operations requiring live validation

### Stripe

- authenticated Checkout Session creation
- Billing Portal session creation
- webhook signature verification against a provider-issued event
- refund retry/idempotency behavior
- uncaptured PaymentIntent reversal behavior

### Shopify

- OAuth state validation and callback
- authorization-code token exchange
- authenticated GraphQL API request
- webhook registration and delivery

## External acceptance evidence

A real staging/production run must record sanitized evidence for each applicable provider operation, including a successful authenticated request, provider-issued resource identifier, verified webhook delivery, retry/idempotency behavior, and controlled failure-mode behavior. Secrets, access tokens, payment-card data, and customer PII must never be committed to the repository or uploaded as CI artifacts.

## Current boundary

The current environment does not provide operator-controlled Stripe/Shopify credentials or a customer/staging endpoint. Therefore the live provider gate remains blocked and **no production certification or customer acceptance claim is made**.

The CI contract is an engineering readiness gate only; it does not substitute for external provider certification.
