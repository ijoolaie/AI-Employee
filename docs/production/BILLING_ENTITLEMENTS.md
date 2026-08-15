# Billing & Entitlements

The plan layer must govern:
- employees
- runs/month
- storage
- AI tokens
- channels
- knowledge documents

Every billable operation should:
1. resolve tenant plan
2. verify entitlement
3. record usage
4. reject gracefully with a stable error code when exceeded

Frontend must show current usage, limit, and upgrade path.
