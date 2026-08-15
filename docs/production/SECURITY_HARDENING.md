# Security Hardening Checklist

## Identity
- [ ] Refresh-token rotation and reuse detection
- [ ] Brute-force/rate-limit protection
- [ ] Session revocation
- [ ] Strong password/reset policy

## Authorization
- [ ] Tenant isolation tests
- [ ] IDOR tests for every resource family
- [ ] Permission-aware UI
- [ ] Sensitive operation approvals

## API / Web
- [ ] CORS allow-list
- [ ] CSRF strategy for cookie auth
- [ ] Request size limits
- [ ] File MIME/content validation
- [ ] SSRF protections for fetch/import features
- [ ] Webhook signature verification

## AI
- [ ] Prompt-injection defenses
- [ ] Tool allow-list and argument validation
- [ ] Per-tool authorization
- [ ] Human approval for high-risk operations
- [ ] Secret redaction in traces/logs

## Secrets
- [ ] Encryption at rest
- [ ] Rotation
- [ ] Never expose secrets to frontend logs
