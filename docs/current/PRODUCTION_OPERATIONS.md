# Production Operations Contract

## Failure notification

Production certification, hardening, DR, observability, and rollback workflows are monitored by `.github/workflows/production-notify.yml`.

For automated failure notification, configure the GitHub Actions repository secret:

`PRODUCTION_ALERT_WEBHOOK_URL`

The value must be an HTTPS webhook accepted by the team's alerting system (for example Slack-compatible incoming webhook or an internal alert gateway). The secret is never stored in the repository.

The notification includes workflow name, repository, and failed run URL. The notification workflow fails closed when the webhook secret is missing or the webhook request fails.

## Rollback

Rollback remains gated by the production health/readiness contract and the known-good revision. A deployment system may select the previous immutable image/revision when the readiness gate fails.

The repository intentionally does not claim a live production rollback until a real deployment platform executes one successfully.
