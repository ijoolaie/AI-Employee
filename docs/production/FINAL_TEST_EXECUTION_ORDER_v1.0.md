# Final Test Execution Order v1.0

1. Install backend dependencies from the locked/declared dependency set.
2. Run backend unit/integration tests.
3. Run `npm ci` in frontend.
4. Run frontend lint/typecheck/build/unit/contract tests.
5. Start staging services.
6. Run API E2E.
7. Run browser E2E.
8. Run Docker E2E where configured.
9. Certify Stripe.
10. Certify Shopify.
11. Certify WhatsApp inbound/outbound.
12. Certify human handoff.
13. Certify GDPR export/delete.
14. Verify backup/restore.
15. Run security checks.
16. Produce `FINAL_RELEASE_CERTIFICATION.md`.
17. If all P0/P1 gates pass, tag the release candidate; otherwise record blocking defects.

No feature work should be mixed into this phase except fixes for verified release-blocking defects.
