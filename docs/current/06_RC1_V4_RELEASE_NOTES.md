# RC.1 v4 release notes

## Frontend dependency cleanup

- Next.js upgraded from 15.1.x to 15.5.21.
- `eslint-config-next` aligned to 15.5.21.
- Vitest upgraded from 2.1.8 to 4.1.10 to remove the vulnerable Vite/esbuild dependency chain reported by `npm audit`.
- Node.js requirement raised to >=22.13.0.
- Bootstrap now checks the Node.js version before installing frontend dependencies.

## Important

This is a dependency/security cleanup. It is not a claim that the application is production-ready. Run `npm audit`, unit tests, and `npm run build` after installation.
