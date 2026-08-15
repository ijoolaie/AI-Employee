# Frontend dependency/security baseline

## Current baseline

The frontend uses Next.js 15.5.21, the latest patched 15.x maintenance release selected for this RC baseline, together with Vitest 4.1.10.

The previous baseline (`next 15.1.x`, `vitest 2.x`) produced `npm audit` findings through vulnerable transitive versions of `postcss`, `sharp`, and `esbuild`.

Do **not** run `npm audit fix --force` blindly. It can perform major-version changes and alter the application dependency graph.

## Node.js

Use Node.js **22.13.0 or newer**. The bootstrap script enforces this requirement.

## Verification

After extracting this release:

```powershell
cd frontend
npm install
npm audit
npm run test:unit
npm run build
```

The expected result is that the previously reported Next.js/PostCSS/sharp/esbuild advisories are no longer present. If `npm audit` reports a new issue, inspect the dependency tree before changing versions:

```powershell
npm audit
npm ls next postcss sharp esbuild vitest
```

## Security policy

Do not use `npm audit fix --force` as the first response. Update the direct dependency responsible for the vulnerable chain, then run the tests and production build.

This release intentionally keeps the Next.js major version at 15 to minimize application-level migration risk while moving to the patched 15.5.21 maintenance release.
