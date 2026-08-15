# RC8 TESTFIX5 — Docker Build Context Hardening

## Issue

The TESTFIX4 image export failed in Docker Desktop while unpacking a layer under `frontend/node_modules`, with `input/output error` / `connection reset by peer`.

## Fix

- Added a root `.dockerignore` that excludes `frontend/node_modules`, `.next`, coverage and local/runtime artifacts.
- Removed the duplicate frontend COPY from `backend/Dockerfile`.
- Kept the frontend source available at `/app/frontend` and exposed `/frontend` as a symlink for compatibility with existing certification checks.
- Preserved tests, migrations and application source in the build context.

## Certification rule

This is an infrastructure/build fix only. No application test result is marked PASS until the rebuilt Docker image is successfully created and the full test suite runs inside the container.
