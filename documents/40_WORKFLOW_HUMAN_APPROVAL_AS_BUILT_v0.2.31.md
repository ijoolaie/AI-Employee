# Workflow Human Approval — As Built v0.2.31

Durable human approval/wait-resume for workflow steps. The worker persists a waiting state and exits; approval decision resumes from the persisted workflow position. Expiration is enforced by a Celery periodic task.
