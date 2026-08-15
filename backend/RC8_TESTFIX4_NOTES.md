# RC8 TESTFIX4

- Fixed LM Studio provider factory to pass runtime settings explicitly.
- Added Tesseract (English/Persian) and Poppler runtime dependencies to the backend image.
- Updated tool registry contract for the currently registered commerce tools.
- Added an Alembic merge migration for the two RC8 billing/commerce heads.
- Updated the migration contract test to require exactly one head.
- Docker build context now includes the frontend; frontend is available at `/app/frontend` and `/frontend` for staging contract checks.
- No manual source edits are required; this archive is the complete patched handoff.

Local host pytest was not treated as authoritative because the host environment lacks the project's container dependencies (e.g. asyncpg). Run the suite inside the rebuilt Docker image.


## TESTFIX5
Docker build context hardened by excluding frontend node_modules and removing duplicate frontend copy.
