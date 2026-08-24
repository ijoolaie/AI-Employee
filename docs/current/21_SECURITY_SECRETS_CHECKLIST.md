# Security / Secrets Checklist

- [ ] No real secrets are present in the release archive.
- [ ] `.env` files are excluded from source control and release artifacts.
- [ ] `SECRET_KEY` is generated uniquely per environment.
- [ ] Database and Redis passwords are unique and strong.
- [ ] Production uses `DEBUG=false`.
- [ ] CORS origins are explicit; no wildcard is used for authenticated production traffic.
- [ ] TLS is enabled at the customer edge.
- [ ] Secrets are stored in the approved secret manager or protected host secret store.
- [ ] Stripe/Shopify credentials are supplied only when the integration is enabled.
- [ ] SMTP credentials are protected and recipient-domain policy is configured when email is enabled.
- [ ] OTEL endpoint credentials, if any, are protected.
- [ ] Production logs do not expose credentials or tokens.
- [ ] Backup data is encrypted/protected and access-controlled.
- [ ] Release checksum is verified before installation.
- [ ] Customer operator access is least-privilege.
- [ ] Emergency access and recovery contacts are documented.
