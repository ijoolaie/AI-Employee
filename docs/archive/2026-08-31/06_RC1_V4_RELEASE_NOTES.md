# Historical Snapshot — RC.1 v4 release notes

> Archived from `docs/current/06_RC1_V4_RELEASE_NOTES.md` on 2026-08-31.
> This is a historical dependency/security cleanup note and is not current project status.

## Frontend dependency cleanup

- Next.js upgraded from 15.1.x to 15.5.21.
- `eslint-config-next` aligned to 15.5.21.
- Vitest upgraded from 2.1.8 to 4.1.10 to remove the vulnerable Vite/esbuild dependency chain reported by `npm audit`.
- Node.js requirement raised to >=22.13.0.
- Bootstrap now checks the Node.js version before installing frontend dependencies.

## Important

This was a dependency/security cleanup. It was not a claim that the application was production-ready.
