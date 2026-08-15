# Backup & Disaster Recovery Contract

## Required production policy
- PostgreSQL: automated encrypted backups
- Object storage: versioning/lifecycle policy
- Redis: define persistence/rebuild strategy
- Secrets: encrypted backup of configuration references, never plaintext secrets
- Retention: documented per environment
- Restore test: scheduled and recorded
- RPO/RTO: explicitly approved by owner

## Default target proposal
RPO: 15 minutes
RTO: 60 minutes

These are targets, not claims of current infrastructure performance.
